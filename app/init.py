"""
App initializer: create default admin if missing.
"""
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, UserRole
from app.core.security import get_password_hash


def ensure_default_admin():
    db: Session = SessionLocal()
    try:
        admin_email = "admin@example.com"
        existing = db.query(User).filter(User.email == admin_email).first()
        if existing is None:
            admin = User(
                name="System Admin",
                email=admin_email,
                phone="",
                role=UserRole.ADMIN,
                hashed_password=get_password_hash("Admin@123")
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


