# pyright: reportMissingImports=false
"""Database helpers for connecting to PostgreSQL."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import psycopg
from psycopg.rows import dict_row


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/patient_summary",
)


def _ensure_database_url() -> str:
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    return DATABASE_URL


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    """Yield a psycopg3 connection."""
    conn = psycopg.connect(
        _ensure_database_url(), autocommit=True, row_factory=dict_row
    )
    try:
        yield conn
    finally:
        conn.close()


def init_db(schema_path: Path | None = None) -> None:
    """Create required tables by executing the schema.sql file."""

    default_schema = Path(__file__).with_name("schema.sql")
    sql_path = schema_path or default_schema
    schema_sql = sql_path.read_text(encoding="utf-8")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)

