try:
    from app.models.answer_submission import AnswerSubmission
    from app.models.attempt_question import AttemptQuestion
    from app.models.exam import Exam
    from app.models.exam_attempt import ExamAttempt
    from app.models.exam_question import ExamQuestion
    from app.models.exam_session import ExamSession
    from app.models.question import Question
    from app.models.subject import Subject
    from app.models.user import User
except ModuleNotFoundError:
    from backend.app.models.answer_submission import AnswerSubmission
    from backend.app.models.attempt_question import AttemptQuestion
    from backend.app.models.exam import Exam
    from backend.app.models.exam_attempt import ExamAttempt
    from backend.app.models.exam_question import ExamQuestion
    from backend.app.models.exam_session import ExamSession
    from backend.app.models.question import Question
    from backend.app.models.subject import Subject
    from backend.app.models.user import User

__all__ = [
    "User",
    "Subject",
    "Question",
    "Exam",
    "ExamQuestion",
    "ExamSession",
    "ExamAttempt",
    "AnswerSubmission",
    "AttemptQuestion",
]