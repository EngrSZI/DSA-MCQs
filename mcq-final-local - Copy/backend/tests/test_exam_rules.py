from types import SimpleNamespace

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Exam, ExamQuestion, Question, Subject
from app.routers.attempts import (
    _normalize_submitted_answers,
    _select_fair_question_assignments,
    _effective_passing_marks,
    _submission_answers_for_attempt,
)
from app.routers.results import _serialize_admin_attempt
from seed_nsct_exam import _read_questions, seed_nsct_exam


def test_nsct_workbook_has_multiple_subjects_and_more_than_400_questions():
    questions = list(_read_questions())

    assert len(questions) > 400
    assert len({question["subject"] for question in questions}) > 1
    assert len({question["difficulty"] for question in questions}) > 1


def test_seed_creates_published_exam_and_is_repeatable():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as db:
            seed_nsct_exam(db)
            seed_nsct_exam(db)

            exam = db.scalar(select(Exam).where(
                Exam.title == "NSCT Preparation - All Subjects"
            ))
            assert exam is not None
            assert exam.is_published is True
            assert exam.is_active is True
            assert exam.passing_marks == (exam.total_marks + 1) // 2
            assert db.scalar(select(func.count(ExamQuestion.id)).where(
                ExamQuestion.exam_id == exam.id
            )) > 400
            assert db.scalar(select(func.count(Subject.id)).where(
                Subject.id != exam.subject_id
            )) > 1
            assert db.scalar(select(func.count(Question.id))) > 400
    finally:
        Base.metadata.drop_all(engine)


def test_zero_passing_threshold_uses_half_of_attempt_marks():
    attempt = SimpleNamespace(total_marks=5.0, passing_marks=0.0)

    assert _effective_passing_marks(attempt) == 3.0


def test_configured_passing_threshold_is_preserved():
    attempt = SimpleNamespace(total_marks=5.0, passing_marks=2.0)

    assert _effective_passing_marks(attempt) == 2.0


def test_select_fair_question_assignments_prioritizes_least_used_questions():
    assignments = [
        SimpleNamespace(question_id=101),
        SimpleNamespace(question_id=102),
        SimpleNamespace(question_id=103),
        SimpleNamespace(question_id=104),
    ]
    usage_counts = {101: 4, 102: 0, 103: 1, 104: 0}

    selected = _select_fair_question_assignments(assignments, 2, usage_counts)

    assert set(question.question_id for question in selected) == {102, 104}


def test_normalize_submitted_answers_ignores_unanswered_questions():
    answers = [
        SimpleNamespace(question_id=1, selected_option="A"),
        SimpleNamespace(question_id=2, selected_option=None),
        SimpleNamespace(question_id=3, selected_option=""),
        SimpleNamespace(question_id=4, selected_option="B"),
    ]

    normalized = _normalize_submitted_answers(answers)

    assert normalized == {1: "A", 4: "B"}


def test_expired_submission_discards_answers_instead_of_scoring_them():
    submitted_answers = [
        SimpleNamespace(question_id=1, selected_option="A"),
    ]
    attempt_questions = [SimpleNamespace(question_id=1)]

    assert _submission_answers_for_attempt(
        submitted_answers, attempt_questions, expired=True
    ) == {}


def test_admin_attempt_summary_includes_correct_answers_and_deductions():
    attempt = SimpleNamespace(
        id=15,
        batch_number=2,
        status="submitted",
        started_at=None,
        submitted_at=None,
        obtained_marks=0.6,
        total_marks=2.0,
    )
    assigned_questions = [
        (
            SimpleNamespace(question_order=1, correct_option="A"),
            SimpleNamespace(
                id=101,
                question_text="First question?",
                option_a="Alpha",
                option_b="Beta",
                option_c="Gamma",
                option_d="Delta",
            ),
        ),
        (
            SimpleNamespace(question_order=2, correct_option="B"),
            SimpleNamespace(
                id=102,
                question_text="Second question?",
                option_a="One",
                option_b="Two",
                option_c="Three",
                option_d="Four",
            ),
        ),
    ]
    answers = [
        SimpleNamespace(
            question_id=101,
            selected_option="A",
            is_correct=True,
            marks_awarded=1.0,
        ),
        SimpleNamespace(
            question_id=102,
            selected_option="C",
            is_correct=False,
            marks_awarded=-0.2,
        ),
    ]

    summary = _serialize_admin_attempt(attempt, assigned_questions, answers)

    assert summary["correct_count"] == 1
    assert summary["wrong_count"] == 1
    assert summary["wrong_answer_deduction"] == 0.2
    assert "tab_switch_deduction" not in summary
    assert "tab_switch_count" not in summary
    assert summary["total_deductions"] == 0.2
    assert summary["questions"][0]["correct_answer"] == "Alpha"
    assert summary["questions"][1]["selected_answer"] == "Three"


def test_admin_attempt_summary_does_not_grade_answers_before_submission():
    attempt = SimpleNamespace(
        id=16,
        batch_number=1,
        status="in_progress",
        started_at=None,
        submitted_at=None,
        obtained_marks=0.0,
        total_marks=1.0,
    )
    question = SimpleNamespace(
        id=201,
        question_order=1,
        correct_option="A",
        question_text="Question?",
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
    )
    answer = SimpleNamespace(
        question_id=201,
        selected_option="B",
        is_correct=False,
        marks_awarded=0.0,
    )

    summary = _serialize_admin_attempt(attempt, [(question, question)], [answer])

    assert summary["questions_attempted"] == 1
    assert summary["correct_count"] == 0
    assert summary["wrong_count"] == 0
    assert summary["questions"][0]["selected_option"] == "B"
    assert summary["questions"][0]["correct_option"] is None
    assert summary["questions"][0]["is_correct"] is None
