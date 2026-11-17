from typing import Literal

from pydantic import BaseModel


class AnswerSubmission(BaseModel):
    question_id: int
    selected_option: Literal["A", "B", "C", "D"]


class AttemptSubmission(BaseModel):
    answers: list[AnswerSubmission]
