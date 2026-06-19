"""Groq LLM access behind a Protocol, with a deterministic mock fallback.

The factory `get_groq_service()` returns the mock when `MOCK_AI=true` (default)
so the whole app runs and demos with no API key. Switching to the real backend
requires only `MOCK_AI=false` + `GROQ_API_KEY` in the environment.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Protocol, runtime_checkable

from app.core.config import get_settings

logger = logging.getLogger("tapms.ai")


@runtime_checkable
class GroqService(Protocol):
    def complete(self, prompt: str, **kwargs: Any) -> str: ...

    def complete_json(self, prompt: str, schema: dict, **kwargs: Any) -> dict: ...


# --------------------------------------------------------------------------- #
# Real backend
# --------------------------------------------------------------------------- #
class RealGroqService:
    def __init__(self) -> None:
        from langchain_groq import ChatGroq  # imported lazily

        settings = get_settings()
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is required when MOCK_AI=false")
        self._llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0.2,
        )

    def complete(self, prompt: str, **kwargs: Any) -> str:
        return self._llm.invoke(prompt).content

    def complete_json(self, prompt: str, schema: dict, **kwargs: Any) -> dict:
        instruction = (
            f"{prompt}\n\nRespond with ONLY valid JSON conforming to this schema:\n"
            f"{json.dumps(schema)}\nDo not wrap it in markdown fences."
        )
        raw = self._llm.invoke(instruction).content
        return _parse_json(raw)


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        # strip ```json ... ``` fences
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip().rstrip("`").strip()
    return json.loads(text)


# --------------------------------------------------------------------------- #
# Mock backend — deterministic, realistic, shaped to the schema
# --------------------------------------------------------------------------- #
class MockGroqService:
    def complete(self, prompt: str, **kwargs: Any) -> str:
        return (
            "This is a deterministic mock completion. Set MOCK_AI=false and "
            "provide GROQ_API_KEY to use the real Groq model."
        )

    def complete_json(self, prompt: str, schema: dict, **kwargs: Any) -> dict:
        # Branch on the kind of request via the schema's top-level fields.
        props = (schema or {}).get("properties", {})
        if "questions" in props:
            return self._mock_questions(**kwargs)
        if "recommendations" in props and "summary" not in props:
            return self._mock_recommendations(**kwargs)
        return self._mock_summary(**kwargs)

    # -- assessment generation --
    def _mock_questions(
        self,
        *,
        num_questions: int = 5,
        types: list[str] | None = None,
        topic: str = "the training material",
        **_: Any,
    ) -> dict:
        types = [str(t) for t in (types or ["mcq", "short"])]
        questions = []
        for i in range(num_questions):
            qtype = types[i % len(types)]
            if qtype == "mcq":
                correct = f"Correct option for concept {i + 1}"
                questions.append(
                    {
                        "question_text": f"Q{i + 1}: Which statement about {topic} (concept {i + 1}) is correct?",
                        "question_type": "mcq",
                        "options": [
                            correct,
                            f"Common misconception {i + 1}",
                            f"Unrelated idea {i + 1}",
                            f"Partially true claim {i + 1}",
                        ],
                        "correct_answer": correct,
                        "marks": 1,
                    }
                )
            elif qtype == "short":
                questions.append(
                    {
                        "question_text": f"Q{i + 1}: In one phrase, define key term {i + 1} from {topic}.",
                        "question_type": "short",
                        "options": None,
                        "correct_answer": f"key term {i + 1}",
                        "marks": 1,
                    }
                )
            elif qtype == "scenario":
                questions.append(
                    {
                        "question_text": f"Q{i + 1}: Describe how you would apply {topic} in scenario {i + 1}.",
                        "question_type": "scenario",
                        "options": None,
                        "correct_answer": f"A reasonable application of {topic} for scenario {i + 1}.",
                        "marks": 2,
                    }
                )
            else:  # coding
                questions.append(
                    {
                        "question_text": f"Q{i + 1}: Write a function demonstrating {topic} (task {i + 1}).",
                        "question_type": "coding",
                        "options": None,
                        "correct_answer": "def solution():\n    ...  # reference implementation",
                        "marks": 2,
                    }
                )
        return {"questions": questions}

    # -- performance summary --
    def _mock_summary(
        self,
        *,
        name: str = "The learner",
        attendance_pct: float = 0.0,
        avg_score: float = 0.0,
        completed_trainings: int = 0,
        **_: Any,
    ) -> dict:
        attend_desc = (
            "strong and consistent" if attendance_pct >= 80
            else "inconsistent" if attendance_pct >= 50
            else "a concern"
        )
        score_desc = (
            "above expectations" if avg_score >= 75
            else "around the passing line" if avg_score >= 50
            else "below the passing threshold"
        )
        summary = (
            f"{name} has completed {completed_trainings} training(s). Attendance is "
            f"{attend_desc} at {attendance_pct}% and assessment performance is "
            f"{score_desc} (avg {avg_score}%). "
            "Engagement and outcomes are trending in line with these signals."
        )
        gaps = []
        if attendance_pct < 80:
            gaps.append("Session attendance below the 80% target")
        if avg_score < 70:
            gaps.append("Assessment scores indicate gaps in core concepts")
        if not gaps:
            gaps.append("No major gaps detected; focus on advanced topics")

        skills = ["Foundational concepts", "Practical application"]
        if avg_score >= 75:
            skills.append("Independent problem solving")
        return {"summary": summary, "learning_gaps": gaps, "skill_areas": skills}

    # -- recommendations --
    def _mock_recommendations(
        self,
        *,
        attendance_pct: float = 0.0,
        avg_score: float = 0.0,
        **_: Any,
    ) -> dict:
        recs = []
        if attendance_pct < 80:
            recs.append("Schedule make-up sessions to recover missed attendance")
        if avg_score < 70:
            recs.append("Review fundamentals and retake the practice assessment")
            recs.append("Pair with a mentor for the weakest topic areas")
        else:
            recs.append("Enroll in an advanced module to build on current strengths")
        recs.append("Set a measurable goal for the next assessment cycle")
        return {"recommendations": recs}


def get_groq_service() -> GroqService:
    settings = get_settings()
    if settings.mock_ai:
        logger.debug("Using MockGroqService (MOCK_AI=true)")
        return MockGroqService()
    return RealGroqService()
