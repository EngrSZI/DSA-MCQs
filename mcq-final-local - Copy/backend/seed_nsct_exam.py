import logging
import re
from pathlib import Path

from openpyxl import load_workbook
from sqlalchemy import select

from app.database import SessionLocal
from app.models.subject import Subject
from app.models.question import Question
from app.models.exam import Exam
from app.models.exam_question import ExamQuestion

BASE = Path(__file__).resolve().parents[1]
WORKBOOK_PATH = BASE / "NSCT_Prep_All_Subjects_MCQs.xlsx"

EXAM_TITLE = "NSCT Preparation - All Subjects"
LEGACY_EXAM_TITLE = "Data Structures & Algorithms – NSCT Preparation"
BANK_SUBJECT_CODE = "NSCT-ALL"
logger = logging.getLogger(__name__)

HEADER_ALIASES = {
    "question": {"question", "questiontext", "mcq", "questionstatement"},
    "option_a": {"a", "optiona", "choicea", "answera", "option1", "choice1"},
    "option_b": {"b", "optionb", "choiceb", "answerb", "option2", "choice2"},
    "option_c": {"c", "optionc", "choicec", "answerc", "option3", "choice3"},
    "option_d": {"d", "optiond", "choiced", "answerd", "option4", "choice4"},
    "correct": {"correctoption", "correctanswer", "answerkey", "key", "rightanswer"},
    "subject": {"subject", "subjectname", "subjectarea", "discipline", "topic", "category"},
    "difficulty": {"difficulty", "level", "questionlevel", "complexity"},
    "marks": {"marks", "mark", "points", "score"},
    "active": {"isactive", "active", "status"},
    "explanation": {"explanation", "solution", "rationale"},
}


def _normalize_header(value) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _find_column(headers: list, field: str) -> int | None:
    aliases = HEADER_ALIASES[field]
    normalized = [_normalize_header(header) for header in headers]
    for index, header in enumerate(normalized):
        if header in aliases:
            return index
    for index, header in enumerate(normalized):
        if any(alias in header for alias in aliases if len(alias) > 2):
            return index
    return None


def _header_row(rows: list[list]) -> tuple[int, dict[str, int]]:
    required = {"question", "option_a", "option_b", "option_c", "option_d", "correct"}
    for row_index, row in enumerate(rows[:30]):
        columns = {
            field: column
            for field in HEADER_ALIASES
            if (column := _find_column(row, field)) is not None
        }
        if required.issubset(columns):
            return row_index, columns
    raise ValueError("Could not find a question/options/answer header row in the workbook.")


def _cell(row: list, columns: dict[str, int], field: str, default=None):
    column = columns.get(field)
    if column is None or column >= len(row):
        return default
    return row[column]


def _clean_text(value) -> str:
    return str(value).strip() if value is not None else ""


def _correct_option(value, options: list[str]) -> str:
    answer = _clean_text(value).upper()
    if answer in {"1", "2", "3", "4"}:
        return "ABCD"[int(answer) - 1]
    match = re.search(r"\b([ABCD])\b", answer)
    if match:
        return match.group(1)
    for letter, option in zip("ABCD", options):
        if answer and answer == option.strip().upper():
            return letter
    raise ValueError(f"Unrecognized correct answer: {value!r}")


def _is_active(value) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() not in {"false", "0", "no", "inactive"}


def _read_questions():
    if not WORKBOOK_PATH.is_file():
        raise FileNotFoundError(f"Question workbook not found: {WORKBOOK_PATH}")

    workbook = load_workbook(WORKBOOK_PATH, read_only=True, data_only=True)
    for worksheet in workbook.worksheets:
        rows = list(worksheet.iter_rows(values_only=True))
        header_index, columns = _header_row(rows)
        last_subject = worksheet.title
        last_difficulty = "medium"

        for row_number, row in enumerate(rows[header_index + 1:], start=header_index + 2):
            question_text = _clean_text(_cell(row, columns, "question"))
            if not question_text:
                continue
            if not _is_active(_cell(row, columns, "active")):
                continue

            subject_value = _clean_text(_cell(row, columns, "subject"))
            if subject_value:
                last_subject = subject_value
            difficulty_value = _clean_text(_cell(row, columns, "difficulty"))
            if difficulty_value:
                last_difficulty = difficulty_value.lower()

            options = [
                _clean_text(_cell(row, columns, f"option_{letter.lower()}"))
                for letter in "ABCD"
            ]
            if not all(options):
                logger.warning(
                    "Skipping workbook row %s:%s because one or more answer options are missing",
                    worksheet.title,
                    row_number,
                )
                continue
            try:
                correct_option = _correct_option(_cell(row, columns, "correct"), options)
            except ValueError:
                logger.warning(
                    "Skipping workbook row %s:%s because its correct answer is not recognized",
                    worksheet.title,
                    row_number,
                )
                continue
            yield {
                "subject": last_subject,
                "question_text": question_text,
                "option_a": options[0],
                "option_b": options[1],
                "option_c": options[2],
                "option_d": options[3],
                "correct_option": correct_option,
                "difficulty": last_difficulty,
                "marks": float(_cell(row, columns, "marks", 1) or 1),
                "explanation": _clean_text(_cell(row, columns, "explanation")) or None,
            }
    workbook.close()


