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
    """You are an expert assessment author and subject-matter expert. Write
{num_questions} high-quality exam questions of these types: {types}, on the
topic below. Use your own authoritative knowledge of the subject — you are NOT
limited to any supplied text.

Topic: {topic}
Learning objectives: {objectives}

Optional reference material (may be empty — if so, rely on your own expert
knowledge of the topic; if present, you may use it but are not restricted to it):
\"\"\"
{material_text}
\"\"\"

Strict rules:
- Write real, substantive questions that genuinely test understanding of the
  topic. NEVER output generic, templated, or placeholder text like
  "concept 1", "Correct option", or "Common misconception".
- Each question_text must be concrete and self-contained, naming the actual
  concept being tested (e.g. "What does the `len()` function return for a list?").
- For "mcq": provide exactly 4 realistic options of similar length/style; exactly
  one is correct and `correct_answer` must equal that option's text verbatim.
  The 3 distractors must be plausible, common mistakes — not obvious filler.
- For "short": `correct_answer` is the concise expected answer (word/short phrase);
  options must be null.
- Cover a spread of subtopics and difficulty; no near-duplicate questions.
- `marks`: 1 for recall, 2 for applied/scenario.

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
        topic=topic,
        objectives="; ".join(objectives) or "general comprehension",
        material_text=material_text or "(none provided)",
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
