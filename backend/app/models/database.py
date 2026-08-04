from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import get_settings

_settings = get_settings()

DATABASE_URL = _settings.DATABASE_URL

# Project-wide rule: ONLY MySQL / PostgreSQL are allowed at runtime.
# Any sqlite:// URL (even if accidentally left in an .env) will be rejected
# at bootstrap by run.py before we ever reach this module, so there is no
# check_same_thread / file-lock special-case to carry here.
engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()