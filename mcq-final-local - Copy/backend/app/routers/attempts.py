import random
from datetime import datetime, timedelta, timezone
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.dependencies import get_current_user
    from app.models import (
        AnswerSubmission,
        AttemptQuestion,
        Exam,
        ExamAttempt,
        ExamQuestion,
        ExamSession,
        Question,
        Subject,
        User,
    )
    from app.schemas import AttemptSubmission
except ModuleNotFoundError:
    from backend.app.database import get_db
    from backend.app.dependencies import get_current_user
    from backend.app.models import (
        AnswerSubmission,
        AttemptQuestion,
        Exam,
        ExamAttempt,
        ExamQuestion,
        ExamSession,
        Question,
        Subject,
        User,
    )
    from backend.app.schemas import AttemptSubmission


try:
    from app.services.result_exporter import export_results
except ModuleNotFoundError:
    from backend.app.services.result_exporter import export_results


router = APIRouter(
    prefix="/attempts",
    tags=["Attempts"],
)

QUESTIONS_PER_ATTEMPT = 25
ATTEMPT_DURATION_MINUTES = 13
CORRECT_MARKS = 1.00
WRONG_PENALTY = 0.20


def _effective_passing_marks(attempt: ExamAttempt) -> float:
    return (
        float(attempt.passing_marks)
        if attempt.passing_marks > 0
        else float(ceil(attempt.total_marks / 2))
    )


def _normalize_submitted_answers(submission_answers: list) -> dict[int, str]:
    normalized_answers: dict[int, str] = {}
    for answer in submission_answers:
        if answer.selected_option in (None, ""):
            continue

        question_id = answer.question_id
        if question_id in normalized_answers:
            raise ValueError("Each question may only be answered once")

        normalized_answers[question_id] = answer.selected_option

    return normalized_answers


def _submission_answers_for_attempt(
    submission_answers: list,
    attempt_questions: list[AttemptQuestion],
    expired: bool,
) -> dict[int, str]:
    if expired:
        return {}

    normalized_answers = _normalize_submitted_answers(submission_answers)
    attempt_question_ids = {
        assignment.question_id for assignment in attempt_questions
    }
    if set(normalized_answers) - attempt_question_ids:
        raise ValueError("One or more submitted questions do not belong to this exam")

    return normalized_answers


def _count_answered_questions_for_session(db: Session, session_id: int) -> int:
    return (
        db.query(func.count(func.distinct(AnswerSubmission.question_id)))
        .join(ExamAttempt, ExamAttempt.id == AnswerSubmission.attempt_id)
        .filter(
            ExamAttempt.session_id == session_id,
            ExamAttempt.status == "submitted",
            AnswerSubmission.selected_option.isnot(None),
            AnswerSubmission.selected_option != "",
        )
        .scalar()
        or 0
    )


def _select_fair_question_assignments(assignments: list[ExamQuestion], limit: int, usage_counts: dict[int, int] | None = None) -> list[ExamQuestion]:
    if not assignments or limit <= 0:
        return []

    usage_counts = usage_counts or {}
    ranked = [
        (usage_counts.get(assignment.question_id, 0), random.random(), assignment)
        for assignment in assignments
    ]
    ranked.sort(key=lambda item: (item[0], item[1]))
    return [assignment for _, _, assignment in ranked[:limit]]


def _attempt_duration_minutes(db: Session, attempt: ExamAttempt) -> int:
    question_count = db.query(AttemptQuestion).filter(
        AttemptQuestion.attempt_id == attempt.id
    ).count()
    return max(
        ATTEMPT_DURATION_MINUTES,
        ceil(question_count / QUESTIONS_PER_ATTEMPT) * ATTEMPT_DURATION_MINUTES,
    )


def _attempt_response(attempt: ExamAttempt, duration_minutes: int) -> dict:
    return {
        "id": attempt.id,
        "student_id": attempt.student_id,
        "exam_id": attempt.exam_id,
        "total_marks": attempt.total_marks,
        "passing_marks": _effective_passing_marks(attempt),
        "obtained_marks": attempt.obtained_marks,
        "status": attempt.status,
        "started_at": attempt.started_at,
        "submitted_at": attempt.submitted_at,
        "duration_minutes": duration_minutes,
        # started_at is stored as UTC-naive in PostgreSQL. Mark it as UTC
        # when serializing so browsers do not interpret it as local time.
        "expires_at": (
            (attempt.started_at.replace(tzinfo=timezone.utc)
             + timedelta(minutes=duration_minutes))
        ),
    }


