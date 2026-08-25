from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    # lightweight column migrations for pre-existing databases
    with engine.begin() as conn:
        for stmt in (
            "ALTER TABLE job ADD COLUMN salary_min INTEGER",
            "ALTER TABLE job ADD COLUMN salary_max INTEGER",
            "ALTER TABLE company ADD COLUMN priority BOOLEAN DEFAULT 0",
            "UPDATE company SET priority = 1 WHERE source = 'salesforce'",
            "ALTER TABLE job ADD COLUMN salary_currency TEXT",
        ):
            try:
                conn.execute(text(stmt))
            except Exception:
                pass
