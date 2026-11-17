from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.dependencies import (
        require_admin,
        require_teacher_or_admin,
    )
    from app.models.question import Question
    from app.models.subject import Subject
    from app.models.user import User
    from app.schemas.question import (
        QuestionCreate,
        QuestionResponse,
        QuestionUpdate,
    )
except ModuleNotFoundError:
    from backend.app.database import get_db
    from backend.app.dependencies import (
        require_admin,
        require_teacher_or_admin,
    )
    from backend.app.models.question import Question
    from backend.app.models.subject import Subject
    from backend.app.models.user import User
    from backend.app.schemas.question import (
        QuestionCreate,
        QuestionResponse,
        QuestionUpdate,
    )

router = APIRouter(
    prefix="/questions",
    tags=["Questions"],
)


@router.post(
    "",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_question(
    question_data: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    subject = db.get(Subject, question_data.subject_id)

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    if not subject.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add a question to an inactive subject",
        )

    question = Question(**question_data.model_dump())

    db.add(question)
    db.commit()
    db.refresh(question)

    return question


@router.get(
    "",
    response_model=list[QuestionResponse],
)
def list_questions(
    subject_id: int | None = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    query = select(Question).order_by(Question.id)

    if subject_id is not None:
        query = query.where(Question.subject_id == subject_id)

    if not include_inactive:
        query = query.where(Question.is_active.is_(True))

    return db.scalars(query).all()


@router.get(
    "/{question_id}",
    response_model=QuestionResponse,
)
def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    question = db.get(Question, question_id)

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    return question


@router.put(
    "/{question_id}",
    response_model=QuestionResponse,
)
def update_question(
    question_id: int,
    question_data: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    question = db.get(Question, question_id)

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    update_data = question_data.model_dump(exclude_unset=True)

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
                detail="Cannot assign a question to an inactive subject",
            )

    for field, value in update_data.items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)

    return question


@router.delete(
    "/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    question = db.get(Question, question_id)

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    db.delete(question)
    db.commit()

    return None