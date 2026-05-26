import json
import random
from functools import lru_cache
from pathlib import Path
from typing import Any

from database.db_connection import fetch_all
from services.strength_service import normalize_strength_name


PROFILE_PATH = Path(__file__).resolve().parents[1] / "data" / "student_strength_profiles.json"


@lru_cache(maxsize=1)
def load_student_profiles() -> dict[str, dict[str, Any]]:
    if not PROFILE_PATH.exists():
        return {}
    data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    return {
        profile["child_id"]: profile
        for profile in data.get("students", [])
        if profile.get("child_id")
    }


def get_student_profile(child_id: str) -> dict[str, Any] | None:
    return load_student_profiles().get(child_id)


def get_student_strength_cases(child_id: str, strength_name: str) -> list[dict[str, Any]]:
    profile = get_student_profile(child_id)
    if not profile:
        return []
    normalized = normalize_strength_name(strength_name)
    cases = profile.get("strength_cases", {}).get(normalized, [])
    return list(cases) if isinstance(cases, list) else []


def get_random_strength_case(child_id: str, strength_name: str) -> dict[str, Any] | None:
    cases = get_student_strength_cases(child_id, strength_name)
    if not cases:
        return None
    return random.choice(cases)


def get_top_strengths(child_id: str) -> list[dict[str, Any]]:
    profile = get_student_profile(child_id)
    if not profile:
        return []
    strengths = profile.get("top_strengths", [])
    return list(strengths) if isinstance(strengths, list) else []


def get_initial_equipment(child_id: str) -> list[dict[str, Any]]:
    return [
        {
            "strength_name": item.get("strength_name"),
            "category": item.get("category"),
            "outfit_reward": item.get("outfit_reward"),
            "source": "counseling_record",
        }
        for item in get_top_strengths(child_id)
        if item.get("outfit_reward")
    ]


def get_ai_case_context(child_id: str, max_strengths: int = 5, max_cases_each: int = 2) -> str:
    profile = get_student_profile(child_id)
    if not profile:
        return "沒有可引用的過去案例。"

    lines = []
    for strength in profile.get("top_strengths", [])[:max_strengths]:
        strength_name = strength.get("strength_name")
        if not strength_name:
            continue
        cases = get_student_strength_cases(child_id, strength_name)[:max_cases_each]
        if not cases:
            continue
        descriptions = "；".join(case.get("description", "") for case in cases)
        lines.append(f"- {strength_name}：{descriptions}")

    if not lines:
        return "沒有可引用的過去案例。"
    return "\n".join(lines)


def get_ai_observation_context(child_id: str, limit_each: int = 5) -> str:
    sections = [
        _format_observation_section("輔導紀錄 / counseling_record", _counseling_observations(child_id, limit_each)),
        _format_observation_section("心情日記 / journal", _db_text_rows(
            """
            SELECT content AS text, created_at
            FROM diary_entries
            WHERE child_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT %s
            """,
            child_id,
            limit_each,
        )),
        _format_observation_section("任務清單 / task", _db_text_rows(
            """
            SELECT CONCAT(
                CASE WHEN is_completed THEN '已完成任務：' ELSE '未完成任務：' END,
                title,
                CASE WHEN description IS NULL OR description = '' THEN '' ELSE CONCAT('；', description) END
            ) AS text,
            COALESCE(completed_at, created_at) AS created_at
            FROM todo_items
            WHERE child_id = %s
            ORDER BY COALESCE(completed_at, created_at) DESC, id DESC
            LIMIT %s
            """,
            child_id,
            limit_each,
        )),
        _format_observation_section("遊戲復活回答 / game_response", _db_text_rows(
            """
            SELECT CONCAT('問題：', question, '；回答：', answer) AS text, created_at
            FROM game_reflections
            WHERE child_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT %s
            """,
            child_id,
            limit_each,
        )),
        _format_observation_section("平台互動文字 / platform_interaction", _db_text_rows(
            """
            SELECT user_message AS text, created_at
            FROM chat_logs
            WHERE child_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT %s
            """,
            child_id,
            limit_each,
        )),
    ]
    context = "\n".join(section for section in sections if section)
    return context or "目前沒有足夠的跨來源觀察資料。"


def _counseling_observations(child_id: str, limit_each: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    profile = get_student_profile(child_id)
    if profile:
        for record in profile.get("records", [])[: limit_each * 2]:
            for event in record.get("key_events", [])[:2]:
                if event:
                    rows.append({"text": event, "created_at": record.get("source_label") or record.get("month")})
                    if len(rows) >= limit_each:
                        return rows

    rows.extend(_db_text_rows(
        """
        SELECT cs.evidence_text AS text, cs.created_at
        FROM child_strengths cs
        WHERE cs.child_id = %s AND cs.source = 'counseling_record'
        ORDER BY cs.created_at DESC, cs.id DESC
        LIMIT %s
        """,
        child_id,
        limit_each - len(rows),
    ))
    return rows[:limit_each]


def _db_text_rows(sql: str, child_id: str, limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    try:
        return list(fetch_all(sql, (child_id, int(limit))))
    except Exception:
        return []


def _format_observation_section(title: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    lines = [f"{title}："]
    for row in rows:
        text = str(row.get("text") or "").strip()
        if not text:
            continue
        text = text.replace("\n", " ")
        if len(text) > 180:
            text = text[:180] + "..."
        lines.append(f"- {text}")
    return "\n".join(lines) if len(lines) > 1 else ""
