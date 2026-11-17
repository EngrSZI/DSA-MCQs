import csv
import os
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models.subject import Subject
from app.models.question import Question
from app.models.exam import Exam
from app.models.exam_question import ExamQuestion

BASE = Path(__file__).resolve().parents[1]
CSV_PATH = BASE / "dsa_1080_questions.csv"

EXAM_TITLE = "Data Structures & Algorithms – NSCT Preparation"
SUBJECT_CODE = "DSA-NSCT"

def main():
    db = SessionLocal()
    try:
        subject = db.scalar(select(Subject).where(Subject.code == SUBJECT_CODE))
        if subject is None:
            subject = Subject(name="Data Structures & Algorithms", code=SUBJECT_CODE, description="NSCT DSA preparation question bank")
            db.add(subject)
            db.flush()

        exam = db.scalar(select(Exam).where(Exam.title == EXAM_TITLE))
        if exam is None:
            exam = Exam(subject_id=subject.id, title=EXAM_TITLE, description="1080-question DSA bank. Each batch selects 25 unattempted questions for 13 minutes.", duration_minutes=13, total_marks=0.0, passing_marks=200.0, is_published=True, is_active=True)
            db.add(exam)
            db.flush()

        existing = {qid for (qid,) in db.execute(select(ExamQuestion.question_id).where(ExamQuestion.exam_id == exam.id)).all()}
        created = 0
        with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                text = (row.get("question_text") or "").strip()
                if not text:
                    continue
                source_no = int(row.get("question_number") or 0)
                question = db.scalar(select(Question).where(Question.subject_id == subject.id, Question.question_text == text))
                if question is None:
                    question = Question(subject_id=subject.id, question_text=text, option_a=row["option_a"], option_b=row["option_b"], option_c=row["option_c"], option_d=row["option_d"], correct_option=row["correct_option"].strip().upper(), difficulty=row.get("difficulty") or "medium", marks=1.0, is_active=True)
                    db.add(question)
                    db.flush()
                if question.id not in existing:
                    db.add(ExamQuestion(exam_id=exam.id, question_id=question.id, question_order=source_no or question.id, marks=1.0))
                    existing.add(question.id)
                    created += 1

        total = len(existing) * 1.0
        # Students receive at most 400 questions, so 50% of the maximum
        # student allocation is 200 marks.
        exam.total_marks = total
        exam.passing_marks = 200.0
        db.commit()
        print(f"Subject ID: {subject.id}")
        print(f"Exam ID: {exam.id}")
        print(f"Questions linked: {len(existing)}")
        print(f"New links created: {created}")
        print(f"Total bank marks: {exam.total_marks}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
