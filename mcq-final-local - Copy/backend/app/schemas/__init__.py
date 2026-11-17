try:
    from app.schemas.auth import (
        TokenResponse,
        UserLogin,
        UserRegister,
        UserResponse,
    )
    from app.schemas.attempt import AttemptSubmission
    from app.schemas.exam import ExamCreate, ExamResponse, ExamUpdate
    from app.schemas.exam_question import (
        ExamQuestionCreate,
        ExamQuestionResponse,
        ExamQuestionUpdate,
    )
    from app.schemas.question import (
        QuestionCreate,
        QuestionResponse,
        QuestionUpdate,
    )
    from app.schemas.subject import (
        SubjectCreate,
        SubjectResponse,
        SubjectUpdate,
    )
except ModuleNotFoundError:
    from backend.app.schemas.auth import (
        TokenResponse,
        UserLogin,
        UserRegister,
        UserResponse,
    )
    from backend.app.schemas.attempt import AttemptSubmission
    from backend.app.schemas.exam import ExamCreate, ExamResponse, ExamUpdate
    from backend.app.schemas.exam_question import (
        ExamQuestionCreate,
        ExamQuestionResponse,
        ExamQuestionUpdate,
    )
    from backend.app.schemas.question import (
        QuestionCreate,
        QuestionResponse,
        QuestionUpdate,
    )
    from backend.app.schemas.subject import (
        SubjectCreate,
        SubjectResponse,
        SubjectUpdate,
    )

__all__ = [
    "TokenResponse",
    "UserLogin",
    "UserRegister",
    "UserResponse",
    "AttemptSubmission",
    "ExamCreate",
    "ExamResponse",
    "ExamUpdate",
    "ExamQuestionCreate",
    "ExamQuestionResponse",
    "ExamQuestionUpdate",
    "QuestionCreate",
    "QuestionResponse",
    "QuestionUpdate",
    "SubjectCreate",
    "SubjectResponse",
    "SubjectUpdate",
]