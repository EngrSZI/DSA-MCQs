import smtplib
import time
import csv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ============================================================
# OUTLOOK / MICROSOFT 365 SETTINGS
# ============================================================

SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587

SENDER_EMAIL = "zaid.irshad@jinnah.edu"
SENDER_PASSWORD = "Itel82!@#"

# ============================================================
# SETTINGS
# ============================================================

QUIZ_URL = "http://10.23.120.84:5173/"

# IMPORTANT:
# True  = do NOT actually send emails; print what would be sent
# False = actually send emails
TEST_MODE = False

# Delay between emails in seconds
DELAY = 2


# ============================================================
# STUDENT DATA
# ============================================================

students = [
    {
        "student_id": "CS-2026-001",
        "name": "Ali Ahmed",
        "email": "ali@example.com",
        "password": "ChangeMe123!",
        "program": "BS Computer Science"
    },
    {
        "student_id": "CS-2026-002",
        "name": "Shahzaib Ali",
        "email": "FA24BSSE0036@maju.edu.pk",
        "password": "FA24-BSSE-0036",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-003",
        "name": "Hamza Shehzad",
        "email": "FA25BSSE0004@maju.edu.pk",
        "password": "FA25-BSSE-0004",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-004",
        "name": "LAIBA ABDUL RAZZAK ALI GOHAR",
        "email": "FA25BSSE0005@maju.edu.pk",
        "password": "FA25-BSSE-0005",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-005",
        "name": "RAO MADYAN",
        "email": "FA25BSSE0006@maju.edu.pk",
        "password": "FA25-BSSE-0006",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-006",
        "name": "MUHAMMAD RAAHIM",
        "email": "FA25BSSE0007@maju.edu.pk",
        "password": "FA25-BSSE-0007",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-007",
        "name": "MUHAMMAD ALYAAN KHAN",
        "email": "FA25BSSE0009@maju.edu.pk",
        "password": "FA25-BSSE-0009",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-008",
        "name": "LAIBA ADNAN",
        "email": "FA25BSSE0010@maju.edu.pk",
        "password": "FA25-BSSE-0010",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-009",
        "name": "ASMA RAZA",
        "email": "FA25BSSE0012@maju.edu.pk",
        "password": "FA25-BSSE-0012",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-010",
        "name": "ABDULLAH IRFAN",
        "email": "FA25BSSE0013@maju.edu.pk",
        "password": "FA25-BSSE-0013",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-011",
        "name": "AFIA MUHAMMAD SHAHID",
        "email": "FA25BSSE0014@maju.edu.pk",
        "password": "FA25-BSSE-0014",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-012",
        "name": "RUMAN AHMED",
        "email": "FA25BSSE0015@maju.edu.pk",
        "password": "FA25-BSSE-0015",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-013",
        "name": "AREESHA ASHRAF MUHAMMAD ASHRAF",
        "email": "FA25BSSE0018@maju.edu.pk",
        "password": "FA25-BSSE-0018",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-014",
        "name": "AMMAR JUNAID FARIDI",
        "email": "FA25BSSE0019@maju.edu.pk",
        "password": "FA25-BSSE-0019",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-015",
        "name": "MUHAMMAD MAAZ",
        "email": "FA25BSSE0020@maju.edu.pk",
        "password": "FA25-BSSE-0020",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-016",
        "name": "ALI MUSTAFA",
        "email": "FA25BSSE0023@maju.edu.pk",
        "password": "FA25-BSSE-0023",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-017",
        "name": "ALIZA ROSHAN",
        "email": "FA25BSSE0025@maju.edu.pk",
        "password": "FA25-BSSE-0025",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-018",
        "name": "BISMA ZEB",
        "email": "FA25BSSE0026@maju.edu.pk",
        "password": "FA25-BSSE-0026",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-019",
        "name": "ZULQARNAIN MUHAMMAD SHAKIR HAIDER",
        "email": "FA25BSSE0027@maju.edu.pk",
        "password": "FA25-BSSE-0027",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-020",
        "name": "MANAHIL IMRAN",
        "email": "FA25BSSE0029@maju.edu.pk",
        "password": "FA25-BSSE-0029",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-021",
        "name": "SARWAN ALI",
        "email": "FA25BSSE0030@maju.edu.pk",
        "password": "FA25-BSSE-0030",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-022",
        "name": "MISHRA MUHAMMAD AAMIR",
        "email": "FA25BSSE0032@maju.edu.pk",
        "password": "FA25-BSSE-0032",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-023",
        "name": "Muhammad Ahsan Ather",
        "email": "FA25BSSE0034@maju.edu.pk",
        "password": "FA25-BSSE-0034",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-024",
        "name": "WANIA ARSHAD",
        "email": "FA25BSSE0036@maju.edu.pk",
        "password": "FA25-BSSE-0036",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-025",
        "name": "GHULAM FATIMA",
        "email": "FA25BSSE0037@maju.edu.pk",
        "password": "FA25-BSSE-0037",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-026",
        "name": "MUSTAFA NOOR NOOR",
        "email": "FA25BSSE0042@maju.edu.pk",
        "password": "FA25-BSSE-0042",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-027",
        "name": "FARHAD KHURRAM",
        "email": "FA25BSSE0045@maju.edu.pk",
        "password": "FA25-BSSE-0045",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-028",
        "name": "MAIRA SABIR",
        "email": "FA25BSSE0046@maju.edu.pk",
        "password": "FA25-BSSE-0046",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-029",
        "name": "ASIA YOUSAF",
        "email": "FA25BSSE0048@maju.edu.pk",
        "password": "FA25-BSSE-0048",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-030",
        "name": "HALIMA SHAIKH SADIA",
        "email": "FA25BSSE0050@maju.edu.pk",
        "password": "FA25-BSSE-0050",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-031",
        "name": "EZHAN MUHAMMAD RAFIQ",
        "email": "FA25BSSE0079@maju.edu.pk",
        "password": "FA25-BSSE-0079",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-032",
        "name": "Umaima Saleem",
        "email": "FA25BSSE0083@maju.edu.pk",
        "password": "FA25-BSSE-0083",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-033",
        "name": "MUHAMMAD HUSSAIN MEHMOOD HUSSAIN",
        "email": "FA25BSSE0087@maju.edu.pk",
        "password": "FA25-BSSE-0087",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-034",
        "name": "NOOR KHAN",
        "email": "FA25BSSE0092@maju.edu.pk",
        "password": "FA25-BSSE-0092",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-035",
        "name": "YASIR KHAN",
        "email": "FA25BSSE0095@maju.edu.pk",
        "password": "FA25-BSSE-0095",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-036",
        "name": "AHMED RAZA",
        "email": "FA25BSSE0097@maju.edu.pk",
        "password": "FA25-BSSE-0097",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-037",
        "name": "Syed Muneeb Shahid",
        "email": "SP23BSSE0037@maju.edu.pk",
        "password": "SP23-BSSE-0037",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-038",
        "name": "Shahbaz Ali",
        "email": "SP24BSSE0078@maju.edu.pk",
        "password": "SP24-BSSE-0078",
        "program": "BS Software Engineering"
    },
    {
        "student_id": "CS-2026-039",
        "name": "Laiba Saleem",
        "email": "SP25BSSE0072@maju.edu.pk",
        "password": "SP25-BSSE-0072",
        "program": "BS Software Engineering"
    }
]


