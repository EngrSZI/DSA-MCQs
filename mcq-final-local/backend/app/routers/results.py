from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.dependencies import require_admin
    from app.models import AnswerSubmission, AttemptQuestion, Exam, ExamAttempt, Question, User
    from app.services.result_exporter import EXPORT_FILE, export_results
except ModuleNotFoundError:
    from backend.app.database import get_db
    from backend.app.dependencies import require_admin
    from backend.app.models import AnswerSubmission, AttemptQuestion, Exam, ExamAttempt, Question, User
    from backend.app.services.result_exporter import EXPORT_FILE, export_results

router = APIRouter(prefix="/admin/results", tags=["Admin Results"])
TAB_SWITCH_PENALTY = 0.20


def _serialize_admin_attempt(attempt, assigned_questions, answers):
    answers_by_question = {answer.question_id: answer for answer in answers}
    question_details = []
    for assignment, question in assigned_questions:
        answer = answers_by_question.get(question.id)
        options = {
            "A": question.option_a,
            "B": question.option_b,
            "C": question.option_c,
            "D": question.option_d,
        }
        correct_option = assignment.correct_option
        selected_option = answer.selected_option if answer else None
        question_details.append({
            "question_id": question.id,
            "question_number": assignment.question_order,
            "question_text": question.question_text,
            "selected_option": selected_option,
            "selected_answer": options.get(selected_option),
            "correct_option": correct_option,
            "correct_answer": options.get(correct_option),
            "is_correct": answer.is_correct if answer else None,
            "marks_awarded": answer.marks_awarded if answer else 0.0,
        })

    raw_answer_marks = sum(answer.marks_awarded for answer in answers)
    wrong_answer_deduction = round(
        sum(max(0.0, -answer.marks_awarded) for answer in answers), 2
    )
    tab_switch_deduction = round(
        max(0.0, raw_answer_marks - attempt.obtained_marks), 2
    )
    correct_count = sum(1 for answer in answers if answer.is_correct)
    wrong_count = sum(1 for answer in answers if not answer.is_correct)

    return {
        "attempt_id": attempt.id,
        "batch_number": attempt.batch_number,
        "status": attempt.status,
        "started_at": attempt.started_at,
        "submitted_at": attempt.submitted_at,
        "questions_assigned": len(assigned_questions),
        "questions_attempted": len(answers),
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "unanswered_count": max(0, len(assigned_questions) - len(answers)),
        "correct_marks": round(sum(max(0.0, answer.marks_awarded) for answer in answers), 2),
        "wrong_answer_deduction": wrong_answer_deduction,
        "tab_switch_deduction": tab_switch_deduction,
        "tab_switch_count": int(round(tab_switch_deduction / TAB_SWITCH_PENALTY)),
        "total_deductions": round(wrong_answer_deduction + tab_switch_deduction, 2),
        "cumulative_attempt_score": attempt.obtained_marks,
        "total_marks": attempt.total_marks,
        "questions": question_details,
    }


@router.get("/export.xlsx")
def export_student_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    path = export_results(db)
    return FileResponse(
        path=path,
        filename="student_results.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/students/{student_id}/attempts")
def get_student_attempt_details(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    student = db.scalar(
        select(User).where(User.id == student_id, User.role == "student")
    )
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    attempts = db.scalars(
        select(ExamAttempt)
        .where(ExamAttempt.student_id == student.id)
        .order_by(ExamAttempt.started_at, ExamAttempt.id)
    ).all()
    attempt_summaries = []
    for attempt in attempts:
        assigned_questions = db.execute(
            select(AttemptQuestion, Question)
            .join(Question, Question.id == AttemptQuestion.question_id)
            .where(AttemptQuestion.attempt_id == attempt.id)
            .order_by(AttemptQuestion.question_order)
        ).all()
        answers = db.scalars(
            select(AnswerSubmission)
            .where(AnswerSubmission.attempt_id == attempt.id)
            .order_by(AnswerSubmission.id)
        ).all()
        exam = db.get(Exam, attempt.exam_id)
        attempt_summary = _serialize_admin_attempt(
            attempt, assigned_questions, answers
        )
        attempt_summary["exam_id"] = attempt.exam_id
        attempt_summary["exam_title"] = exam.title if exam else "Unknown exam"
        attempt_summaries.append(attempt_summary)

    submitted_attempts = [
        attempt for attempt in attempt_summaries if attempt["status"] == "submitted"
    ]
    return {
        "student": {
            "id": student.id,
            "student_id": student.student_id or "",
            "full_name": student.full_name,
            "email": student.email,
        },
        "attempt_count": len(attempt_summaries),
        "cumulative_score": round(
            sum(attempt["cumulative_attempt_score"] for attempt in submitted_attempts), 2
        ),
        "cumulative_correct": sum(attempt["correct_count"] for attempt in submitted_attempts),
        "cumulative_wrong": sum(attempt["wrong_count"] for attempt in submitted_attempts),
        "cumulative_deductions": round(
            sum(attempt["total_deductions"] for attempt in submitted_attempts), 2
        ),
        "attempts": attempt_summaries,
    }
