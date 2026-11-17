from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.dependencies import (
        get_current_user,
        require_admin,
        require_teacher_or_admin,
    )
    from app.models.exam import Exam
    from app.models.subject import Subject
    from app.models.user import User
    from app.schemas.exam import ExamCreate, ExamResponse, ExamUpdate
except ModuleNotFoundError:
    from backend.app.database import get_db
    from backend.app.dependencies import (
        get_current_user,
        require_admin,
        require_teacher_or_admin,
    )
    from backend.app.models.exam import Exam
    from backend.app.models.subject import Subject
    from backend.app.models.user import User
    from backend.app.schemas.exam import ExamCreate, ExamResponse, ExamUpdate

router = APIRouter(
    prefix="/exams",
    tags=["Exams"],
)


@router.post(
    "",
    response_model=ExamResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_exam(
    exam_data: ExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    subject = db.get(Subject, exam_data.subject_id)

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    if not subject.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create an exam for an inactive subject",
        )

    if exam_data.passing_marks > exam_data.total_marks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passing marks cannot exceed total marks",
        )

    exam = Exam(**exam_data.model_dump())

    db.add(exam)
    db.commit()
    db.refresh(exam)

    return exam


@router.get(
    "",
    response_model=list[ExamResponse],
)
def list_exams(
    subject_id: int | None = None,
    include_unpublished: bool = False,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Exam).order_by(Exam.id)

    if subject_id is not None:
        query = query.where(Exam.subject_id == subject_id)

    if not include_inactive:
        query = query.where(Exam.is_active.is_(True))

    if current_user.role == "student" or not include_unpublished:
        query = query.where(Exam.is_published.is_(True))

    return db.scalars(query).all()


@router.get(
    "/{exam_id}",
    response_model=ExamResponse,
)
def get_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exam = db.get(Exam, exam_id)

    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )

    if current_user.role == "student":
        if not exam.is_active or not exam.is_published:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam not found",
            )

    return exam


@router.put(
    "/{exam_id}",
    response_model=ExamResponse,
)
def update_exam(
    exam_id: int,
    exam_data: ExamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    exam = db.get(Exam, exam_id)

    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )

    update_data = exam_data.model_dump(exclude_unset=True)

    if "subject_id" in update_data:
        subject = db.get(Subject, update_data["subject_id"])

        if subject is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found",
            )

        if not subject.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign an exam to an inactive subject",
            )

    new_total_marks = update_data.get("total_marks", exam.total_marks)
    new_passing_marks = update_data.get("passing_marks", exam.passing_marks)

    if new_passing_marks > new_total_marks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passing marks cannot exceed total marks",
        )

    for field, value in update_data.items():
        setattr(exam, field, value)

    db.commit()
    db.refresh(exam)

    return exam


@router.patch(
    "/{exam_id}/publish",
    response_model=ExamResponse,
)
def publish_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    exam = db.get(Exam, exam_id)

    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )

    if not exam.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot publish an inactive exam",
        )

    exam.is_published = True

    db.commit()
    db.refresh(exam)

    return exam


@router.patch(
    "/{exam_id}/unpublish",
    response_model=ExamResponse,
)
def unpublish_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    exam = db.get(Exam, exam_id)

    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )

    exam.is_published = False

    db.commit()
    db.refresh(exam)

    return exam


@router.delete(
    "/{exam_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    exam = db.get(Exam, exam_id)

    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )

    db.delete(exam)
    db.commit()

    return None