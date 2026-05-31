import math
import os
import re
from datetime import datetime, timedelta
from typing import Any

from database.db_connection import execute, fetch_one, get_connection

# 設定小幫手每日可用量上限；可用 CHAT_AI_DAILY_TOKEN_LIMIT 覆蓋。
DEFAULT_CHAT_AI_DAILY_TOKEN_LIMIT = 12000


def get_chat_ai_daily_token_limit() -> int:
    raw_value = os.getenv("CHAT_AI_DAILY_TOKEN_LIMIT", "").strip()
    if not raw_value:
        raw_value = _get_streamlit_secret("CHAT_AI_DAILY_TOKEN_LIMIT")
    try:
        limit = int(raw_value or DEFAULT_CHAT_AI_DAILY_TOKEN_LIMIT)
    except ValueError:
        limit = DEFAULT_CHAT_AI_DAILY_TOKEN_LIMIT
    return max(1, limit)


def estimate_text_tokens(text: str) -> int:
    cleaned = str(text or "")
    if not cleaned:
        return 0
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", cleaned))
    non_chinese_chars = max(0, len(cleaned) - chinese_chars)
    return max(1, math.ceil(chinese_chars * 1.1 + non_chinese_chars / 4))


def get_chat_ai_usage(child_id: str) -> dict[str, Any]:
    _ensure_chat_ai_usage_table()
    usage = _fetch_usage(child_id)
    if not usage or _is_expired(usage.get("reset_at")):
        return _reset_usage(child_id)
    usage["limit_tokens"] = get_chat_ai_daily_token_limit()
    return usage


def can_use_chat_ai(child_id: str, estimated_next_tokens: int = 0) -> tuple[bool, dict[str, Any]]:
    usage = get_chat_ai_usage(child_id)
    limit = int(usage["limit_tokens"])
    used = int(usage["used_tokens"] or 0)
    return used + max(0, estimated_next_tokens) <= limit, usage


def record_chat_ai_usage(child_id: str, tokens_used: int) -> dict[str, Any]:
    if tokens_used <= 0:
        return get_chat_ai_usage(child_id)
    usage = get_chat_ai_usage(child_id)
    new_total = int(usage["used_tokens"] or 0) + int(tokens_used)
    execute(
        """
        UPDATE chat_ai_usage_limits
        SET used_tokens = %s, updated_at = CURRENT_TIMESTAMP
        WHERE child_id = %s
        """,
        (new_total, child_id),
    )
    return get_chat_ai_usage(child_id)


def chat_limit_reply(child_name: str) -> str:
    name = str(child_name or "孩子").strip() or "孩子"
    return f"小幫手該回去休息了～也祝{name}有美好的一天！"


def _get_streamlit_secret(name: str) -> str:
    try:
        import streamlit as st

        return str(st.secrets.get(name, "")).strip().strip('"').strip("'")
    except Exception:
        return ""


def _ensure_chat_ai_usage_table() -> None:
    execute(
        """
        CREATE TABLE IF NOT EXISTS chat_ai_usage_limits (
            child_id VARCHAR(64) PRIMARY KEY,
            used_tokens INT NOT NULL DEFAULT 0,
            reset_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


def _fetch_usage(child_id: str) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT child_id, used_tokens, reset_at
        FROM chat_ai_usage_limits
        WHERE child_id = %s
        """,
        (child_id,),
    )


def _reset_usage(child_id: str) -> dict[str, Any]:
    reset_at = datetime.now() + timedelta(hours=24)
    with get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO chat_ai_usage_limits (child_id, used_tokens, reset_at)
                    VALUES (%s, 0, %s)
                    ON DUPLICATE KEY UPDATE
                        used_tokens = 0,
                        reset_at = VALUES(reset_at)
                    """,
                    (child_id, reset_at),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return {
        "child_id": child_id,
        "used_tokens": 0,
        "reset_at": reset_at,
        "limit_tokens": get_chat_ai_daily_token_limit(),
    }


def _is_expired(reset_at: Any) -> bool:
    if not reset_at:
        return True
    if isinstance(reset_at, datetime):
        return datetime.now() >= reset_at
    try:
        parsed = datetime.fromisoformat(str(reset_at))
    except ValueError:
        return True
    return datetime.now() >= parsed
