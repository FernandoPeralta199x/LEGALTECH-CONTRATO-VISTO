"""Database session setup with a startup connectivity check.

In local development the backend fails fast when PostgreSQL is not reachable,
instead of hanging indefinitely on the first authenticated request.
"""

import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
    connect_args={"connect_timeout": 5},
)

# Fast fail for local development: waiting until the first request to discover
# that PostgreSQL is down leads to confusing timeouts in the browser/proxy.
if settings.app_env == "local":
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
    except OperationalError as exc:
        logger.error(
            "PostgreSQL is not reachable at %s. "
            "Start the database before running the backend locally. "
            "See docs/MVP_LOCAL_RUNBOOK.md section 3.",
            settings.database_url,
        )
        raise RuntimeError(
            "PostgreSQL is not reachable. "
            "Run 'docker compose up -d postgres' (or start your local DB) "
            "before starting the backend."
        ) from exc

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
