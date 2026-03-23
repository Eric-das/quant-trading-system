from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from db.engine import get_engine


def check_database_health() -> tuple[bool, str]:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "Database connection is healthy."
    except SQLAlchemyError as exc:
        return False, f"Database health check failed: {exc}"
