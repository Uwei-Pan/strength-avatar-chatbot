import json
from datetime import datetime
from pathlib import Path
from typing import Any


SESSION_DIR = Path(__file__).resolve().parents[1] / "data" / "chat_sessions"


def save_chat_session(session: dict[str, Any]) -> Path:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    child_id = _safe_id(str(session["student_id"]))
    session_id = _safe_id(str(session["session_id"]))
    path = SESSION_DIR / f"{child_id}_{session_id}.json"
    path.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def list_chat_sessions(student_id: str, limit: int = 10) -> list[dict[str, Any]]:
    if not SESSION_DIR.exists():
        return []

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


def _safe_id(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)


def _sort_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min
