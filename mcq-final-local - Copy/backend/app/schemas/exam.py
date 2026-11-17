from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExamCreate(BaseModel):
    subject_id: int
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None
    duration_minutes: int = Field(gt=0)
    total_marks: float = Field(default=0, ge=0)
    passing_marks: float = Field(default=0, ge=0)
    is_published: bool = False
    is_active: bool = True
    start_time: datetime | None = None
    end_time: datetime | None = None

    @field_validator("passing_marks")
    @classmethod
    def validate_passing_marks(cls, value: int, info):
        total_marks = info.data.get("total_marks", 0)

        if value > total_marks:
            raise ValueError("passing_marks cannot exceed total_marks")

        return value

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, value: datetime | None, info):
        start_time = info.data.get("start_time")

        if value is not None and start_time is not None and value <= start_time:
            raise ValueError("end_time must be later than start_time")

        return value


class ExamUpdate(BaseModel):
    subject_id: int | None = None
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    total_marks: float | None = Field(default=None, ge=0)
    passing_marks: float | None = Field(default=None, ge=0)
    is_published: bool | None = None
    is_active: bool | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class ExamResponse(BaseModel):
    id: int
    subject_id: int
    title: str
    description: str | None
    duration_minutes: int
    total_marks: float
    passing_marks: float
    is_published: bool
    is_active: bool
    start_time: datetime | None
    end_time: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)