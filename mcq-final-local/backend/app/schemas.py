from pydantic import BaseModel
from typing import List


class AnswerSubmission(BaseModel):
    question_id: int
    selected_option: str


class AttemptSubmission(BaseModel):
    answers: List[AnswerSubmission]