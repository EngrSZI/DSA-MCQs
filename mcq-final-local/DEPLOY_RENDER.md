# Online Deployment — MCQ Examination System

This project is prepared for deployment on Render using the included `render.yaml` Blueprint. FastAPI supports container/server deployment and should run behind an HTTPS termination proxy in production. citeturn0search0turn0search5

## 1. Put the project in GitHub

Create a private GitHub repository and push this project. Do not commit `backend/.env`, real passwords, or production secrets.

## 2. Deploy the API and database with Render Blueprint

In Render, create a **Blueprint** and select the GitHub repository. Render will read `render.yaml` and create:

- `mcq-examination-api` — FastAPI API
- `mcq-examination-db` — PostgreSQL

The API runs Alembic migrations and then imports the DSA question bank from `dsa_1080_questions.csv`.

## 3. First deployment

After deployment, open:

- API health: `https://mcq-examination-api.onrender.com/health`
- API docs: `https://mcq-examination-api.onrender.com/docs`
- Student site: `https://engrszi.github.io/dsaquestion/`

The included GitHub Actions workflow builds and publishes the React frontend to GitHub Pages. Set the repository variable `VITE_API_BASE_URL` if the Render API hostname differs from the default.

## 4. Student accounts

Students can register through the API only if that route is exposed. For controlled university exams, create student accounts through an admin workflow rather than distributing a shared password.

## 5. Custom university domain

Add your university domain/subdomain to the frontend Render service, for example:

`exam.youruniversity.edu`

Then change the API `FRONTEND_URL` to that exact HTTPS origin and redeploy. HTTPS should be used for student login and examination traffic. citeturn0search5

## 6. DSA exam configuration

The seed script creates/updates:

- Data Structures & Algorithms – NSCT Preparation
- 1,080-question bank
- 25 randomly selected unattempted questions per batch
- 13-minute server-enforced attempt duration
-  +1.00 for a correct answer
- −0.05 for a wrong answer
- 0 for unanswered questions

The existing session logic continues selecting new unattempted batches until the student has exhausted the active question bank; when no questions remain, the API reports that all questions have been attempted.

## 7. Production checklist

Before giving the URL to students:

- Verify `/health` returns `healthy`.
- Verify `/docs` loads.
- Create a test student account.
- Test login from a different device/network.
- Start an exam and verify exactly 25 questions are returned.
- Verify the timer is 13 minutes.
- Submit one correct and one wrong answer and verify scoring.
- Verify a second batch contains no questions from the first batch.
- Verify that correct answers are not returned by the student question endpoint.
- Take a PostgreSQL backup before the real examination.
