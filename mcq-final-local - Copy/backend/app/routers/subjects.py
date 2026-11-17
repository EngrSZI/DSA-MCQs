from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.dependencies import (
        get_current_user,
        require_admin,
        require_teacher_or_admin,
    )
    from app.models.subject import Subject
    from app.models.user import User
    from app.schemas.subject import (
        SubjectCreate,
        SubjectResponse,
        SubjectUpdate,
    )
except ModuleNotFoundError:
    from backend.app.database import get_db
    from backend.app.dependencies import (
        get_current_user,
        require_admin,
        require_teacher_or_admin,
    )
    from backend.app.models.subject import Subject
    from backend.app.models.user import User
    from backend.app.schemas.subject import (
        SubjectCreate,
        SubjectResponse,
        SubjectUpdate,
    )

router = APIRouter(
    prefix="/subjects",
    tags=["Subjects"],
)


@router.post(
    "",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subject(
    payload: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    existing_subject = db.scalar(
        select(Subject).where(Subject.code == payload.code)
    )

    if existing_subject:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A subject with this code already exists.",
        )

    subject = Subject(
        name=payload.name,
        code=payload.code,
        description=payload.description,
    )

    db.add(subject)
    db.commit()
    db.refresh(subject)

    return subject


@router.get(
    "",
    response_model=list[SubjectResponse],
)
def list_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(Subject)
        .where(Subject.is_active.is_(True))
        .order_by(Subject.name)
    )

    return list(db.scalars(statement).all())


@router.get(
    "/{subject_id}",
    response_model=SubjectResponse,
)
def get_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subject = db.get(Subject, subject_id)

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found.",
        )

    return subject


@router.put(
    "/{subject_id}",
    response_model=SubjectResponse,
)
def update_subject(
    subject_id: int,
    payload: SubjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    subject = db.get(Subject, subject_id)

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "code" in update_data:
        existing_subject = db.scalar(
            select(Subject).where(
                Subject.code == update_data["code"],
                Subject.id != subject_id,
            )
        )

        if existing_subject:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A subject with this code already exists.",
            )

    for field, value in update_data.items():
        setattr(subject, field, value)

    db.commit()
    db.refresh(subject)

    return subject


@router.delete(
    "/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    subject = db.get(Subject, subject_id)

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found.",
        )

    db.delete(subject)
    db.commit()

    return None