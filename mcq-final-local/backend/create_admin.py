import os
from sqlalchemy import select
from app.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password

email = os.getenv("ADMIN_EMAIL", "admin@localhost.local")
password = os.getenv("ADMIN_PASSWORD", "Admin@12345")
name = os.getenv("ADMIN_NAME", "System Administrator")

db = SessionLocal()
try:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(full_name=name, email=email, password_hash=hash_password(password), role="admin", is_active=True)
        db.add(user)
    else:
        user.full_name = name
        user.password_hash = hash_password(password)
        user.role = "admin"
        user.is_active = True
    db.commit()
    print(f"Admin ready: {email}")
finally:
    db.close()
