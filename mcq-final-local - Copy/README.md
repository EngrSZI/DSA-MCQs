# MCQ Examination System

Local NSCT examination app built with FastAPI, PostgreSQL, and React.

## Run on a local network

See [README_LOCAL.md](./README_LOCAL.md). Start the host with
`.\START_EXAM_LOCAL.ps1`, then give students the LAN URL printed by the
script. Student devices and the host computer must be on the same trusted
network, and Windows Firewall must allow inbound TCP port 5173 on the Private
profile.

The startup script applies database migrations and imports the question bank
from `NSCT_Prep_All_Subjects_MCQs.xlsx`. Students select a subject, difficulty,
and question count before beginning.