def _session_progress(db: Session, session: ExamSession) -> dict:
    batch_count = db.query(ExamAttempt).filter(
        ExamAttempt.session_id == session.id
    ).count()
    completed_questions = _count_answered_questions_for_session(db, session.id)
    completed_batches = db.query(ExamAttempt).filter(
        ExamAttempt.session_id == session.id,
        ExamAttempt.status == "submitted",
    ).count()
    session.obtained_marks = sum(
        attempt.obtained_marks
        for attempt in db.query(ExamAttempt).filter(
            ExamAttempt.session_id == session.id,
            ExamAttempt.status == "submitted",
        ).all()
    )

    remaining_questions = max(0, session.total_questions - completed_questions)
    return {
        "session_id": session.id,
        "completed_batches": completed_batches,
        "total_batches": batch_count,
        "completed_questions": completed_questions,
        "total_questions": session.total_questions,
        "remaining_questions": remaining_questions,
        "completion_percentage": (
            (completed_questions / session.total_questions) * 100
            if session.total_questions else 0
        ),
        "session_total_marks": session.total_marks,
        "session_obtained_marks": session.obtained_marks,
        "session_status": session.status,
    }


def _create_attempt_questions(
    db: Session,
    attempt: ExamAttempt,
    assignments: list[ExamQuestion],
    exam: Exam,
) -> list[AttemptQuestion]:
    snapshots = [
        AttemptQuestion(
            attempt_id=attempt.id,
            question_id=assignment.question_id,
            question_order=position,
            marks=CORRECT_MARKS,
            correct_option=db.get(Question, assignment.question_id).correct_option,
        )
        for position, assignment in enumerate(assignments, start=1)
    ]
    db.add_all(snapshots)
    db.flush()

    attempt.total_marks = float(len(snapshots) * CORRECT_MARKS)
    if exam.total_marks > 0 and exam.passing_marks > 0:
        attempt.passing_marks = float(
            ceil(attempt.total_marks * exam.passing_marks / exam.total_marks)
        )
    else:
        attempt.passing_marks = float(ceil(attempt.total_marks / 2))
    return snapshots


def _batch_response(db: Session, session: ExamSession, attempt: ExamAttempt) -> dict:
    response = _attempt_response(attempt, _attempt_duration_minutes(db, attempt))
    response.update(_session_progress(db, session))
    response["batch_number"] = attempt.batch_number
    return response


def _final_result(db: Session, session: ExamSession) -> dict:
    submitted_attempts = db.query(ExamAttempt).filter(
        ExamAttempt.session_id == session.id,
        ExamAttempt.status == "submitted",
    ).all()
    session.obtained_marks = sum(
        attempt.obtained_marks for attempt in submitted_attempts
    )
    percentage = (
        session.obtained_marks / session.total_marks * 100
        if session.total_marks > 0
        else 0
    )
    passing_marks = sum(
        _effective_passing_marks(attempt) for attempt in submitted_attempts
    )
    return {
        "session_id": session.id,
        "attempt_id": session.id,
        "exam_id": session.exam_id,
        "student_id": session.student_id,
        "total_questions": session.total_questions,
        "total_marks": session.total_marks,
        "obtained_marks": session.obtained_marks,
        "score": session.obtained_marks,
        "percentage": percentage,
        "passing_marks": passing_marks,
        "passed": session.obtained_marks >= passing_marks,
        "status": session.status,
        "started_at": session.started_at,
        "completed_at": session.completed_at,
    }


# ---------------------------------------------------------
# Start an exam attempt
# ---------------------------------------------------------

