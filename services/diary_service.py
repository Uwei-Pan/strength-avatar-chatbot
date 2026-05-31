import json
import re
from typing import Any

from database.db_connection import execute, fetch_all
from services.ai_service import analyze_diary_entry
from services.strength_service import save_child_strength
from services.token_service import award_diary_tokens


def create_diary_entry(child_profile: dict[str, Any], content: str) -> dict[str, Any]:
    child_id = child_profile["child_id"]
    result = analyze_diary_entry(child_profile, content)
    if not _has_meaningful_content(re.sub(r"\s+", "", content.strip())):
        result["detected_strengths"] = []
    tokens_earned, token_messages = _calculate_diary_tokens(
        content,
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


def _calculate_diary_tokens(content: str, *, has_confirmed_strength: bool) -> tuple[int, list[str]]:
    cleaned = content.strip()
    compact = re.sub(r"\s+", "", cleaned)
    if not _has_meaningful_content(compact):
        return 0, ["日記已儲存，謝謝你願意記錄今天。"]

    tokens = 10
    messages = ["日記已儲存，獲得 +10 代幣。"]
    if len(compact) >= 30:
        tokens += 5
        messages.append("謝謝你分享得這麼完整，額外獲得 +5 代幣。")
    if has_confirmed_strength:
        tokens += 5
        messages.append("小幫手看見一個清楚的亮點，額外獲得 +5 代幣。")
    return tokens, messages


def _has_meaningful_content(compact_text: str) -> bool:
    if len(compact_text) < 6:
        return False
    low_signal = {"不知道", "還好", "沒事", "無聊", "普通", "今天很累"}
    if compact_text in low_signal:
        return False
    if len(set(compact_text)) <= 3:
        return False
    run = 1
    previous = ""
    for char in compact_text:
        if char == previous:
            run += 1
            if run >= 5:
                return False
        else:
            previous = char
            run = 1
    return True
