"""SQLAlchemy engine and session factory."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import get_settings

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.database_url, echo=settings.echo_sql, pool_pre_ping=True)
    return _engine


def get_session_factory() -> sessionmaker:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _session_factory


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Transactional scope for repository operations."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine() -> None:
    """Reset engine (tests)."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
