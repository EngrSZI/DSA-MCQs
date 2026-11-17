# Run the MCQ Examination System from your Windows computer

This package is configured for a local Windows deployment with:

- React/Vite student interface on port 5173
- FastAPI API on port 8000
- PostgreSQL in Docker on port 5433
- Vite same-origin proxy so students do not need direct API access
- The existing 1,080-question DSA bank and 13-minute/25-question exam seed
- Optional Cloudflare Quick Tunnel for a public HTTPS URL

## 1. Prerequisites

Install/run:

- Docker Desktop
- Python 3.11+ (3.12 is also suitable)
- Node.js 20+
- cloudflared (only if students will access the system over the Internet)

Install cloudflared from the official Cloudflare downloads page:
https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

You can place `cloudflared.exe` at `C:\cloudflared\cloudflared.exe`.

## 2. First local startup

Open PowerShell in this project folder and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\START_EXAM_LOCAL.ps1
```

The script starts PostgreSQL, creates the Python virtual environment, installs backend dependencies, runs Alembic migrations, imports/updates the DSA bank, installs frontend dependencies, and starts FastAPI and Vite in separate windows.

## 3. Test locally

Open:

- Student site: http://localhost:5173/
- API health: http://localhost:8000/health
- API docs: http://localhost:8000/docs

The health endpoint should return:

```json
{"status":"healthy"}
```

## 4. Make it available to students for free

After the local site works, double-click:

`CLOUDFLARE_TUNNEL.bat`

or run:

```powershell
C:\cloudflared\cloudflared.exe tunnel --url http://127.0.0.1:5173
```

Cloudflare will print an HTTPS address ending in:

`trycloudflare.com`

Give that HTTPS address to students.

Do NOT give students `http://localhost:5173`. That points to each student's own computer.

## 5. Test from another network

Use a phone on mobile data or another computer outside your local network and open the Cloudflare HTTPS URL.

Test:

1. Login with a test student.
2. Start the DSA exam.
3. Verify 25 questions.
4. Verify the 13-minute timer.
5. Submit.
6. Verify the score.

## 6. During the exam

Keep all of these running:

- Docker Desktop
- PostgreSQL container
- FastAPI PowerShell window
- Vite PowerShell window
- Cloudflare Tunnel window
- The Windows computer must remain powered on and connected to the Internet.

Prevent Windows from sleeping during the examination.

## 7. Stop the system

Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\STOP_EXAM_LOCAL.ps1
```

The Docker volume is preserved by `docker compose down`, so the PostgreSQL data is not removed.

## Important security notes

- Do not expose PostgreSQL directly to the Internet.
- Do not commit `backend/.env` to GitHub.
- The Cloudflare Quick Tunnel URL is temporary and changes when the tunnel is restarted.
- This setup is appropriate for a controlled class/exam session. For a permanent university service, use a university server or managed hosting.
- Take a PostgreSQL backup before the real exam.
