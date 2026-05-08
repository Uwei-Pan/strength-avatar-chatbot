import json
from typing import Any

from database.db_connection import execute, fetch_all
from services.ai_service import analyze_child_message
from services.strength_service import save_child_strength
from services.token_service import award_diary_tokens


def create_diary_entry(child_profile: dict[str, Any], content: str) -> dict[str, Any]:
    child_id = child_profile["child_id"]
    result = analyze_child_message(child_profile, content)
    tokens_earned = 0
    if result["should_award_tokens"]:
        award_diary_tokens(child_id)
        tokens_earned = result["tokens_earned"]

    execute(
        """
        INSERT INTO diary_entries
            (child_id, content, ai_reply, detected_strengths_json, tokens_earned)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            child_id,
            content,
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
            evidence_text=strength.get("evidence_text") or content,
            confidence=float(strength.get("confidence") or 0.7),
        )

    return {**result, "tokens_earned": tokens_earned}


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
