"""LangChain pipeline that generates assessment questions from material text.

Validates the model output against a Pydantic schema; on failure it retries
once with a "fix the JSON" prompt, then raises 502.
"""
from __future__ import annotations

import logging

from fastapi import HTTPException
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from app.ai.groq_client import GroqService
from app.schemas.ai import GeneratedQuestionList

logger = logging.getLogger("tapms.ai")

_PROMPT = ChatPromptTemplate.from_template(
    """You are an expert assessment author. Generate {num_questions} questions
of these types: {types}, based strictly on the material below.

Learning objectives: {objectives}

Material:
\"\"\"
{material_text}
\"\"\"

Each question must include: question_text, question_type (one of the requested
types), options (a list for mcq, otherwise null), correct_answer, and marks.
"""
)


def generate_questions(
    groq: GroqService,
    *,
    material_text: str,
    num_questions: int,
    types: list[str],
    objectives: list[str],
    topic: str,
) -> GeneratedQuestionList:
    prompt = _PROMPT.format(
        num_questions=num_questions,
        types=", ".join(types),
        objectives="; ".join(objectives) or "general comprehension",
        material_text=material_text,
    )
    schema = GeneratedQuestionList.model_json_schema()

    def _attempt(extra: str = "") -> GeneratedQuestionList:
        raw = groq.complete_json(
            prompt + extra,
            schema,
            num_questions=num_questions,
            types=types,
            topic=topic,
        )
        return GeneratedQuestionList.model_validate(raw)

    try:
        return _attempt()
    except (ValidationError, ValueError, KeyError, TypeError) as first_error:
        logger.warning("AI question JSON invalid, retrying once: %s", first_error)
        try:
            return _attempt(
                "\n\nYour previous response was not valid JSON for the schema. "
                "Return ONLY a JSON object with a 'questions' array."
            )
        except (ValidationError, ValueError, KeyError, TypeError) as second_error:
            logger.error("AI question generation failed twice: %s", second_error)
            raise HTTPException(
                status_code=502,
                detail="AI failed to produce valid questions. Please try again.",
            ) from second_error
