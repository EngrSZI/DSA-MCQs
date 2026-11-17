# MCQ Examination System - Local Windows Deployment

## Exam behavior
- 25 questions per timed attempt
- Each student receives a maximum of 400 unique questions from the 1,080-question bank
- Questions are selected randomly and never repeated for the same student
- Student progress is tracked against the 400-question allocation
- 13-minute server-enforced timer
- Correct: +1.00
- Wrong: -0.20
- Unanswered: 0
- Timeout automatically submits the current answers
- Submission is final; no new batch starts automatically
- Student is logged out after submission
- Answers/results are stored in PostgreSQL
- PostgreSQL is the source of truth

## Excel results
The backend automatically regenerates `backend/exports/student_results.xlsx` after each successful submission. It contains:
- Results: one row per submitted batch
- Answers: one row per saved answer
- Session Summary: cumulative student/exam results
- Results includes tab-switch count and deduction per batch; Student Summary includes each student's total count per exam

An administrator can also download the latest workbook through:
`GET /admin/results/export.xlsx`
with an admin Bearer token.

## Start
Run `START_EXAM_LOCAL.ps1` from PowerShell. Then open `http://localhost:5173/`.
