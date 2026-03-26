import os
from sqlalchemy import create_engine, Column, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost:5432/poc3_db")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    verification_id = Column(String, primary_key=True, index=True)
    candidate_id = Column(String, index=True, nullable=False)
    status = Column(String, nullable=False)           # VERIFIED | FAILED
    confidence_score = Column(Float, nullable=True)
    document_type = Column(String, nullable=True)
    extracted_name = Column(String, nullable=True)
    extracted_dob = Column(String, nullable=True)
    claimed_name = Column(String, nullable=True)
    claimed_dob = Column(String, nullable=True)
    name_match_score = Column(Float, nullable=True)
    dob_matched = Column(Boolean, nullable=True)
    tamper_detected = Column(Boolean, nullable=True)
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def get_db():
    """Dependency: yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
