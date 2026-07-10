"""SQLAlchemy database setup."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "resellpro.db"

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_columns() -> None:
    """Add new columns to existing SQLite DBs without Alembic."""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if "app_settings" not in insp.get_table_names():
        return
    existing = {c["name"] for c in insp.get_columns("app_settings")}
    with engine.begin() as conn:
        if "vinted_proxy_encrypted" not in existing:
            conn.execute(text("ALTER TABLE app_settings ADD COLUMN vinted_proxy_encrypted TEXT DEFAULT ''"))
        if "default_scan_minutes" not in existing:
            conn.execute(text("ALTER TABLE app_settings ADD COLUMN default_scan_minutes INTEGER DEFAULT 15"))


def init_db():
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_columns()