@router.get("/options")
def get_attempt_options(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can select exam questions")

    exam = db.query(Exam).filter(
        Exam.id == exam_id,
        Exam.is_published.is_(True),
        Exam.is_active.is_(True),
    ).first()
    if exam is None:
        raise HTTPException(status_code=404, detail="No published exam is available")

    rows = db.query(
        Subject.id,
        Subject.name,
        Question.difficulty,
        func.count(Question.id),
    ).join(
        Question,
        Question.subject_id == Subject.id,
    ).join(
        ExamQuestion,
        ExamQuestion.question_id == Question.id,
    ).filter(
        ExamQuestion.exam_id == exam.id,
        Question.is_active.is_(True),
        Subject.is_active.is_(True),
    ).group_by(
        Subject.id,
        Subject.name,
        Question.difficulty,
    ).order_by(
        Subject.name,
        Question.difficulty,
    ).all()

    subjects: dict[int, dict] = {}
    for subject_id, subject_name, difficulty, count in rows:
        subject = subjects.setdefault(subject_id, {
            "id": subject_id,
            "name": subject_name,
            "question_count": 0,
            "difficulties": [],
        })
        subject["question_count"] += count
        subject["difficulties"].append({
            "name": difficulty,
            "question_count": count,
        })

    return {"exam_id": exam.id, "subjects": list(subjects.values())}


@router.post("/start")
def start_attempt(
    exam_id: int,
    subject_id: int | None = Query(default=None, gt=0),
    difficulty: str | None = Query(default=None, min_length=1),
    question_count: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can start an exam",
        )

    exam = db.query(Exam).filter(
        Exam.id == exam_id,
        Exam.is_published.is_(True),
        Exam.is_active.is_(True),
    ).first()

    if exam is None:
        raise HTTPException(status_code=404, detail="No published exam is available")

    now = datetime.utcnow()
    if exam.start_time is not None and now < exam.start_time:
        raise HTTPException(status_code=403, detail="This exam has not started")
    if exam.end_time is not None and now > exam.end_time:
        raise HTTPException(status_code=403, detail="This exam has ended")

    session = db.query(ExamSession).filter(
        ExamSession.student_id == current_user.id,
        ExamSession.exam_id == exam.id,
        ExamSession.status == "in_progress",
    ).first()

    existing_attempt = None
    if session is not None:
        existing_attempt = db.query(ExamAttempt).filter(
            ExamAttempt.session_id == session.id,
            ExamAttempt.status == "in_progress",
        ).first()
    if existing_attempt:
        duration_minutes = _attempt_duration_minutes(db, existing_attempt)
        if datetime.utcnow() <= existing_attempt.started_at + timedelta(minutes=duration_minutes):
            return _batch_response(db, session, existing_attempt)
        existing_attempt.status = "submitted"
        existing_attempt.submitted_at = datetime.utcnow()
        existing_attempt.obtained_marks = 0.0
        db.commit()

    if session is None:
        filtered_assignments_query = db.query(ExamQuestion).join(
            Question,
            Question.id == ExamQuestion.question_id,
        ).filter(
            ExamQuestion.exam_id == exam.id,
            Question.is_active.is_(True),
        )
        if subject_id is not None:
            filtered_assignments_query = filtered_assignments_query.filter(
                Question.subject_id == subject_id
            )
        if difficulty is not None:
            filtered_assignments_query = filtered_assignments_query.filter(
                func.lower(Question.difficulty) == difficulty.strip().lower()
            )

        filtered_assignments = filtered_assignments_query.all()
        if not filtered_assignments:
            raise HTTPException(
                status_code=400,
                detail="No active questions match the selected subject and difficulty",
            )
        if question_count is not None and question_count > len(filtered_assignments):
            raise HTTPException(
                status_code=400,
                detail=f"Only {len(filtered_assignments)} questions are available for this selection",
            )

        target_questions = question_count or len(filtered_assignments)
        session = ExamSession(
            student_id=current_user.id,
            exam_id=exam.id,
            total_questions=target_questions,
            total_marks=float(target_questions * CORRECT_MARKS),
        )
        db.add(session)
        db.flush()
    else:
        first_assigned_question = db.query(AttemptQuestion.question_id).join(
            ExamAttempt,
            ExamAttempt.id == AttemptQuestion.attempt_id,
        ).filter(
            ExamAttempt.session_id == session.id,
        ).first()
        if first_assigned_question is not None:
            scope_question = db.get(Question, first_assigned_question[0])
            if scope_question is not None:
                subject_id = scope_question.subject_id
                difficulty = scope_question.difficulty

    session.total_marks = float(session.total_questions * CORRECT_MARKS)
    assigned_question_ids = db.query(AttemptQuestion.question_id).join(
        ExamAttempt,
        ExamAttempt.id == AttemptQuestion.attempt_id,
    ).filter(ExamAttempt.session_id == session.id).all()
    assigned_question_ids = {question_id for (question_id,) in assigned_question_ids}

    remaining_assignments = db.query(ExamQuestion).join(
        Question,
        Question.id == ExamQuestion.question_id,
    ).filter(
        ExamQuestion.exam_id == exam.id,
        Question.is_active.is_(True),
    )
    if subject_id is not None:
        remaining_assignments = remaining_assignments.filter(
            Question.subject_id == subject_id
        )
    if difficulty is not None:
        remaining_assignments = remaining_assignments.filter(
            func.lower(Question.difficulty) == difficulty.strip().lower()
        )
    if assigned_question_ids:
        remaining_assignments = remaining_assignments.filter(
            ~ExamQuestion.question_id.in_(assigned_question_ids)
        )
    remaining_for_student = max(0, session.total_questions - len(assigned_question_ids))
    if remaining_for_student == 0:
        session.status = "completed"
        session.completed_at = session.completed_at or datetime.utcnow()
        db.commit()
        raise HTTPException(
            status_code=409,
            detail="You have completed the selected questions for this exam.",
        )

    batch_size = remaining_for_student
    candidate_assignments = remaining_assignments.all()
    candidate_ids = {assignment.question_id for assignment in candidate_assignments}

    usage_counts: dict[int, int] = {}
    if candidate_ids:
        rows = db.query(
            AttemptQuestion.question_id,
            func.count(AttemptQuestion.id).label("usage_count"),
        ).join(
            ExamAttempt,
            ExamAttempt.id == AttemptQuestion.attempt_id,
        ).filter(
            AttemptQuestion.question_id.in_(candidate_ids),
            ExamAttempt.exam_id == exam.id,
            ExamAttempt.status.in_(["submitted", "in_progress"]),
        ).group_by(AttemptQuestion.question_id).all()
        usage_counts = {question_id: int(count) for question_id, count in rows}

    assignments = _select_fair_question_assignments(candidate_assignments, batch_size, usage_counts)
    if len(assignments) < batch_size:
        session.status = "completed"
        session.completed_at = session.completed_at or datetime.utcnow()
        db.commit()
        raise HTTPException(
            status_code=409,
            detail="Not enough unused questions remain for this selection",
        )

    batch_number = (db.query(ExamAttempt).filter(
        ExamAttempt.session_id == session.id
    ).count() + 1)

    attempt = ExamAttempt(
        student_id=current_user.id,
        exam_id=exam.id,
        session_id=session.id,
        batch_number=batch_number,
        total_marks=float(len(assignments) * CORRECT_MARKS),
        passing_marks=exam.passing_marks,
        obtained_marks=0.0,
        status="in_progress",
    )

    db.add(attempt)
    db.flush()
    _create_attempt_questions(db, attempt, assignments, exam)
    db.commit()
    db.refresh(attempt)

    return _batch_response(db, session, attempt)


# ---------------------------------------------------------
# Get questions for an attempt
# ---------------------------------------------------------

@router.get("/{attempt_id}/questions")
def get_attempt_questions(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = db.query(ExamAttempt).filter(
        ExamAttempt.id == attempt_id,
        ExamAttempt.student_id == current_user.id,
    ).first()

    if not attempt:
        raise HTTPException(
            status_code=404,
            detail="Attempt not found",
        )

    attempt_questions = db.query(AttemptQuestion).filter(
        AttemptQuestion.attempt_id == attempt.id
    ).order_by(AttemptQuestion.question_order).all()
    saved_answers = {
        answer.question_id: answer.selected_option
        for answer in db.query(AnswerSubmission).filter(
            AnswerSubmission.attempt_id == attempt.id,
            AnswerSubmission.selected_option.isnot(None),
        ).all()
    }
    duration_minutes = _attempt_duration_minutes(db, attempt)

    questions = []

    for attempt_question in attempt_questions:
        question = db.query(Question).filter(
            Question.id == attempt_question.question_id
        ).first()

        if not question:
            continue

        questions.append({
            "id": question.id,
            "question_text": question.question_text,
            "option_a": question.option_a,
            "option_b": question.option_b,
            "option_c": question.option_c,
            "option_d": question.option_d,
            "marks": attempt_question.marks,
            "selected_option": saved_answers.get(question.id),
        })

    return {
        "attempt_id": attempt.id,
        "exam_id": attempt.exam_id,
        "total_marks": attempt.total_marks,
        "questions": questions,
        "duration_minutes": duration_minutes,
        # Explicit UTC timezone prevents the browser from treating the
        # database's UTC-naive timestamp as Pakistan local time.
        "expires_at": (
            (attempt.started_at.replace(tzinfo=timezone.utc)
             + timedelta(minutes=duration_minutes))
        ),
    }


@router.put("/{attempt_id}/answers")
def save_attempt_answers(
    attempt_id: int,
    submission: AttemptSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = db.query(ExamAttempt).filter(
        ExamAttempt.id == attempt_id,
        ExamAttempt.student_id == current_user.id,
    ).with_for_update().first()
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.status != "in_progress":
        raise HTTPException(status_code=400, detail="This attempt is no longer active")

    expires_at = attempt.started_at + timedelta(
        minutes=_attempt_duration_minutes(db, attempt)
    )
    if datetime.utcnow() > expires_at:
        raise HTTPException(status_code=409, detail="The attempt deadline has passed")

    attempt_questions = db.query(AttemptQuestion).filter(
        AttemptQuestion.attempt_id == attempt.id
    ).all()
    try:
        saved_answers = _submission_answers_for_attempt(
            submission.answers, attempt_questions, expired=False
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    questions_by_id = {
        assignment.question_id: assignment for assignment in attempt_questions
    }
    for question_id, selected_option in saved_answers.items():
        answer = db.query(AnswerSubmission).filter(
            AnswerSubmission.attempt_id == attempt.id,
            AnswerSubmission.question_id == question_id,
        ).first()
        if answer is None:
            answer = AnswerSubmission(
                attempt_id=attempt.id,
                question_id=question_id,
                correct_option=questions_by_id[question_id].correct_option,
            )
            db.add(answer)
        answer.selected_option = selected_option
        answer.answered_at = datetime.utcnow()

    db.commit()
    return {"saved": len(saved_answers)}


# ---------------------------------------------------------
# Submit an exam attempt
# ---------------------------------------------------------

@router.post("/{attempt_id}/submit")
def submit_attempt(
    attempt_id: int,
    submission: AttemptSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = db.query(ExamAttempt).filter(
        ExamAttempt.id == attempt_id,
        ExamAttempt.student_id == current_user.id,
    ).with_for_update().first()

    if not attempt:
        raise HTTPException(
            status_code=404,
            detail="Attempt not found",
        )

    if attempt.status == "submitted":
        raise HTTPException(
            status_code=400,
            detail="This attempt has already been submitted",
        )

    exam = db.get(Exam, attempt.exam_id)
    if exam is None:
        raise HTTPException(status_code=404, detail="Exam not found")

    now = datetime.utcnow()
    duration_minutes = _attempt_duration_minutes(db, attempt)
    expired = now > attempt.started_at + timedelta(minutes=duration_minutes)
    attempt_questions = db.query(AttemptQuestion).filter(
        AttemptQuestion.attempt_id == attempt.id
    ).all()

    correct_answers = 0
    attempted_questions = 0
    obtained_marks = 0.0

    try:
        submitted_answers = _submission_answers_for_attempt(
            submission.answers, attempt_questions, expired
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if expired:
        submitted_answers = {
            answer.question_id: answer.selected_option
            for answer in db.query(AnswerSubmission).filter(
                AnswerSubmission.attempt_id == attempt.id,
                AnswerSubmission.selected_option.isnot(None),
            ).all()
        }

    for attempt_question in attempt_questions:
        question = db.query(Question).filter(
            Question.id == attempt_question.question_id
        ).first()

        if not question:
            continue

        if question.id in submitted_answers:
            attempted_questions += 1

            selected_option = submitted_answers[question.id]

            if selected_option == attempt_question.correct_option:
                correct_answers += 1
                obtained_marks += CORRECT_MARKS
            else:
                obtained_marks -= WRONG_PENALTY

            answer = db.query(AnswerSubmission).filter(
                AnswerSubmission.attempt_id == attempt.id,
                AnswerSubmission.question_id == question.id,
            ).first()
            if answer is None:
                answer = AnswerSubmission(
                    attempt_id=attempt.id,
                    question_id=question.id,
                )
                db.add(answer)
            answer.selected_option = selected_option
            answer.correct_option = attempt_question.correct_option
            answer.marks_awarded = (
                CORRECT_MARKS
                if selected_option == attempt_question.correct_option
                else -WRONG_PENALTY
            )
            answer.is_correct = selected_option == attempt_question.correct_option
            answer.answered_at = datetime.utcnow()

    attempt.obtained_marks = obtained_marks
    attempt.passing_marks = _effective_passing_marks(attempt)
    attempt.submitted_at = datetime.utcnow()
    attempt.status = "submitted"

    session = db.get(ExamSession, attempt.session_id) if attempt.session_id else None
    final_result = None
    session_complete = False
    if session is not None:
        allocated_question_count = db.query(
            func.count(func.distinct(AttemptQuestion.question_id))
        ).join(
            ExamAttempt,
            ExamAttempt.id == AttemptQuestion.attempt_id,
        ).filter(
            ExamAttempt.session_id == session.id,
        ).scalar() or 0
        if allocated_question_count >= session.total_questions:
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            session_complete = True
            db.flush()
            final_result = _final_result(db, session)

    db.commit()
    db.refresh(attempt)
    export_results(db)

    return {
        "message": "Exam submitted automatically because time expired" if expired else "Exam submitted successfully",
        "expired": expired,
        "attempt_id": attempt.id,
        "exam_id": attempt.exam_id,
        "student_id": attempt.student_id,
        "total_questions": len(attempt_questions),
        "attempted_questions": attempted_questions,
        "correct_answers": correct_answers,
        "score": attempt.obtained_marks,
        "total_marks": attempt.total_marks,
        "percentage": (
            attempt.obtained_marks / attempt.total_marks * 100
            if attempt.total_marks > 0
            else 0
        ),
        "passed": attempt.obtained_marks >= attempt.passing_marks,
        "status": attempt.status,
        "submitted_at": attempt.submitted_at,
        "batch_number": attempt.batch_number,
        "session_complete": session_complete,
        "next_batch_available": session is not None and not session_complete,
        "progress": _session_progress(db, session) if session is not None else None,
        "final_result": final_result,
    }


# ---------------------------------------------------------
# Get result
# ---------------------------------------------------------

@router.get("/{attempt_id}/result")
def get_attempt_result(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = db.query(ExamAttempt).filter(
        ExamAttempt.id == attempt_id,
        ExamAttempt.student_id == current_user.id,
    ).first()

    if not attempt:
        raise HTTPException(
            status_code=404,
            detail="Attempt not found",
        )

    if attempt.status != "submitted":
        raise HTTPException(
            status_code=400,
            detail="This exam has not been submitted yet",
        )

    exam = db.get(Exam, attempt.exam_id)
    if exam is None:
        raise HTTPException(status_code=404, detail="Exam not found")

    session = db.get(ExamSession, attempt.session_id) if attempt.session_id else None
    if session is not None and session.status == "completed":
        return _final_result(db, session)

    percentage = 0

    if attempt.total_marks > 0:
        percentage = (
            attempt.obtained_marks / attempt.total_marks
        ) * 100

    return {
        "attempt_id": attempt.id,
        "exam_id": attempt.exam_id,
        "student_id": attempt.student_id,
        "score": attempt.obtained_marks,
        "total_marks": attempt.total_marks,
        "percentage": percentage,
        "passing_marks": _effective_passing_marks(attempt),
        "passed": attempt.obtained_marks >= _effective_passing_marks(attempt),
        "status": attempt.status,
        "started_at": attempt.started_at,
        "submitted_at": attempt.submitted_at,
    }