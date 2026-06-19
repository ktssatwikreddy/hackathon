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
    AssessmentResult,
    Enrollment,
    EnrollmentStatus,
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
    summary: str
    learning_gaps: list[str]
    skill_areas: list[str]
    recommendations: list[str]


def build_graph(db: Session, groq: GroqService):
    def gather_metrics(state: PerfState) -> PerfState:
        user = db.get(User, state["user_id"])
        results = list(
            db.scalars(
                select(AssessmentResult).where(
                    AssessmentResult.user_id == state["user_id"]
                )
            )
        )
        # Percentage score per attempt.
        raw_scores = [
            round(float(r.score) / float(r.max_score) * 100, 1)
            for r in results
            if r.max_score
        ]
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
            "completed_trainings": completed_count,
        }

    def compute_aggregates(state: PerfState) -> PerfState:
        scores = state.get("raw_scores", [])
        avg = round(sum(scores) / len(scores), 1) if scores else 0.0
        return {**state, "avg_score": avg}

    def llm_summarize(state: PerfState) -> PerfState:
        from app.schemas.ai import PerformanceInsight  # for schema shape

        schema = {
            "properties": {
                "summary": {"type": "string"},
                "learning_gaps": {"type": "array"},
                "skill_areas": {"type": "array"},
            }
        }
        data = groq.complete_json(
            f"Summarise the training performance of {state['name']}.",
            schema,
            name=state["name"],
            attendance_pct=state["attendance_pct"],
            avg_score=state["avg_score"],
            completed_trainings=state["completed_trainings"],
        )
        return {
            **state,
            "summary": data.get("summary", ""),
            "learning_gaps": data.get("learning_gaps", []),
            "skill_areas": data.get("skill_areas", []),
        }

    def extract_recommendations(state: PerfState) -> PerfState:
        schema = {"properties": {"recommendations": {"type": "array"}}}
        data = groq.complete_json(
            f"Recommend next steps for {state['name']}.",
            schema,
            attendance_pct=state["attendance_pct"],
            avg_score=state["avg_score"],
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
