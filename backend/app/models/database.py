from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import get_settings

_settings = get_settings()

DATABASE_URL = _settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={} if DATABASE_URL.startswith("mysql") else {"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()