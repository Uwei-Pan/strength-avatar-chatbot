import json
from pathlib import Path
from typing import Any

from database.db_connection import execute, fetch_all, fetch_one, get_connection


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "strengths_24.json"

RULES = [
    ("仁慈", ["幫", "照顧", "分享", "安慰"]),
    ("勤奮", ["完成", "努力", "練習", "堅持"]),
    ("好奇心", ["嘗試", "新", "發現", "為什麼"]),
    ("勇敢", ["害怕但", "勇敢", "挑戰"]),
    ("感激", ["謝謝", "感謝"]),
    ("團體合作", ["一起", "合作", "隊友", "幫忙完成"]),
]

LOW_SIGNAL_PHRASES = ["今天很累", "不知道", "還好", "沒事", "普通", "很累"]


def load_strengths_from_json() -> list[dict[str, Any]]:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return data["strengths"]


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


def detect_strengths_rule_based(message: str) -> list[dict[str, Any]]:
    text = message.strip()
    if len(text) <= 5 or any(phrase == text for phrase in LOW_SIGNAL_PHRASES):
        return []

    detected: list[dict[str, Any]] = []
    for strength_name, keywords in RULES:
        if any(keyword in text for keyword in keywords):
            detected.append(
                {
                    "strength_name": strength_name,
                    "confidence": 0.72,
                    "evidence_text": text,
                    "reason": f"文字中出現與「{strength_name}」相關的行動或感受。",
                }
            )
    return detected[:2]


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
