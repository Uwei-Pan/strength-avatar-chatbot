import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from database.db_connection import execute, fetch_all, fetch_one, get_connection


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "strengths_24.json"
DEFINITIONS_PATH = Path(__file__).resolve().parents[1] / "data" / "strength_definitions.json"

LOW_SIGNAL_PHRASES = [
    "今天很累",
    "不知道",
    "還好",
    "沒事",
    "普通",
    "很累",
    "想知道我的優勢",
    "可以給我建議嗎",
    "可以鼓勵我一下嗎",
    "請給我一個小任務",
]
CONFIDENCE_VALUES = {
    "high": 0.86,
    "medium": 0.68,
    "low": 0.45,
}


def load_strengths_from_json() -> list[dict[str, Any]]:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return data["strengths"]


@lru_cache(maxsize=1)
def load_strength_definitions() -> dict[str, Any]:
    return json.loads(DEFINITIONS_PATH.read_text(encoding="utf-8"))


def get_strength_definition_by_name(strength_name: str) -> dict[str, Any] | None:
    normalized = normalize_strength_name(strength_name)
    for item in load_strength_definitions().get("strengths", []):
        if item.get("name_zh") == normalized:
            return item
    return None


def get_strength_interpretation_principles() -> list[str]:
    data = load_strength_definitions()
    return list(data.get("interpretation_principles", []))


def build_strength_prompt_context() -> str:
    data = load_strength_definitions()
    lines = [
        "24 個成長亮點觀察參考（不是問卷，不要求學生填答）：",
    ]
    for item in data.get("strengths", []):
        indicators = "；".join(item.get("behavior_indicators", [])[:2])
        cues = "；".join(item.get("semantic_cues", [])[:2])
        lines.append(
            f"- {item['name_zh']} ({item['name_en']}｜{item['virtue']})："
            f"{item['core_definition']} 行為指標：{indicators}。語意線索：{cues}。"
            f"注意：{item.get('not_overinterpret', '')}"
        )
    return "\n".join(lines)


def get_all_strengths() -> list[dict[str, Any]]:
    rows = fetch_all("SELECT * FROM strengths ORDER BY category, name_zh")
    return list(rows)


def get_strength_by_name(strength_name: str) -> dict[str, Any] | None:
    return fetch_one(
        "SELECT * FROM strengths WHERE name_zh = %s",
        (normalize_strength_name(strength_name),),
    )


def normalize_strength_name(strength_name: str) -> str:
    aliases = {
        "恆毅力": "勤奮",
        "毅力": "勤奮",
        "堅毅": "勤奮",
        "盡責": "勤奮",
        "善良": "仁慈",
        "感恩": "感激",
        "合作": "團體合作",
    }
    return aliases.get(strength_name.strip(), strength_name.strip())


def detect_strengths_rule_based(message: str, source: str = "platform_interaction") -> list[dict[str, Any]]:
    text = message.strip()
    compact = re.sub(r"\s+", "", text)
    if len(text) <= 5 or any(phrase in compact for phrase in LOW_SIGNAL_PHRASES):
        return []

    detected: list[dict[str, Any]] = []
    for definition in load_strength_definitions().get("strengths", []):
        strength_name = definition["name_zh"]
        matched = _matched_definition_terms(text, definition)
        if matched:
            confidence_level = _confidence_level_from_matches(len(matched))
            detected.append(
                {
                    "strength_name": strength_name,
                    "confidence_level": confidence_level,
                    "confidence": CONFIDENCE_VALUES[confidence_level],
                    "evidence_count": 1,
                    "evidence_sources": [_canonical_evidence_source(source)],
                    "evidence_quotes": [text[:180]],
                    "evidence_text": text,
                    "reason": f"文字中出現與「{strength_name}」相關的行動、情境或語意線索：{', '.join(matched[:4])}",
                    "reasoning_summary": f"這段內容呈現了「{strength_name}」的可能展現。",
                    "child_friendly_feedback": definition.get("child_friendly_description", ""),
                    "teacher_facing_explanation": (
                        f"此觀察依據具體文字線索與「{strength_name}」的行為描述，"
                        "不是正式心理測驗結果；若只有單一紀錄，建議持續陪伴觀察。"
                    ),
                }
            )
    detected.sort(key=lambda item: (item["confidence"], len(item["reason"])), reverse=True)
    return detected[:2]


