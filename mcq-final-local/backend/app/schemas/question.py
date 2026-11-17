from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuestionCreate(BaseModel):
    subject_id: int
    question_text: str = Field(min_length=5)
    option_a: str = Field(min_length=1, max_length=500)
    option_b: str = Field(min_length=1, max_length=500)
    option_c: str = Field(min_length=1, max_length=500)
    option_d: str = Field(min_length=1, max_length=500)
    correct_option: str = Field(min_length=1, max_length=1)
    explanation: str | None = None
    difficulty: str = "medium"
    marks: float = Field(default=1, gt=0)
    is_active: bool = True

    @field_validator("correct_option")
    @classmethod
    def validate_correct_option(cls, value: str) -> str:
        value = value.upper()

        if value not in {"A", "B", "C", "D"}:
            raise ValueError("correct_option must be A, B, C, or D")

        return value

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, value: str) -> str:
        value = value.lower()

        if value not in {"easy", "medium", "hard"}:
            raise ValueError("difficulty must be easy, medium, or hard")

        return value


class QuestionUpdate(BaseModel):
    subject_id: int | None = None
    question_text: str | None = Field(default=None, min_length=5)
    option_a: str | None = Field(default=None, min_length=1, max_length=500)
    option_b: str | None = Field(default=None, min_length=1, max_length=500)
    option_c: str | None = Field(default=None, min_length=1, max_length=500)
    option_d: str | None = Field(default=None, min_length=1, max_length=500)
    correct_option: str | None = Field(default=None, min_length=1, max_length=1)
    explanation: str | None = None
    difficulty: str | None = None
    marks: float | None = Field(default=None, gt=0)
    is_active: bool | None = None

    @field_validator("correct_option")
    @classmethod
    def validate_correct_option(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.upper()

        if value not in {"A", "B", "C", "D"}:
            raise ValueError("correct_option must be A, B, C, or D")

        return value

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.lower()

        if value not in {"easy", "medium", "hard"}:
            raise ValueError("difficulty must be easy, medium, or hard")

        return value


class QuestionResponse(BaseModel):
    id: int
    subject_id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    explanation: str | None
    difficulty: str
    marks: float
    is_active: bool

    model_config = ConfigDict(from_attributes=True)