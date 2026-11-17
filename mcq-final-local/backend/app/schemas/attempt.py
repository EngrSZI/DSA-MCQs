from typing import Literal

from pydantic import BaseModel, Field


class AnswerSubmission(BaseModel):
    question_id: int
    selected_option: Literal["A", "B", "C", "D"]


class AttemptSubmission(BaseModel):
    answers: list[AnswerSubmission]
    tab_switch_penalty: float = Field(default=0.0, ge=0)
