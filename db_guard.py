"""
Safety layer around the database the agent can see.

The agent is free to write its own SQL, but every query passes through
`validate_query` first. Anything that isn't a read-only SELECT (or a
WITH ... SELECT CTE) is rejected before it ever reaches the database --
and a row cap is added automatically so one bad query can't dump the
whole table into the LLM's context.

This is a reasonable safety net for a demo/portfolio project. If you
point this at a real production database, also connect with a
database-level read-only user -- don't rely on this check alone.
"""

import re
from typing import Optional

from langchain_community.utilities import SQLDatabase

BANNED_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE",
    "ATTACH", "DETACH", "PRAGMA", "REPLACE", "GRANT", "REVOKE",
    "CREATE", "VACUUM",
]

MAX_ROWS = 25
# Free-tier Groq accounts get a tight 8,000-tokens/minute budget. An
# ungoverned query that returns hundreds of raw rows can burn through
# most of that in one shot, so this cap is deliberately conservative --
# raise it if you move to a paid tier or a model with more headroom.


def validate_query(query: str) -> Optional[str]:
    """Returns an error string if the query is unsafe, otherwise None."""
    stripped = query.strip().rstrip(";").strip()

    if not stripped:
        return "Rejected: empty query."

    first_word = stripped.split(None, 1)[0].upper()
    if first_word not in ("SELECT", "WITH"):
        return (
            f"Rejected: only read-only SELECT (or WITH ... SELECT) statements "
            f"are allowed. Got a statement starting with '{first_word}'."
        )

    upper_query = stripped.upper()
    for keyword in BANNED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper_query):
            return f"Rejected: query contains a disallowed keyword '{keyword}'."

    return None


def enforce_row_limit(query: str, max_rows: int = MAX_ROWS) -> str:
    """Appends a LIMIT clause if the query doesn't already have one."""
    stripped = query.strip().rstrip(";")
    if re.search(r"\bLIMIT\b", stripped.upper()):
        return stripped
    return f"{stripped} LIMIT {max_rows}"


class GuardedSQLDatabase(SQLDatabase):
    """A SQLDatabase that validates and caps every query before running it."""

    def run(self, command: str, *args, **kwargs):
        error = validate_query(command)
        if error:
            # Raising here lets the query-checker tool surface the problem
            # back to the agent so it can try a different, safe query.
            raise ValueError(error)
        command = enforce_row_limit(command)
        return super().run(command, *args, **kwargs)

    def run_no_throw(self, command: str, *args, **kwargs):
        error = validate_query(command)
        if error:
            return error
        command = enforce_row_limit(command)
        return super().run_no_throw(command, *args, **kwargs)