def _subject_code(name: str, existing_codes: set[str]) -> str:
    base_code = re.sub(r"[^A-Z0-9]+", "-", name.upper()).strip("-")[:24] or "SUBJECT"
    code = base_code
    suffix = 2
    while code in existing_codes:
        code = f"{base_code[:24 - len(str(suffix))]}-{suffix}"
        suffix += 1
    existing_codes.add(code)
    return code


def seed_nsct_exam(db):
    bank_subject = db.scalar(select(Subject).where(Subject.code == BANK_SUBJECT_CODE))
    if bank_subject is None:
        bank_subject = Subject(
            name="NSCT Preparation",
            code=BANK_SUBJECT_CODE,
            description="Container subject for the multi-subject NSCT question bank",
        )
        db.add(bank_subject)
        db.flush()

    exam = db.scalar(select(Exam).where(Exam.title == EXAM_TITLE))
    if exam is None:
        exam = db.scalar(select(Exam).where(Exam.title == LEGACY_EXAM_TITLE))
    if exam is None:
        exam = Exam(
            subject_id=bank_subject.id,
            title=EXAM_TITLE,
            description="Select a subject, difficulty level, and question count before starting.",
            duration_minutes=13,
            total_marks=0.0,
            passing_marks=0.0,
            is_published=True,
            is_active=True,
        )
        db.add(exam)
        db.flush()
    else:
        exam.subject_id = bank_subject.id
        exam.title = EXAM_TITLE
        exam.description = "Select a subject, difficulty level, and question count before starting."
        exam.is_published = True
        exam.is_active = True

    question_rows = list(_read_questions())
    if not question_rows:
        raise ValueError("The workbook does not contain any valid questions.")

    db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam.id).delete(
        synchronize_session=False
    )

    subjects = {
        subject.name.casefold(): subject
        for subject in db.scalars(select(Subject)).all()
        if subject.id != bank_subject.id
    }
    used_codes = {subject.code for subject in db.scalars(select(Subject)).all()}
    linked_question_ids = set()
    question_subjects = set()
    imported = 0
    for item in question_rows:
        subject_name = item.pop("subject").strip()[:150] or "General"
        question_subjects.add(subject_name)
        subject = subjects.get(subject_name.casefold())
        if subject is None:
            subject = Subject(
                name=subject_name,
                code=_subject_code(subject_name, used_codes),
            )
            db.add(subject)
            db.flush()
            subjects[subject_name.casefold()] = subject

        question = db.scalar(select(Question).where(
            Question.subject_id == subject.id,
            Question.question_text == item["question_text"],
        ))
        if question is None:
            question = Question(subject_id=subject.id, **item)
            db.add(question)
            db.flush()
        else:
            for field, value in item.items():
                setattr(question, field, value)
            question.is_active = True

        if question.id in linked_question_ids:
            continue
        db.add(ExamQuestion(
            exam_id=exam.id,
            question_id=question.id,
            question_order=imported + 1,
            marks=question.marks,
        ))
        linked_question_ids.add(question.id)
        imported += 1

    exam.total_marks = float(imported)
    exam.passing_marks = float((imported + 1) // 2)
    db.commit()
    logger.info(
        "NSCT question bank seeded: exam_id=%s, questions=%s, subjects=%s",
        exam.id,
        imported,
        len(question_subjects),
    )


def main():
    db = SessionLocal()
    try:
        seed_nsct_exam(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