def _matched_definition_terms(text: str, definition: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for field in ("counseling_keywords", "semantic_cues", "observable_behaviors", "behavior_indicators"):
        for value in definition.get(field, []):
            for term in _candidate_terms(str(value)):
                if term and term in text and term not in terms:
                    terms.append(term)
    return terms


def _candidate_terms(value: str) -> list[str]:
    parts = re.split(r"[，、；,;／/（）()「」\s]+", value)
    return [part for part in parts if len(part) >= 2]


def _confidence_level_from_matches(match_count: int) -> str:
    if match_count >= 4:
        return "high"
    if match_count >= 2:
        return "medium"
    return "low"


def _canonical_evidence_source(source: str) -> str:
    source_map = {
        "initial_profile": "counseling_record",
        "counseling_record": "counseling_record",
        "diary": "journal",
        "journal": "journal",
        "todo": "task",
        "task": "task",
        "game": "game_response",
        "game_reflection": "game_response",
        "game_response": "game_response",
        "chat": "platform_interaction",
        "platform_interaction": "platform_interaction",
    }
    return source_map.get(str(source or "platform_interaction"), "platform_interaction")


def save_child_strength(
    child_id: str,
    strength_name: str,
    source: str,
    evidence_text: str,
    confidence: float,
) -> None:
    strength = get_strength_by_name(strength_name)
    if not strength:
        return

    with get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO child_strengths
                        (child_id, strength_id, source, evidence_text, confidence)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        child_id,
                        strength["strength_id"],
                        source,
                        evidence_text,
                        confidence,
                    ),
                )
                outfit_reward = strength.get("outfit_reward")
                if outfit_reward:
                    cursor.execute(
                        """
                        INSERT IGNORE INTO child_outfits
                            (child_id, outfit_id, unlocked_source)
                        VALUES (%s, %s, %s)
                        """,
                        (child_id, outfit_reward, source),
                    )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def get_child_strengths(child_id: str) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
            cs.id,
            cs.child_id,
            cs.source,
            cs.evidence_text,
            cs.confidence,
            cs.created_at,
            s.strength_id,
            s.name_zh,
            s.category,
            s.description,
            s.suggestion,
            s.fruit_name,
            s.outfit_reward
        FROM child_strengths cs
        JOIN strengths s ON s.strength_id = cs.strength_id
        WHERE cs.child_id = %s
        ORDER BY cs.created_at DESC, cs.id DESC
        """,
        (child_id,),
    )


def get_strength_context_for_game(child_id: str, strength_name: str) -> dict[str, Any]:
    normalized = normalize_strength_name(strength_name)
    from services.student_profile_service import get_random_strength_case

    profile_case = get_random_strength_case(child_id, normalized)
    if profile_case:
        return {
            "strength_name": normalized,
            "has_strength": True,
            "message": (
                f"你吃到了「{normalized}」果實！"
                f"過去紀錄裡有一個例子：{profile_case['description']} "
                f"這就是「{normalized}」的表現。"
            ),
            "case": profile_case,
        }

    row = fetch_one(
        """
        SELECT
            s.name_zh,
            s.category,
            s.description,
            s.suggestion,
            s.fruit_name,
            cs.evidence_text,
            cs.source
        FROM strengths s
        LEFT JOIN child_strengths cs
            ON cs.strength_id = s.strength_id
            AND cs.child_id = %s
        WHERE s.name_zh = %s
        ORDER BY cs.created_at DESC, cs.id DESC
        LIMIT 1
        """,
        (child_id, normalized),
    )
    if not row:
        return {
            "strength_name": normalized,
            "has_strength": False,
            "message": "這顆果實還在準備中，之後可以補上更多說明。",
        }

    if row.get("evidence_text"):
        message = (
            f"你之前曾經做到這件事：{row['evidence_text']} "
            f"這展現了「{row['name_zh']}」。"
        )
        has_strength = True
    else:
        message = f"{row['name_zh']}是{row['description']} {row['suggestion']}"
        has_strength = False

    return {
        "strength_name": row["name_zh"],
        "category": row["category"],
        "fruit_name": row["fruit_name"],
        "has_strength": has_strength,
        "message": message,
    }


def save_chat_log(
    child_id: str,
    user_message: str,
    ai_reply: str,
    emotion: str,
    detected_strengths: list[dict[str, Any]],
    tokens_earned: int,
) -> None:
    execute(
        """
        INSERT INTO chat_logs
            (child_id, user_message, ai_reply, emotion, detected_strengths_json, tokens_earned)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            child_id,
            user_message,
            ai_reply,
            emotion,
            json.dumps(detected_strengths, ensure_ascii=False),
            tokens_earned,
        ),
    )


def list_chat_logs(child_id: str, limit: int = 8) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, user_message, ai_reply, emotion,
               detected_strengths_json, tokens_earned, created_at
        FROM chat_logs
        WHERE child_id = %s
        ORDER BY created_at DESC, id DESC
        LIMIT %s
        """,
        (child_id, int(limit)),
    )
