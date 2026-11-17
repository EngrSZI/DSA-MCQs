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
    from app.models.exam import Exam
    from app.models.exam_question import ExamQuestion
    from app.models.question import Question
    from app.schemas.exam_question import (
        ExamQuestionCreate,
        ExamQuestionResponse,
        ExamQuestionUpdate,
    )
except ModuleNotFoundError:
    from backend.app.database import get_db
    from backend.app.dependencies import (
        get_current_user,
        require_admin,
        require_teacher_or_admin,
    )
    from backend.app.models.exam import Exam
    from backend.app.models.exam_question import ExamQuestion
    from backend.app.models.question import Question
    from backend.app.schemas.exam_question import (
        ExamQuestionCreate,
        ExamQuestionResponse,
        ExamQuestionUpdate,
    )

router = APIRouter(
    prefix="/exam-questions",
    tags=["Exam Questions"],
)

def recalculate_exam_marks(db: Session, exam_id: int):
    exam = db.get(Exam, exam_id)

    if exam is None:
        return

    assignments = db.scalars(
        select(ExamQuestion).where(
            ExamQuestion.exam_id == exam_id
        )
    ).all()

    exam.total_marks = sum(
        assignment.marks for assignment in assignments
    )

    exam.passing_marks = exam.total_marks // 2

@router.post(
    "",
    response_model=ExamQuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_question_to_exam(
    data: ExamQuestionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_teacher_or_admin),
):
    exam = db.get(Exam, data.exam_id)

    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )

    question = db.get(Question, data.question_id)

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    if not exam.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add questions to an inactive exam",
        )

    if not question.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add an inactive question",
        )

    if exam.subject_id != question.subject_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must belong to the same subject as the exam",
        )

    existing_assignment = db.scalar(
        select(ExamQuestion).where(
            ExamQuestion.exam_id == data.exam_id,
            ExamQuestion.question_id == data.question_id,
        )
    )

    if existing_assignment is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Question is already assigned to this exam",
        )

    assignment = ExamQuestion(
        exam_id=data.exam_id,
        question_id=data.question_id,
        question_order=data.question_order,
        marks=data.marks,
    )

    db.add(assignment)

    try:
        db.commit()

        recalculate_exam_marks(db, exam.id)

        db.commit()
        db.refresh(assignment)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Question could not be assigned to this exam",
        )

    return assignment


@router.get(
    "/exam/{exam_id}",
    response_model=list[ExamQuestionResponse],
)
def list_exam_questions(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    exam = db.get(Exam, exam_id)

    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )

    assignments = db.scalars(
        select(ExamQuestion)
        .where(ExamQuestion.exam_id == exam_id)
        .order_by(ExamQuestion.question_order, ExamQuestion.id)
    ).all()

    return assignments


@router.get(
    "/{assignment_id}",
    response_model=ExamQuestionResponse,
)
def get_exam_question_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    assignment = db.get(ExamQuestion, assignment_id)

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam question assignment not found",
        )

    return assignment


@router.put(
    "/{assignment_id}",
    response_model=ExamQuestionResponse,
)
def update_exam_question_assignment(
    assignment_id: int,
    data: ExamQuestionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_teacher_or_admin),
):
    assignment = db.get(ExamQuestion, assignment_id)

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam question assignment not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(assignment, field, value)

    db.commit()

    recalculate_exam_marks(db, assignment.exam_id)

    db.commit()
    db.refresh(assignment)

    return assignment


@router.delete(
    "/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_question_from_exam(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    assignment = db.get(ExamQuestion, assignment_id)

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam question assignment not found",
        )

    exam_id = assignment.exam_id

    db.delete(assignment)
    db.commit()

    recalculate_exam_marks(db, exam_id)

    db.commit()

    return None