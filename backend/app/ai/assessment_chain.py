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
    """You are an expert assessment author. Write {num_questions} high-quality
questions of these types: {types}, grounded strictly in the material below.

Learning objectives: {objectives}

Material:
\"\"\"
{material_text}
\"\"\"

Strict rules:
- Test real understanding of specific facts/concepts FROM THE MATERIAL — never
  generic, templated, or placeholder text.
- The question_text must be a concrete, self-contained question a learner can
  answer from the material (mention the actual concept, not "concept 1").
- For "mcq": provide exactly 4 plausible options that are all realistic and
  similar in length/style; exactly one is correct. Distractors must be common,
  believable mistakes — NOT obviously wrong filler. `correct_answer` must be the
  exact text of the correct option.
- For "short": `correct_answer` is the concise expected answer (a word/phrase);
  options must be null.
- Vary difficulty and the concepts covered; do not repeat near-duplicate questions.
- `marks` is a small positive integer (1 for recall, 2 for applied/scenario).

Each question must include: question_text, question_type (one of the requested
types), options (a list of 4 strings for mcq, otherwise null), correct_answer,
and marks.
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
            material=material_text,
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
