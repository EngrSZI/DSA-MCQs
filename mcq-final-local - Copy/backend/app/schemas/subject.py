from pydantic import BaseModel, ConfigDict, Field


class SubjectCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    code: str = Field(
        min_length=2,
        max_length=30,
    )

    description: str | None = None


class SubjectUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    code: str | None = Field(
        default=None,
        min_length=2,
        max_length=30,
    )

    description: str | None = None

    is_active: bool | None = None


class SubjectResponse(BaseModel):
    id: int
    name: str
    code: str
    description: str | None
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True,
    )