# ============================================================
# CREATE PERSONALIZED EMAIL
# ============================================================

def create_email(student):

    message = MIMEMultipart("alternative")

    message["From"] = SENDER_EMAIL
    message["To"] = student["email"]
    message["Subject"] = "Online Quiz - Your Login Credentials"

    plain_text = f"""
Dear {student["name"]},

You are required to attempt the online quiz using your
individual login credentials.

STUDENT INFORMATION
-------------------
Student ID : {student["student_id"]}
Name       : {student["name"]}
Program    : {student["program"]}

QUIZ LOGIN INFORMATION
----------------------
Quiz URL   : {QUIZ_URL}
Username   : {student["email"]}
Password   : {student["password"]}

Please do not share your login credentials with another student.

Regards,
Engr. Syed Zaid Irshad
"""

    html_text = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">

<style>

body {{
    font-family: Arial, Helvetica, sans-serif;
    background-color: #f4f6f8;
    padding: 30px;
}}

.container {{
    max-width: 650px;
    margin: auto;
    background-color: white;
    padding: 30px;
    border-radius: 10px;
}}

h2 {{
    color: #1f2937;
}}

h3 {{
    color: #374151;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 25px;
}}

td {{
    padding: 10px;
    border: 1px solid #d1d5db;
}}

.label {{
    font-weight: bold;
    background-color: #f3f4f6;
    width: 35%;
}}

