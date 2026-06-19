"""LangGraph pipeline that analyses a learner's performance.

Nodes: gather_metrics -> compute_aggregates -> llm_summarize -> extract_recommendations
"""
from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.groq_client import GroqService
from app.models import (
    Assessment,
    AssessmentResult,
    Enrollment,
    EnrollmentStatus,
    Training,
    User,
)
from app.services.attendance_service import attendance_percentage


class PerfState(TypedDict, total=False):
    user_id: int
    name: str
    attendance_pct: float
    raw_scores: list[float]
    avg_score: float
    completed_trainings: int
    results_detail: list[dict]
    metrics_text: str
    summary: str
    learning_gaps: list[str]
    skill_areas: list[str]
    recommendations: list[str]


def build_graph(db: Session, groq: GroqService):
    def gather_metrics(state: PerfState) -> PerfState:
        user = db.get(User, state["user_id"])
        rows = db.execute(
            select(AssessmentResult, Assessment.title, Training.title)
            .join(Assessment, AssessmentResult.assessment_id == Assessment.id)
            .join(Training, Assessment.training_id == Training.id)
            .where(AssessmentResult.user_id == state["user_id"])
            .order_by(AssessmentResult.attempt_date.desc())
        ).all()

        raw_scores: list[float] = []
        results_detail: list[dict] = []
        for r, a_title, t_title in rows:
            pct = round(float(r.score) / float(r.max_score) * 100, 1) if r.max_score else 0.0
            raw_scores.append(pct)
            results_detail.append(
                {
                    "assessment": a_title,
                    "training": t_title,
                    "score": f"{r.score}/{r.max_score}",
                    "pct": pct,
                    "result": r.result.value,
                }
            )

        completed_count = len(
            list(
                db.scalars(
                    select(Enrollment.id).where(
                        Enrollment.user_id == state["user_id"],
                        Enrollment.status == EnrollmentStatus.completed,
                    )
                )
            )
        )
        return {
            **state,
            "name": user.name if user else "The learner",
            "attendance_pct": attendance_percentage(db, state["user_id"]),
            "raw_scores": raw_scores,
            "results_detail": results_detail,
            "completed_trainings": completed_count,
        }

    def compute_aggregates(state: PerfState) -> PerfState:
        scores = state.get("raw_scores", [])
        avg = round(sum(scores) / len(scores), 1) if scores else 0.0

        # A plain-text block of THIS learner's real data, embedded into the
        # prompt so the model grounds its output in actual results.
        details = state.get("results_detail", [])
        if details:
            lines = "\n".join(
                f"- {d['training']} / {d['assessment']}: {d['score']} ({d['pct']}%, {d['result']})"
                for d in details
            )
        else:
            lines = "- No assessment attempts yet."
        metrics_text = (
            f"Learner: {state['name']}\n"
            f"Attendance: {state['attendance_pct']}%\n"
            f"Completed trainings: {state['completed_trainings']}\n"
            f"Average assessment score: {avg}%\n"
            f"Assessment attempts:\n{lines}"
        )
        return {**state, "avg_score": avg, "metrics_text": metrics_text}

    def llm_summarize(state: PerfState) -> PerfState:
        schema = {
            "properties": {
                "summary": {"type": "string"},
                "learning_gaps": {"type": "array"},
                "skill_areas": {"type": "array"},
            }
        }
        prompt = (
            "You are a learning & development analyst. Using ONLY this learner's "
            "actual data below, write a concise performance summary plus their "
            "specific learning gaps and demonstrated skill areas. Reference the "
            "real numbers and assessments — do not invent data.\n\n"
            f"{state['metrics_text']}\n\n"
            "Return JSON: summary (string, 2-4 sentences), learning_gaps (array of "
            "short strings), skill_areas (array of short strings)."
        )
        data = groq.complete_json(
            prompt, schema,
            name=state["name"], attendance_pct=state["attendance_pct"],
            avg_score=state["avg_score"], completed_trainings=state["completed_trainings"],
        )
        return {
            **state,
            "summary": data.get("summary", ""),
            "learning_gaps": data.get("learning_gaps", []),
            "skill_areas": data.get("skill_areas", []),
        }

    def extract_recommendations(state: PerfState) -> PerfState:
        schema = {"properties": {"recommendations": {"type": "array"}}}
        prompt = (
            "Based ONLY on this learner's actual data below, give 3-5 concrete, "
            "personalised next-step recommendations.\n\n"
            f"{state['metrics_text']}\n\n"
            "Return JSON: recommendations (array of short strings)."
        )
        data = groq.complete_json(
            prompt, schema,
            attendance_pct=state["attendance_pct"], avg_score=state["avg_score"],
        )
        return {**state, "recommendations": data.get("recommendations", [])}

    graph = StateGraph(PerfState)
    graph.add_node("gather_metrics", gather_metrics)
    graph.add_node("compute_aggregates", compute_aggregates)
    graph.add_node("llm_summarize", llm_summarize)
    graph.add_node("extract_recommendations", extract_recommendations)

    graph.set_entry_point("gather_metrics")
    graph.add_edge("gather_metrics", "compute_aggregates")
    graph.add_edge("compute_aggregates", "llm_summarize")
    graph.add_edge("llm_summarize", "extract_recommendations")
    graph.add_edge("extract_recommendations", END)
    return graph.compile()


def analyze_performance(db: Session, groq: GroqService, user_id: int) -> dict:
    app = build_graph(db, groq)
    final = app.invoke({"user_id": user_id})
    return {
        "user_id": user_id,
        "summary": final["summary"],
        "attendance_pct": final["attendance_pct"],
        "avg_score": final["avg_score"],
        "completed_trainings": final["completed_trainings"],
        "learning_gaps": final["learning_gaps"],
        "skill_areas": final["skill_areas"],
        "recommendations": final["recommendations"],
    }
