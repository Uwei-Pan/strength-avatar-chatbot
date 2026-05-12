import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from services.strength_service import detect_strengths_rule_based, normalize_strength_name
from services.student_profile_service import get_ai_case_context, get_random_strength_case


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)


DEFAULT_RESULT = {
    "reply_to_child": "謝謝你願意跟我說。聽起來今天有一些感受在心裡，我會陪你慢慢整理。你想先說說最在意的是哪一件事嗎？",
    "emotion": "未明",
    "detected_strengths": [],
    "should_award_tokens": True,
    "tokens_earned": 10,
    "follow_up_question": "你想先說說最在意的是哪一件事嗎？",
    "mode": "mock",
    "error": "",
}

ALLOWED_STRENGTH_NAMES = {
    "創造力",
    "好奇心",
    "判斷力",
    "喜愛學習",
    "洞察力",
    "勇敢",
    "勤奮",
    "真誠",
    "熱誠",
    "愛與被愛",
    "仁慈",
    "社交智慧",
    "團體合作",
    "公平",
    "領導力",
    "寬恕",
    "謙遜",
    "審慎",
    "自我規範",
    "欣賞美好",
    "感激",
    "希望",
    "幽默",
    "靈性",
}


def analyze_child_message(child_profile: dict[str, Any], message: str) -> dict[str, Any]:
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    cleaned = message.strip()
    if not cleaned:
        return {
            **DEFAULT_RESULT,
            "reply_to_child": "你可以慢慢來，想到什麼再告訴我就好。",
            "should_award_tokens": False,
            "tokens_earned": 0,
        }

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        return _mock_analyze(cleaned, "沒有偵測到 GEMINI_API_KEY，使用 mock mode。", child_profile)

    try:
        return _analyze_with_gemini(child_profile, cleaned, api_key)
    except Exception as exc:
        return _mock_analyze(cleaned, _format_gemini_error(exc), child_profile)


def _analyze_with_gemini(
    child_profile: dict[str, Any], message: str, api_key: str
) -> dict[str, Any]:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return _mock_analyze(message)

    client = genai.Client(api_key=api_key)
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    strengths = [
        item.get("name_zh")
        for item in child_profile.get("owned_strengths", [])
        if item.get("name_zh")
    ]
    case_context = get_ai_case_context(child_profile.get("child_id", ""))
    prompt = f"""
你是兒少優勢探索 AI。請用繁體中文回覆，語氣溫暖、簡短、具體、不說教、不誇大。

孩子資料：
- 名字：{child_profile.get("name", "孩子")}
- 已知優勢：{", ".join(sorted(set(strengths))) if strengths else "尚未提供"}

可引用的過去匿名案例：
{case_context}

孩子訊息：
{message}

只能使用以下 24 種優勢名稱，不可以創造其他名稱：
{", ".join(sorted(ALLOWED_STRENGTH_NAMES))}

請只回傳 JSON，不要加 Markdown。格式必須是：
{{
  "reply_to_child": "給孩子的簡短回覆",
  "emotion": "情緒名稱",
  "detected_strengths": [
    {{
      "strength_name": "優勢名稱",
      "confidence": 0.0,
      "evidence_text": "孩子訊息中的具體 evidence",
      "reason": "判斷原因"
    }}
  ],
  "should_award_tokens": true,
  "tokens_earned": 10,
  "follow_up_question": "一個簡單追問"
}}

規則：
- 不要每次都硬判斷優勢。
- 如果只是「今天很累」「不知道」「還好」這類低訊息內容，不要新增優勢。
- 如果孩子低落、自責或挫折，先承接情緒，不急著貼標籤。
- detected_strengths 最多 2 個。
- 如果要提到過去案例，只能使用「可引用的過去匿名案例」中明確存在的內容。
- 如果案例清單沒有相關內容，不可以編造過去事件，只能用一般鼓勵語氣。
"""
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            responseMimeType="application/json",
            temperature=0.4,
        ),
    )
    raw_text = getattr(response, "text", "") or ""
    result = _normalize_result(_parse_json(raw_text), message)
    result["mode"] = "gemini"
    result["error"] = ""
    return result


def _parse_json(raw_text: str) -> dict[str, Any]:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _mock_analyze(
    message: str,
    error: str = "",
    child_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    detected = detect_strengths_rule_based(message)
    emotion = _guess_emotion(message)
    if emotion in {"挫折", "低落", "疲累"}:
        reply = (
            "聽起來你今天真的不太容易。謝謝你願意說出來，"
            "這件事可以慢慢整理，不用一下子就變好。"
        )
        if detected:
            reply += f" 我也看到你有一點「{detected[0]['strength_name']}」的影子。"
    elif detected:
        reply = (
            f"謝謝你跟我分享。你剛剛說的事情裡，"
            f"我看到一點「{detected[0]['strength_name']}」。"
        )
        child_id = (child_profile or {}).get("child_id", "")
        profile_case = get_random_strength_case(child_id, detected[0]["strength_name"])
        if profile_case:
            reply += f" 我也想到你過去有一個例子：{profile_case['description']}"
    else:
        reply = "謝謝你願意告訴我。聽起來這件事對你有一點感覺，我想多了解一些。"

    follow_up = "你願意再說一點，當時你心裡最明顯的感覺是什麼嗎？"
    return _normalize_result(
        {
            "reply_to_child": reply,
            "emotion": emotion,
            "detected_strengths": detected,
            "should_award_tokens": True,
            "tokens_earned": 10,
            "follow_up_question": follow_up,
            "mode": "mock",
            "error": error,
        },
        message,
    )


def _format_gemini_error(exc: Exception) -> str:
    message = str(exc)
    if len(message) > 700:
        message = message[:700] + "..."
    return f"Gemini API 呼叫失敗，使用 mock mode：{type(exc).__name__}: {message}"


def _guess_emotion(message: str) -> str:
    if any(word in message for word in ["煩", "考不好", "失敗", "挫折", "不會"]):
        return "挫折"
    if any(word in message for word in ["累", "疲倦", "想睡"]):
        return "疲累"
    if any(word in message for word in ["難過", "低落", "哭"]):
        return "低落"
    if any(word in message for word in ["開心", "高興", "興奮"]):
        return "開心"
    return "平穩"


def _normalize_result(result: dict[str, Any], message: str) -> dict[str, Any]:
    normalized = {**DEFAULT_RESULT, **(result or {})}
    detected = normalized.get("detected_strengths")
    if not isinstance(detected, list):
        detected = []
    normalized["detected_strengths"] = _clean_detected_strengths(detected)
    normalized["should_award_tokens"] = bool(normalized.get("should_award_tokens", True))
    normalized["tokens_earned"] = 10 if normalized["should_award_tokens"] else 0
    normalized["reply_to_child"] = str(normalized.get("reply_to_child") or DEFAULT_RESULT["reply_to_child"])
    normalized["emotion"] = str(normalized.get("emotion") or _guess_emotion(message))
    normalized["follow_up_question"] = str(normalized.get("follow_up_question") or "")
    return normalized


def _clean_detected_strengths(detected: list[Any]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in detected:
        if not isinstance(item, dict) or not item.get("strength_name"):
            continue

        strength_name = normalize_strength_name(str(item["strength_name"]))
        if strength_name not in ALLOWED_STRENGTH_NAMES or strength_name in seen:
            continue

        item = dict(item)
        item["strength_name"] = strength_name
        item["confidence"] = float(item.get("confidence") or 0.7)
        cleaned.append(item)
        seen.add(strength_name)
        if len(cleaned) >= 2:
            break
    return cleaned
