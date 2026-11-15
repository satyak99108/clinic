"""
Database connection — engine, session factory, and Base.

The SQLite file is stored in:
    %APPDATA%/BDMedicalCenter/clinic.db

Tables are created automatically on first launch via init_db().
No database knowledge is required from application users.
"""

import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


# ---------------------------------------------------------------------------
def get_db_path() -> Path:
    """Return the SQLite file path, creating parent directories if needed."""
    app_data = Path(os.environ.get("APPDATA", Path.home())) / "BDMedicalCenter"
    app_data.mkdir(parents=True, exist_ok=True)
    return app_data / "clinic.db"


# ---------------------------------------------------------------------------
_engine = None
_SessionLocal = None


def get_engine():
    """Return (and lazily create) the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        db_path = get_db_path()
        _engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            echo=False,
        )

        # Enable WAL mode and foreign keys on every new connection
        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, _record):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

    return _engine


def _get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(), autoflush=False, autocommit=False
        )
    return _SessionLocal


@contextmanager
def get_session():
    """Context manager that yields a session and handles commit/rollback."""
    Session = _get_session_factory()
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Create all tables that do not yet exist. Safe to call on every startup."""
    # Import models so SQLAlchemy registers them before create_all
    import clinic_app.models.patient  # noqa: F401
    import clinic_app.models.consultation  # noqa: F401
    import clinic_app.models.prescription  # noqa: F401
    import clinic_app.models.medicine  # noqa: F401

    Base.metadata.create_all(get_engine())

    # Pre-populate common medicine catalog if empty
    from clinic_app.services.prescription_service import seed_initial_catalog
    seed_initial_catalog()
