NSCT PREPARATION QUESTION BANK
=============================

Source workbook:
NSCT_Prep_All_Subjects_MCQs.xlsx

The backend seed script imports this workbook during deployment. It reads
worksheets with columns identifying the question, four answer options, and
correct answer. Subject and difficulty columns are imported when present; if
subject is represented by separate worksheets, the worksheet name is used.
Rows missing an option or a recognized correct answer are skipped with a
warning.

Students choose a subject, difficulty level, and question count before an
attempt begins. The available maximum is the number of valid questions in that
subject/difficulty selection; there is no fixed 400-question cap.
