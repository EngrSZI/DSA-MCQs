from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from openpyxl import Workbook, load_workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

try:
    from app.core.security import hash_password
    from app.database import get_db
    from app.dependencies import require_admin
    from app.models.user import User
except ModuleNotFoundError:
    from backend.app.core.security import hash_password
    from backend.app.database import get_db
    from backend.app.dependencies import require_admin
    from backend.app.models.user import User

router = APIRouter(prefix="/admin/students", tags=["Admin Students"])


def _text(value):
    return "" if value is None else str(value).strip()


@router.get("")
def list_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    students = db.scalars(select(User).where(User.role == "student").order_by(User.id)).all()
    return [
        {
            "id": s.id,
            "student_id": s.student_id or "",
            "full_name": s.full_name,
            "email": s.email,
            "program": s.program or "",
            "is_active": s.is_active,
            "created_at": s.created_at,
        }
        for s in students
    ]


@router.get("/template.xlsx")
def student_template(current_user: User = Depends(require_admin)):
    wb = Workbook()
    ws = wb.active
    ws.title = "Students"
    ws.append(["Student ID", "Full Name", "Email", "Password", "Program"])
    ws.append(["CS-2026-001", "Ali Ahmed", "ali@example.com", "ChangeMe123!", "BS Computer Science"])
    data = BytesIO()
    wb.save(data)
    data.seek(0)
    return StreamingResponse(
        data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="students_template.xlsx"'},
    )


@router.post("/import")
def import_students(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Please upload an Excel .xlsx file.")

    content = file.file.read()
    try:
        wb = load_workbook(BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to read Excel file: {exc}")

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise HTTPException(status_code=400, detail="The Excel file is empty.")

    headers = [_text(v).lower() for v in rows[0]]
    aliases = {
        "student id": "student_id", "student_id": "student_id", "id": "student_id",
        "full name": "full_name", "full_name": "full_name", "name": "full_name",
        "email": "email", "password": "password", "program": "program",
    }
    mapped = [aliases.get(h) for h in headers]
    required = {"student_id", "full_name", "email", "password"}
    if not required.issubset(set(mapped)):
        raise HTTPException(
            status_code=400,
            detail="Excel must contain: Student ID, Full Name, Email, Password. Program is optional.",
        )

    created, updated, failed = [], [], []
    for row_number, values in enumerate(rows[1:], start=2):
        record = {mapped[i]: _text(values[i]) for i in range(min(len(values), len(mapped))) if mapped[i]}
        student_id = record.get("student_id", "")
        name = record.get("full_name", "")
        email = record.get("email", "").lower()
        password = record.get("password", "")
        program = record.get("program", "")
        if not student_id or not name or not email or not password:
            failed.append({"row": row_number, "error": "Student ID, Full Name, Email and Password are required."})
            continue
        if len(password) < 8:
            failed.append({"row": row_number, "student_id": student_id, "error": "Password must be at least 8 characters."})
            continue
        try:
            existing = db.scalar(select(User).where(User.student_id == student_id))
            email_user = db.scalar(select(User).where(User.email == email))
            if existing and email_user and existing.id != email_user.id:
                raise ValueError("Student ID and email belong to different users.")
            user = existing or email_user
            if user:
                if user.role != "student":
                    raise ValueError("An administrator/teacher already uses this email or ID.")
                user.full_name = name
                user.email = email
                user.student_id = student_id
                user.program = program
                user.password_hash = hash_password(password)
                user.is_active = True
                updated.append(student_id)
            else:
                user = User(
                    student_id=student_id,
                    full_name=name,
                    email=email,
                    program=program,
                    password_hash=hash_password(password),
                    role="student",
                    is_active=True,
                )
                db.add(user)
                created.append(student_id)
        except Exception as exc:
            failed.append({"row": row_number, "student_id": student_id, "error": str(exc)})
    db.commit()
    return {"created": len(created), "updated": len(updated), "failed": len(failed), "created_ids": created, "updated_ids": updated, "errors": failed}
