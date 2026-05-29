import json
from datetime import datetime
from pathlib import Path
from typing import Any

from database.db_connection import execute, fetch_all

SESSION_DIR = Path(__file__).resolve().parents[1] / "data" / "chat_sessions"


def save_chat_session(session: dict[str, Any]) -> None:
    _ensure_chat_sessions_table()
    execute(
        """
        INSERT INTO chat_sessions
            (session_id, child_id, created_at, closed_at, messages_json, token_events_json)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            closed_at = VALUES(closed_at),
            messages_json = VALUES(messages_json),
            token_events_json = VALUES(token_events_json),
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            str(session["session_id"]),
            str(session["student_id"]),
            _mysql_datetime(session.get("created_at")),
            _mysql_datetime(session.get("closed_at")),
            json.dumps(session.get("messages", []), ensure_ascii=False),
            json.dumps(session.get("token_events", []), ensure_ascii=False),
        ),
    )


def list_chat_sessions(student_id: str, limit: int = 10) -> list[dict[str, Any]]:
    _ensure_chat_sessions_table()
    rows = fetch_all(
        """
        SELECT session_id, child_id, created_at, closed_at, messages_json, token_events_json
        FROM chat_sessions
        WHERE child_id = %s
        ORDER BY COALESCE(closed_at, created_at) DESC
        LIMIT %s
        """,
        (student_id, int(limit)),
    )
    sessions = [_row_to_session(row) for row in rows]
    if sessions or not SESSION_DIR.exists():
        return sessions

    # One-time compatibility for old local JSON sessions that may exist in a dev checkout.
    sessions: list[dict[str, Any]] = []
    prefix = f"{_safe_id(student_id)}_"
    for path in SESSION_DIR.glob(f"{prefix}*.json"):
        try:
            sessions.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue

    sessions.sort(
        key=lambda item: _sort_datetime(item.get("closed_at") or item.get("created_at")),
        reverse=True,
    )
    return sessions[:limit]


def _ensure_chat_sessions_table() -> None:
    execute(
        """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id VARCHAR(64) PRIMARY KEY,
            child_id VARCHAR(64) NOT NULL,
            created_at TIMESTAMP NULL,
            closed_at TIMESTAMP NULL,
            messages_json JSON NULL,
            token_events_json JSON NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT fk_chat_sessions_child
                FOREIGN KEY (child_id) REFERENCES children(child_id)
                ON DELETE CASCADE,
            INDEX idx_chat_sessions_child_closed (child_id, closed_at, created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


def _row_to_session(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": str(row["session_id"]),
        "student_id": str(row["child_id"]),
        "created_at": _iso_datetime(row.get("created_at")),
        "closed_at": _iso_datetime(row.get("closed_at")),
        "messages": _parse_json_list(row.get("messages_json")),
        "token_events": _parse_json_list(row.get("token_events_json")),
    }


def _parse_json_list(raw_value: Any) -> list[dict[str, Any]]:
    if isinstance(raw_value, list):
        return raw_value
    if not raw_value:
        return []
    try:
        parsed = json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _mysql_datetime(value: Any) -> str | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    text = str(value).replace("T", " ")
    return text[:19]


def _iso_datetime(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    return str(value).replace(" ", "T", 1)


def _safe_id(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)


def _sort_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min
