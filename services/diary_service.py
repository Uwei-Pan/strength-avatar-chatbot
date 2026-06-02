import json
import hashlib
import re
from typing import Any

from database.db_connection import execute, fetch_all, fetch_one
from services.ai_service import analyze_diary_entry
from services.strength_service import save_child_strength
from services.token_service import award_diary_tokens


DIARY_GEMINI_MIN_CHINESE_CHARS = 10
DIARY_GEMINI_MAX_INPUT_CHARS = 500
DIARY_CACHE_MODE = "cached"


def create_diary_entry(child_profile: dict[str, Any], content: str) -> dict[str, Any]:
    child_id = child_profile["child_id"]
    cleaned = content.strip()
    result = _load_cached_diary_analysis(child_id, cleaned)
    if result is None:
        result = analyze_diary_entry(child_profile, cleaned)
        _save_diary_analysis_cache(child_id, cleaned, result)

    tokens_earned, token_messages = _calculate_diary_tokens(
        cleaned,
        has_confirmed_strength=bool(result["detected_strengths"]),
    )
    if tokens_earned:
        award_diary_tokens(child_id, tokens_earned)

    execute(
        """
        INSERT INTO diary_entries
            (child_id, content, ai_reply, detected_strengths_json, tokens_earned)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            child_id,
            cleaned,
            result["reply_to_child"],
            json.dumps(result["detected_strengths"], ensure_ascii=False),
            tokens_earned,
        ),
    )

    for strength in result["detected_strengths"]:
        save_child_strength(
            child_id=child_id,
            strength_name=strength["strength_name"],
            source="diary",
            evidence_text=strength.get("evidence_text") or cleaned,
            confidence=float(strength.get("confidence") or 0.7),
        )

    return {**result, "tokens_earned": tokens_earned, "token_messages": token_messages}


def list_diary_entries(child_id: str) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, content, ai_reply, detected_strengths_json,
               tokens_earned, created_at
        FROM diary_entries
        WHERE child_id = %s
        ORDER BY created_at DESC, id DESC
        LIMIT 20
        """,
        (child_id,),
    )


def delete_diary_entry(child_id: str, entry_id: int) -> None:
    entry = fetch_one(
        """
        SELECT id
        FROM diary_entries
        WHERE id = %s AND child_id = %s
        LIMIT 1
        """,
        (entry_id, child_id),
    )
    if not entry:
        raise ValueError("找不到這篇日記。")

    execute(
        """
        DELETE FROM diary_entries
        WHERE id = %s AND child_id = %s
        """,
        (entry_id, child_id),
    )


def _calculate_diary_tokens(content: str, *, has_confirmed_strength: bool) -> tuple[int, list[str]]:
    cleaned = content.strip()
    if not cleaned:
        return 0, ["日記已儲存，謝謝你願意記錄今天。"]

    chinese_count = _count_chinese_chars(cleaned)
    if chinese_count < 8:
        tokens = 2
        messages = ["日記已儲存，獲得 +2 代幣。"]
    elif chinese_count <= 30:
        tokens = 5
        messages = ["日記已儲存，獲得 +5 代幣。"]
    else:
        tokens = 10
        messages = ["日記已儲存，獲得 +10 代幣。"]

    if has_confirmed_strength:
        tokens += 5
        messages.append("小幫手看見一個清楚的亮點，額外獲得 +5 代幣。")
    return tokens, messages


def _load_cached_diary_analysis(child_id: str, content: str) -> dict[str, Any] | None:
    if not _should_call_gemini(content):
        return None
    _ensure_diary_analysis_cache_table()
    row = fetch_one(
        """
        SELECT analysis_json, ai_reply, detected_strengths_json, model
        FROM diary_analysis_cache
        WHERE child_id = %s AND content_hash = %s
        LIMIT 1
        """,
        (child_id, _analysis_hash(content)),
    )
    if not row:
        return None
    result = _parse_analysis_json(row.get("analysis_json"))
    strengths = _parse_json_list(row.get("detected_strengths_json"))
    return {
        "reply_to_child": row.get("ai_reply") or result.get("reply_to_child") or "日記已儲存，謝謝你願意記錄今天。",
        "emotion": result.get("emotion", "平穩"),
        "detected_strengths": strengths,
        "should_award_tokens": True,
        "tokens_earned": 0,
        "follow_up_question": "",
        "mode": DIARY_CACHE_MODE,
        "error": result.get("error", ""),
        "model": row.get("model") or result.get("model", ""),
        "diary_analysis": result.get("diary_analysis", {}),
    }


def _save_diary_analysis_cache(child_id: str, content: str, result: dict[str, Any]) -> None:
    if not _should_call_gemini(content):
        return
    _ensure_diary_analysis_cache_table()
    execute(
        """
        INSERT INTO diary_analysis_cache
            (child_id, content_hash, content_preview, analysis_json, ai_reply, detected_strengths_json, model)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            analysis_json = VALUES(analysis_json),
            ai_reply = VALUES(ai_reply),
            detected_strengths_json = VALUES(detected_strengths_json),
            model = VALUES(model)
        """,
        (
            child_id,
            _analysis_hash(content),
            _analysis_text(content),
            json.dumps(result, ensure_ascii=False),
            result.get("reply_to_child", ""),
            json.dumps(result.get("detected_strengths", []), ensure_ascii=False),
            result.get("model", ""),
        ),
    )


def _ensure_diary_analysis_cache_table() -> None:
    execute(
        """
        CREATE TABLE IF NOT EXISTS diary_analysis_cache (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            child_id VARCHAR(64) NOT NULL,
            content_hash CHAR(64) NOT NULL,
            content_preview TEXT NOT NULL,
            analysis_json JSON NULL,
            ai_reply TEXT NULL,
            detected_strengths_json JSON NULL,
            model VARCHAR(100) NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_diary_analysis_cache_child_hash (child_id, content_hash),
            INDEX idx_diary_analysis_cache_child_created (child_id, created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


def _should_call_gemini(content: str) -> bool:
    return _count_chinese_chars(content.strip()) >= DIARY_GEMINI_MIN_CHINESE_CHARS


def _analysis_text(content: str) -> str:
    return content.strip()[:DIARY_GEMINI_MAX_INPUT_CHARS]


def _analysis_hash(content: str) -> str:
    return hashlib.sha256(_analysis_text(content).encode("utf-8")).hexdigest()


def _count_chinese_chars(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def _parse_analysis_json(raw_value: Any) -> dict[str, Any]:
    if isinstance(raw_value, dict):
        return raw_value
    if not raw_value:
        return {}
    try:
        value = json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _parse_json_list(raw_value: Any) -> list[dict[str, Any]]:
    if isinstance(raw_value, list):
        return [item for item in raw_value if isinstance(item, dict)]
    if not raw_value:
        return []
    try:
        value = json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        return []
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []
