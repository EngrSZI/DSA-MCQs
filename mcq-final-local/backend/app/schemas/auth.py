from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=150,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    student_id: str | None = None
    full_name: str
    email: EmailStr
    program: str | None = None
    role: str
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"