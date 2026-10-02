"""Data-quality check helper. A "check" is just a SQL query that counts rows
matching some condition we consider suspicious; the count gets written to
staging._dq_log instead of silently disappearing, so a problem that doubles
overnight is visible in the log, not just in a changed downstream number.

This is deliberately hand-rolled rather than a framework (e.g. Great
Expectations) per the charter's tech-stack decision: start simple, upgrade
only if this gets unwieldy.
"""
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.engine import Connection


@dataclass
class DQCheck:
    name: str
    table_name: str
    sql: str  # must be a single SELECT returning one integer count


def run_check(conn: Connection, check: DQCheck) -> int:
    count = conn.execute(text(check.sql)).scalar()
    conn.execute(
        text(
            """
            INSERT INTO staging._dq_log (check_name, table_name, row_count)
            VALUES (:check_name, :table_name, :row_count)
            """
        ),
        {"check_name": check.name, "table_name": check.table_name, "row_count": count},
    )
    flag = "OK" if count == 0 else "FLAGGED"
    print(f"  [{flag}] {check.name}: {count:,} rows")
    return count


def ensure_dq_log_table(conn: Connection) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS staging._dq_log (
                id serial PRIMARY KEY,
                check_name text,
                table_name text,
                row_count bigint,
                run_at timestamp DEFAULT now()
            )
            """
        )
    )
