import os
from getpass import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models.user import User

email = os.getenv("ADMIN_EMAIL", "admin@localhost.local")
name = os.getenv("ADMIN_NAME", "System Administrator")

db = SessionLocal()
try:
    user = db.scalar(select(User).where(User.email == email))
    if user is not None:
        if user.role != "admin":
            raise RuntimeError(
                f"Cannot provision {email}: an account with that email already "
                f"exists with role {user.role!r}."
            )
        print(f"Existing administrator preserved: {email}")
    else:
        from app.core.security import hash_password

        password = os.getenv("ADMIN_PASSWORD") or getpass(
            f"Create administrator password for {email}: "
        )
        if len(password) < 12:
            raise ValueError("Administrator passwords must be at least 12 characters.")

        user = User(
            full_name=name,
            email=email,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"Administrator created: {email}")
finally:
    db.close()
