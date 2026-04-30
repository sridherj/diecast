"""baseline: initial schema from schema.sql

Revision ID: cfe1a46fdefc
Revises:
Create Date: 2026-04-30

Hand-authored baseline (Decision #14). The cast-server codebase has no
SQLAlchemy ORM models, so autogenerate is not used. This migration reads
``cast_server/db/schema.sql`` verbatim and executes each statement.

Naive ``split(";")`` is correct here only because schema.sql contains no
string literals with embedded semicolons. If a future schema change adds
such a literal, switch to ``op.get_bind().exec_driver_sql(raw)``.
"""
from pathlib import Path

from alembic import op


revision = "cfe1a46fdefc"
down_revision = None
branch_labels = None
depends_on = None


def _schema_sql_path() -> Path:
    return (
        Path(__file__).resolve().parent.parent.parent
        / "cast_server"
        / "db"
        / "schema.sql"
    )


def upgrade() -> None:
    raw = _schema_sql_path().read_text()
    for stmt in raw.split(";"):
        stmt = stmt.strip()
        if stmt:
            op.execute(stmt)


def downgrade() -> None:
    raise NotImplementedError(
        "baseline cannot be downgraded; rm ~/.cast/diecast.db to reset"
    )
