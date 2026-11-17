# Online Deployment — MCQ Examination System

This project is prepared for deployment on Render using the included `render.yaml` Blueprint. FastAPI supports container/server deployment and should run behind an HTTPS termination proxy in production. citeturn0search0turn0search5

## 1. Put the project in GitHub

Create a private GitHub repository and push this project. Do not commit `backend/.env`, real passwords, or production secrets.

## 2. Deploy the API and database with Render Blueprint

In Render, create a **Blueprint** and select the GitHub repository. Render will read `render.yaml` and create:

- `mcq-examination-api` — FastAPI API
- `mcq-examination-db` — PostgreSQL

The API runs Alembic migrations before startup. On startup, it imports `NSCT_Prep_All_Subjects_MCQs.xlsx` when the published NSCT exam is not yet present in the database. Seeding errors are logged and prevent the API from starting successfully.

## 3. First deployment

After deployment, open:

- API health: `https://mcq-examination-api.onrender.com/health`
- API docs: `https://mcq-examination-api.onrender.com/docs`
- Student site: `https://engrszi.github.io/dsaquestion/`

The included GitHub Actions workflow builds and publishes the React frontend to GitHub Pages. Set the repository variable `VITE_API_BASE_URL` if the Render API hostname differs from the default.

## 4. Student accounts

Student registration requires an administrator token. For controlled university exams, create student accounts through an admin workflow rather than distributing a shared password.

## 5. Custom university domain

Add your university domain/subdomain to the frontend Render service, for example:

`exam.youruniversity.edu`

Then change the API `FRONTEND_URL` to that exact HTTPS origin and redeploy. HTTPS should be used for student login and examination traffic. citeturn0search5

## 6. NSCT exam configuration

The seed script creates/updates the multi-subject exam from the workbook:

- Subject and difficulty categories found in the workbook
- A randomly selected set matching each student's subject, difficulty, and chosen question count
- No fixed 400-question allocation cap; the maximum selectable count is the matching bank size
- 13 minutes per 25 questions (rounded up) for the server-enforced attempt duration
-  +1.00 for a correct answer
- −0.20 for a wrong answer
- 0 for unanswered questions

The workbook must include columns identifying the question, four answer options, and correct answer. Subject and difficulty columns are used when present; when the workbook separates questions by worksheet, the worksheet name supplies the subject.

## 7. Production checklist

Before giving the URL to students:

- Verify `/health` returns `healthy`.
- Verify `/docs` loads.
- Create a test student account.
- Test login from a different device/network.
- Select a subject, difficulty, and question count, then verify the requested number of questions is returned.
- Verify an available question count greater than 400 can be selected.
- Verify the timer scales at 13 minutes per 25 questions.
- Submit one correct and one wrong answer and verify scoring.
- Verify that correct answers are not returned by the student question endpoint.
- Take a PostgreSQL backup before the real examination.
