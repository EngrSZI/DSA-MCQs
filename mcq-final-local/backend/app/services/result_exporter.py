from __future__ import annotations

from datetime import datetime
from pathlib import Path
from threading import Lock

from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session

try:
    from app.models import AnswerSubmission, AttemptQuestion, Exam, ExamAttempt, ExamSession, Question, User
except ModuleNotFoundError:
    from backend.app.models import AnswerSubmission, AttemptQuestion, Exam, ExamAttempt, ExamSession, Question, User


EXPORT_DIR = Path(__file__).resolve().parents[2] / "exports"
EXPORT_FILE = EXPORT_DIR / "student_results.xlsx"
TAB_SWITCH_PENALTY = 0.20
_export_lock = Lock()


def _autosize(ws):
    for column_cells in ws.columns:
        length = 0
        for cell in column_cells:
            value = "" if cell.value is None else str(cell.value)
            length = max(length, len(value))
        ws.column_dimensions[get_column_letter(column_cells[0].column)].width = min(length + 2, 45)


def _tab_switch_count(raw_answer_marks: float, obtained_marks: float) -> int:
    penalty = max(0.0, raw_answer_marks - obtained_marks)
    return int(round(penalty / TAB_SWITCH_PENALTY))


def export_results(db: Session) -> Path:
    """Write all persisted exam attempts/answers to a local Excel workbook.

    The export is deliberately rebuilt from PostgreSQL so the Excel file is a
    processing/reporting copy, not the source of truth. Failures here should
    never prevent an exam submission from being committed.
    """
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    with _export_lock:
        workbook = Workbook()
        ws = workbook.active
        ws.title = "Results"
        ws.append([
            "Attempt ID", "Session ID", "Student ID", "Student Name", "Student Email",
            "Exam ID", "Exam Title", "Batch", "Status", "Started At", "Submitted At",
            "Questions", "Attempted", "Correct", "Wrong", "Unanswered",
            "Tab Switch Count", "Tab Switch Deduction",
            "Score", "Total Marks", "Percentage", "Passed"
        ])

        attempts = (
            db.query(ExamAttempt, User, Exam)
            .join(User, User.id == ExamAttempt.student_id)
            .join(Exam, Exam.id == ExamAttempt.exam_id)
            .order_by(ExamAttempt.id)
            .all()
        )

        for attempt, user, exam in attempts:
            answer_rows = db.query(AnswerSubmission).filter(
                AnswerSubmission.attempt_id == attempt.id
            ).all()
            attempted = len(answer_rows)
            correct = sum(1 for a in answer_rows if a.is_correct)
            wrong = sum(1 for a in answer_rows if not a.is_correct)
            raw_answer_marks = sum(a.marks_awarded for a in answer_rows)
            tab_switch_deduction = round(
                max(0.0, raw_answer_marks - attempt.obtained_marks), 2
            )
            tab_switch_count = _tab_switch_count(
                raw_answer_marks, attempt.obtained_marks
            )
            questions = db.query(AnswerSubmission.question_id).filter(
                AnswerSubmission.attempt_id == attempt.id
            ).count()
            # AttemptQuestion is the authoritative count of assigned questions.
            try:
                from app.models import AttemptQuestion
            except ModuleNotFoundError:
                from backend.app.models import AttemptQuestion
            questions = db.query(AttemptQuestion).filter(
                AttemptQuestion.attempt_id == attempt.id
            ).count()
            unanswered = max(0, questions - attempted)
            percentage = (attempt.obtained_marks / attempt.total_marks * 100) if attempt.total_marks else 0
            passed = attempt.obtained_marks >= attempt.passing_marks
            ws.append([
                attempt.id, attempt.session_id, user.student_id or user.id, user.full_name, user.email,
                exam.id, exam.title, attempt.batch_number, attempt.status,
                attempt.started_at, attempt.submitted_at, questions, attempted,
                correct, wrong, unanswered, tab_switch_count, tab_switch_deduction,
                attempt.obtained_marks,
                attempt.total_marks, round(percentage, 2), passed
            ])

        answers_ws = workbook.create_sheet("Answers")
        answers_ws.append([
            "Answer ID", "Attempt ID", "Session ID", "Student ID", "Student Name",
            "Student Email", "Exam ID", "Exam Title", "Batch", "Question ID",
            "Selected Option", "Correct Option", "Is Correct", "Marks Awarded", "Answered At"
        ])
        answer_rows = (
            db.query(AnswerSubmission, ExamAttempt, User, Exam)
            .join(ExamAttempt, ExamAttempt.id == AnswerSubmission.attempt_id)
            .join(User, User.id == ExamAttempt.student_id)
            .join(Exam, Exam.id == ExamAttempt.exam_id)
            .order_by(AnswerSubmission.id)
            .all()
        )
        for answer, attempt, user, exam in answer_rows:
            answers_ws.append([
                answer.id, attempt.id, attempt.session_id, user.student_id or user.id, user.full_name,
                user.email, exam.id, exam.title, attempt.batch_number, answer.question_id,
                answer.selected_option, answer.correct_option, answer.is_correct,
                answer.marks_awarded, answer.answered_at
            ])

        summary_ws = workbook.create_sheet("Session Summary")
        summary_ws.append([
            "Session ID", "Student ID", "Student Name", "Student Email", "Exam ID",
            "Exam Title", "Batches Submitted", "Total Questions", "Total Marks",
            "Obtained Marks", "Percentage", "Status", "Started At", "Completed At"
        ])
        sessions = (
            db.query(ExamSession, User, Exam)
            .join(User, User.id == ExamSession.student_id)
            .join(Exam, Exam.id == ExamSession.exam_id)
            .order_by(ExamSession.id)
            .all()
        )
        for session, user, exam in sessions:
            submitted = db.query(ExamAttempt).filter(
                ExamAttempt.session_id == session.id,
                ExamAttempt.status == "submitted",
            ).all()
            obtained = sum(a.obtained_marks for a in submitted)
            percentage = (obtained / session.total_marks * 100) if session.total_marks else 0
            summary_ws.append([
                session.id, user.student_id or user.id, user.full_name, user.email, exam.id, exam.title,
                len(submitted), session.total_questions, session.total_marks,
                obtained, round(percentage, 2), session.status,
                session.started_at, session.completed_at
            ])

        # ---------------------------------------------------------
        # Student question-allocation/progress tracking
        # ---------------------------------------------------------
        # AttemptQuestion is authoritative for allocation: once a question is
        # assigned to a student it is never eligible for that student again.
        MAX_QUESTIONS_PER_STUDENT = 400

        progress_ws = workbook.create_sheet("Student Summary")
        progress_ws.append([
            "Student ID", "Student Name", "Email", "Program", "Exam ID", "Exam Title",
            "Maximum Questions", "Questions Assigned", "Questions Answered",
            "Questions Remaining", "Completion %", "Correct", "Wrong",
            "Tab Switch Count", "Score", "Completed 400"
        ])

        students = db.query(User).filter(User.role == "student").order_by(User.id).all()
        for user in students:
            exams_for_student = (
                db.query(Exam)
                .join(ExamSession, ExamSession.exam_id == Exam.id)
                .filter(ExamSession.student_id == user.id)
                .distinct()
                .all()
            )
            # Include published/active exams even if the student has not started
            # yet, so the report can show zero progress.
            if not exams_for_student:
                exams_for_student = db.query(Exam).filter(Exam.is_active.is_(True)).all()

            for exam in exams_for_student:
                assigned_ids = [
                    qid for (qid,) in db.query(AttemptQuestion.question_id)
                    .join(ExamAttempt, ExamAttempt.id == AttemptQuestion.attempt_id)
                    .filter(
                        ExamAttempt.student_id == user.id,
                        ExamAttempt.exam_id == exam.id,
                    )
                    .distinct()
                    .all()
                ]
                assigned_count = len(assigned_ids)
                answered_count = db.query(AnswerSubmission.question_id).join(
                    ExamAttempt, ExamAttempt.id == AnswerSubmission.attempt_id
                ).filter(
                    ExamAttempt.student_id == user.id,
                    ExamAttempt.exam_id == exam.id,
                ).distinct().count()
                correct_count = db.query(AnswerSubmission).join(
                    ExamAttempt, ExamAttempt.id == AnswerSubmission.attempt_id
                ).filter(
                    ExamAttempt.student_id == user.id,
                    ExamAttempt.exam_id == exam.id,
                    AnswerSubmission.is_correct.is_(True),
                ).count()
                wrong_count = db.query(AnswerSubmission).join(
                    ExamAttempt, ExamAttempt.id == AnswerSubmission.attempt_id
                ).filter(
                    ExamAttempt.student_id == user.id,
                    ExamAttempt.exam_id == exam.id,
                    AnswerSubmission.is_correct.is_(False),
                ).count()
                submitted_attempts = db.query(ExamAttempt).filter(
                    ExamAttempt.student_id == user.id,
                    ExamAttempt.exam_id == exam.id,
                    ExamAttempt.status == "submitted",
                ).all()
                tab_switch_count = 0
                for attempt in submitted_attempts:
                    attempt_answer_marks = sum(
                        answer.marks_awarded
                        for answer in db.query(AnswerSubmission).filter(
                            AnswerSubmission.attempt_id == attempt.id
                        ).all()
                    )
                    tab_switch_count += _tab_switch_count(
                        attempt_answer_marks, attempt.obtained_marks
                    )
                score = sum(
                    a.marks_awarded for a in db.query(AnswerSubmission).join(
                        ExamAttempt, ExamAttempt.id == AnswerSubmission.attempt_id
                    ).filter(
                        ExamAttempt.student_id == user.id,
                        ExamAttempt.exam_id == exam.id,
                    ).all()
                )
                progress_ws.append([
                    user.student_id or user.id, user.full_name, user.email, user.program,
                    exam.id, exam.title, MAX_QUESTIONS_PER_STUDENT, assigned_count,
                    answered_count, max(0, MAX_QUESTIONS_PER_STUDENT - assigned_count),
                    round(min(100, assigned_count / MAX_QUESTIONS_PER_STUDENT * 100), 2),
                    correct_count, wrong_count, tab_switch_count, score,
                    assigned_count >= MAX_QUESTIONS_PER_STUDENT
                ])

        tracking_ws = workbook.create_sheet("Question Tracking")
        tracking_ws.append([
            "Student ID", "Student Name", "Exam ID", "Exam Title", "Attempt ID",
            "Batch", "Question ID", "Question Number", "Assigned At", "Answered",
            "Selected Option", "Correct Option", "Correct", "Marks Awarded"
        ])
        tracking_rows = (
            db.query(AttemptQuestion, ExamAttempt, User, Exam)
            .join(ExamAttempt, ExamAttempt.id == AttemptQuestion.attempt_id)
            .join(User, User.id == ExamAttempt.student_id)
            .join(Exam, Exam.id == ExamAttempt.exam_id)
            .order_by(User.id, Exam.id, AttemptQuestion.id)
            .all()
        )
        for aq, attempt, user, exam in tracking_rows:
            answer = db.query(AnswerSubmission).filter(
                AnswerSubmission.attempt_id == attempt.id,
                AnswerSubmission.question_id == aq.question_id,
            ).first()
            tracking_ws.append([
                user.student_id or user.id, user.full_name, exam.id, exam.title,
                attempt.id, attempt.batch_number, aq.question_id, aq.question_id,
                aq.created_at, bool(answer), answer.selected_option if answer else None,
                aq.correct_option, answer.is_correct if answer else None,
                answer.marks_awarded if answer else 0
            ])

        coverage_ws = workbook.create_sheet("Question Coverage")
        coverage_ws.append([
            "Exam ID", "Exam Title", "Question ID", "Students Assigned",
            "Students Answered", "Students Remaining", "Assignment %"
        ])
        for exam in db.query(Exam).order_by(Exam.id).all():
            # Use AttemptQuestion directly so this sheet reflects actual student
            # allocations rather than merely configured exam questions.
            qids = [qid for (qid,) in db.query(AttemptQuestion.question_id)
                    .join(ExamAttempt, ExamAttempt.id == AttemptQuestion.attempt_id)
                    .filter(ExamAttempt.exam_id == exam.id)
                    .distinct().all()]
            for qid in qids:
                assigned_students = db.query(ExamAttempt.student_id).join(
                    AttemptQuestion, AttemptQuestion.attempt_id == ExamAttempt.id
                ).filter(
                    ExamAttempt.exam_id == exam.id,
                    AttemptQuestion.question_id == qid,
                ).distinct().count()
                answered_students = db.query(ExamAttempt.student_id).join(
                    AnswerSubmission, AnswerSubmission.attempt_id == ExamAttempt.id
                ).filter(
                    ExamAttempt.exam_id == exam.id,
                    AnswerSubmission.question_id == qid,
                ).distinct().count()
                total_students = db.query(User.id).filter(User.role == "student").count()
                coverage_ws.append([
                    exam.id, exam.title, qid, assigned_students, answered_students,
                    max(0, total_students - assigned_students),
                    round(assigned_students / total_students * 100, 2) if total_students else 0
                ])

        for sheet in workbook.worksheets:
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            _autosize(sheet)

        try:
            workbook.save(EXPORT_FILE)
        except PermissionError:
            # Windows may have the workbook open in Excel. Keep the exam working
            # and leave the existing export intact; the admin can close Excel and
            # use the export endpoint to regenerate it.
            return EXPORT_FILE

    return EXPORT_FILE
