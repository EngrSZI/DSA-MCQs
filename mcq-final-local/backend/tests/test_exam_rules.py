from types import SimpleNamespace

from app.routers.attempts import (
    _normalize_submitted_answers,
    _select_fair_question_assignments,
    apply_tab_switch_penalty,
)
from app.routers.results import _serialize_admin_attempt
from app.services.result_exporter import _tab_switch_count


def test_apply_tab_switch_penalty_subtracts_each_violation():
    assert apply_tab_switch_penalty(5.0, 0.4) == 4.6
    assert apply_tab_switch_penalty(0.0, 0.2) == -0.2


def test_export_tab_switch_count_is_derived_from_recorded_score_deduction():
    assert _tab_switch_count(0.8, 0.4) == 2
    assert _tab_switch_count(-0.2, -0.6) == 2
    assert _tab_switch_count(0.8, 0.8) == 0


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
    assert summary["tab_switch_deduction"] == 0.2
    assert summary["tab_switch_count"] == 1
    assert summary["total_deductions"] == 0.4
    assert summary["questions"][0]["correct_answer"] == "Alpha"
    assert summary["questions"][1]["selected_answer"] == "Three"
