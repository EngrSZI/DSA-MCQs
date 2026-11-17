from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from sqlalchemy import func
from sqlalchemy.orm import Session

try:
    from app.config import settings
    from app.database import get_db
    from app.dependencies import (
        get_current_user,
        require_admin,
        require_student,
        require_teacher_or_admin,
    )
    from app.models.user import User
    from app.models import Exam, ExamQuestion
    from app.routers import attempts, auth, exam_questions, exams, questions, subjects, results, admin_students
except ModuleNotFoundError:
    from backend.app.config import settings
    from backend.app.database import get_db
    from backend.app.dependencies import (
        get_current_user,
        require_admin,
        require_student,
        require_teacher_or_admin,
    )
    from backend.app.models.user import User
    from backend.app.models import Exam, ExamQuestion
    from backend.app.routers import attempts, auth, exam_questions, exams, questions, subjects, results, admin_students


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

logger = logging.getLogger(__name__)


@app.on_event("startup")
def seed_question_bank():
    try:
        from app.database import SessionLocal
        from app.models import Exam, ExamQuestion
        from seed_nsct_exam import seed_nsct_exam
    except ModuleNotFoundError:
        from backend.app.database import SessionLocal
        from backend.app.models import Exam, ExamQuestion
        from backend.seed_nsct_exam import seed_nsct_exam

    db = SessionLocal()
    try:
        available_exam = db.query(Exam.id).join(
            ExamQuestion,
            ExamQuestion.exam_id == Exam.id,
        ).filter(
            Exam.title == "NSCT Preparation - All Subjects",
            Exam.is_published.is_(True),
            Exam.is_active.is_(True),
        ).first()
        if available_exam is not None:
            logger.info("Published NSCT exam already exists: exam_id=%s", available_exam[0])
            return

        seed_nsct_exam(db)
    except Exception:
        logger.exception("Failed to seed NSCT workbook question bank during API startup")
        raise
    finally:
        db.close()


app.add_middleware(
    CORSMiddleware,
    # The student UI is served through Vite, and Cloudflare Tunnel can give
    # that UI a temporary public HTTPS hostname. The browser calls the API
    # through Vite's same-origin proxy, so credentials are sent via the
    # Authorization header rather than cookies.
    allow_origins=["*", settings.frontend_url, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(subjects.router)
app.include_router(questions.router)
app.include_router(exams.router)
app.include_router(exam_questions.router)
app.include_router(attempts.router)
app.include_router(results.router)
app.include_router(admin_students.router)

@app.get("/")
def root():
    return {
        "message": "MCQ Examination System API",
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    exams = db.query(
        Exam.id,
        Exam.title,
        Exam.is_published,
        Exam.is_active,
        func.count(ExamQuestion.id).label("question_count"),
    ).outerjoin(
        ExamQuestion,
        ExamQuestion.exam_id == Exam.id,
    ).group_by(
        Exam.id,
    ).order_by(
        Exam.id,
    ).all()
    nsct_exam = next(
        (exam for exam in exams if exam.title == "NSCT Preparation - All Subjects"),
        None,
    )
    return {
        "status": "healthy",
        "nsct_exam": (
            {
                "id": nsct_exam.id,
                "title": nsct_exam.title,
                "is_published": nsct_exam.is_published,
                "is_active": nsct_exam.is_active,
                "question_count": nsct_exam.question_count,
            }
            if nsct_exam
            else None
        ),
    }


@app.get("/auth/me")
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "student_id": current_user.student_id,
        "email": current_user.email,
        "program": current_user.program,
        "role": current_user.role,
        "is_active": current_user.is_active,
    }


@app.get("/test/student-only")
def student_only(
    current_user: User = Depends(require_student),
):
    return {
        "message": "Student access granted.",
        "user": current_user.email,
    }


@app.get("/test/teacher-only")
def teacher_only(
    current_user: User = Depends(require_teacher_or_admin),
):
    return {
        "message": "Teacher or administrator access granted.",
        "user": current_user.email,
    }


@app.get("/test/admin-only")
def admin_only(
    current_user: User = Depends(require_admin),
):
    return {
        "message": "Administrator access granted.",
        "user": current_user.email,
    }