.password {{
    font-weight: bold;
    font-size: 16px;
}}

.quiz {{
    background-color: #2563eb;
    color: white;
    padding: 12px 20px;
    text-decoration: none;
    border-radius: 6px;
}}

.warning {{
    background-color: #fff3cd;
    padding: 12px;
    border-radius: 6px;
}}

</style>
</head>

<body>

<div class="container">

<h2>Online Quiz - Login Credentials</h2>

<p>
Dear <strong>{student["name"]}</strong>,
</p>

<p>
You are required to attempt the online quiz using your
individual login credentials.
</p>

<h3>Student Information</h3>

<table>

<tr>
<td class="label">Student ID</td>
<td>{student["student_id"]}</td>
</tr>

<tr>
<td class="label">Name</td>
<td>{student["name"]}</td>
</tr>

<tr>
<td class="label">Program</td>
<td>{student["program"]}</td>
</tr>

</table>


<h3>Quiz Login Information</h3>

<table>

<tr>
<td class="label">Quiz URL</td>
<td>
<a class="quiz" href="{QUIZ_URL}">
Open Quiz
</a>
</td>
</tr>

<tr>
<td class="label">Username</td>
<td>{student["email"]}</td>
</tr>

<tr>
<td class="label">Password</td>
<td class="password">{student["password"]}</td>
</tr>

</table>


<div class="warning">

<strong>Important:</strong>
Please do not share your login credentials with another student.

</div>

<p>
Regards,<br>
<strong>Engr. Syed Zaid Irshad</strong>
</p>

</div>

</body>
</html>
"""

    message.attach(MIMEText(plain_text, "plain"))
    message.attach(MIMEText(html_text, "html"))

    return message


# ============================================================
# SEND EMAILS
# ============================================================

def send_emails():

    print("=" * 60)
    print("ONLINE QUIZ EMAIL DISTRIBUTION")
    print("=" * 60)

    print(f"Total students: {len(students)}")
    print(f"Quiz URL: {QUIZ_URL}")
    print(f"Test mode: {TEST_MODE}")
    print()

    # --------------------------------------------------------
    # TEST MODE
    # --------------------------------------------------------

    if TEST_MODE:

        print("TEST MODE ENABLED")
        print("No emails will actually be sent.")
        print()

        for student in students:

            print(
                f"[TEST] {student['student_id']} | "
                f"{student['name']} | "
                f"{student['email']}"
            )

        print()
        print("Set TEST_MODE = False when you are ready to send.")
        return

    # --------------------------------------------------------
    # CONNECT TO OUTLOOK
    # --------------------------------------------------------

    print("Connecting to Outlook/Microsoft 365...")

    try:

        server = smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT
        )

        server.ehlo()

        server.starttls()

        server.ehlo()

        server.login(
            SENDER_EMAIL,
            SENDER_PASSWORD
        )

        print("Successfully authenticated.")
        print()

    except Exception as error:

        print()
        print("ERROR: Could not connect/login to Outlook.")
        print(error)

        return

    # --------------------------------------------------------
    # LOG FILE
    # --------------------------------------------------------

    with open(
        "email_sending_log.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as logfile:

        writer = csv.writer(logfile)

        writer.writerow([
            "Student ID",
            "Name",
            "Email",
            "Status",
            "Error"
        ])

        # ----------------------------------------------------
        # SEND EACH STUDENT'S EMAIL
        # ----------------------------------------------------

        for number, student in enumerate(students, start=1):

            print(
                f"[{number}/{len(students)}] "
                f"Sending to {student['name']} "
                f"({student['email']})..."
            )

            try:

                message = create_email(student)

                server.sendmail(
                    SENDER_EMAIL,
                    student["email"],
                    message.as_string()
                )

                print("    SUCCESS")

                writer.writerow([
                    student["student_id"],
                    student["name"],
                    student["email"],
                    "SENT",
                    ""
                ])

            except Exception as error:

                print("    FAILED")
                print(f"    {error}")

                writer.writerow([
                    student["student_id"],
                    student["name"],
                    student["email"],
                    "FAILED",
                    str(error)
                ])

            time.sleep(DELAY)

    # --------------------------------------------------------
    # CLOSE CONNECTION
    # --------------------------------------------------------

    server.quit()

    print()
    print("=" * 60)
    print("EMAIL DISTRIBUTION COMPLETED")
    print("Log saved as: email_sending_log.csv")
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    send_emails()