from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Cấu hình database: ưu tiên SQLite cho development
database_url = os.getenv("DATABASE_URL")

# Chỉ sử dụng external database nếu được cấu hình rõ ràng và không phải PostgreSQL default của Replit
if database_url and not database_url.startswith("postgresql://postgres:password@helium"):
    if database_url.startswith("sqlite"):
        SQLALCHEMY_DATABASE_URL = database_url
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
        )
    else:
        # MySQL hoặc PostgreSQL khác
        SQLALCHEMY_DATABASE_URL = database_url
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
else:
    # Mặc định SQLite cho development
    SQLALCHEMY_DATABASE_URL = "sqlite:///./school_payment.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency để lấy database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()