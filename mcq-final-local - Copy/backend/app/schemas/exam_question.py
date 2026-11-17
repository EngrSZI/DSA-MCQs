from pydantic import BaseModel, ConfigDict, Field


class ExamQuestionCreate(BaseModel):
    exam_id: int
    question_id: int
    question_order: int = Field(default=1, gt=0)
    marks: float = Field(default=1, gt=0)


class ExamQuestionUpdate(BaseModel):
    question_order: int | None = Field(default=None, gt=0)
    marks: float | None = Field(default=None, gt=0)


class ExamQuestionResponse(BaseModel):
    id: int
    exam_id: int
    question_id: int
    question_order: int
    marks: float

    model_config = ConfigDict(from_attributes=True)