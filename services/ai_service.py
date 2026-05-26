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

REFLECTION_VALIDATION_FALLBACK = {
    "is_valid": False,
    "reason": "回答需要更具體一點。",
    "gentle_prompt": "請寫下一句完整想法，說說你的感覺或下一次想怎麼做。",
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


def validate_reflection_answer(
    child_profile: dict[str, Any],
    question: str,
    answer: str,
) -> dict[str, Any]:
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    cleaned = answer.strip()
    local_result = _rule_validate_reflection(cleaned)
    if not local_result["is_valid"]:
        return local_result

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        return {
            **local_result,
            "mode": "mock",
            "error": "沒有偵測到 GEMINI_API_KEY，使用本機規則判斷。",
        }

    try:
        return _validate_reflection_with_gemini(child_profile, question, cleaned, api_key)
    except Exception as exc:
        return {
            **local_result,
            "mode": "mock",
            "error": _format_gemini_error(exc),
        }


def _validate_reflection_with_gemini(
    child_profile: dict[str, Any],
    question: str,
    answer: str,
    api_key: str,
) -> dict[str, Any]:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return _rule_validate_reflection(answer)

    client = genai.Client(api_key=api_key)
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    prompt = f"""
你正在協助兒童遊戲中的反思復活機制。請判斷孩子的回答是否「足夠具體且真誠」，可以讓他復活一次。

孩子名字：{child_profile.get("name", "孩子")}
問題：{question}
回答：{answer}

請只回傳 JSON：
{{
  "is_valid": true,
  "reason": "簡短原因",
  "gentle_prompt": "如果不合格，給孩子一句溫柔提醒；若合格，留空字串"
}}

判斷規則：
- 必須至少一句完整想法，約 6 個中文字/字元以上。
- 合格回答要有具體內容，例如事件、感受、行動、想法、想再試一次的方法、或提到某個優勢。
- 如果只是重複字、亂打、只有「不知道」「還好」「可以」「我要復活」、無意義符號、或明顯敷衍，請判斷不合格。
- 不要責備孩子；提醒要短、溫柔、明確。
"""
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            responseMimeType="application/json",
            temperature=0.1,
        ),
    )
    raw_text = getattr(response, "text", "") or ""
    parsed = _parse_json(raw_text)
    is_valid = bool(parsed.get("is_valid"))
    return {
        "is_valid": is_valid,
        "reason": str(parsed.get("reason") or ""),
        "gentle_prompt": str(parsed.get("gentle_prompt") or ""),
        "mode": "gemini",
        "error": "",
    }


def _rule_validate_reflection(answer: str) -> dict[str, Any]:
    cleaned = answer.strip()
    if len(cleaned) < 6:
        return {
            **REFLECTION_VALIDATION_FALLBACK,
            "reason": "回答太短。",
            "gentle_prompt": "請再多寫一點，例如：我想慢慢移動，不要太急。",
        }

    compact = re.sub(r"\s+", "", cleaned)
    unique_chars = set(compact)
    low_signal = ["不知道", "隨便", "還好", "沒有", "沒事", "可以了", "我要復活"]
    if any(phrase == compact or compact.count(phrase) >= 2 for phrase in low_signal):
        return {
            **REFLECTION_VALIDATION_FALLBACK,
            "reason": "回答太像敷衍或低訊息內容。",
            "gentle_prompt": "請換成一個比較真實的回答，例如說一件事、你的感覺，或下一次想怎麼做。",
        }
    if len(unique_chars) <= 5 or _has_long_repeated_run(compact):
        return {
            **REFLECTION_VALIDATION_FALLBACK,
            "reason": "回答看起來像重複字或亂打。",
            "gentle_prompt": "我想聽你真正的想法，請用一句完整的話說說看。",
        }

    return {
        "is_valid": True,
        "reason": "回答長度與內容通過本機規則。",
        "gentle_prompt": "",
        "mode": "mock",
        "error": "",
    }


def _has_long_repeated_run(text: str) -> bool:
    if not text:
        return False
    run = 1
    previous = text[0]
    for char in text[1:]:
        if char == previous:
            run += 1
            if run >= 6:
                return True
        else:
            previous = char
            run = 1
    return False


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
你是一位溫暖、支持、鼓勵孩子的兒少優勢探索 AI 夥伴。請用繁體中文回覆。
你的任務不是批評、命令或診斷孩子，而是陪孩子一起理解感受、看見自己的優勢，並給出簡單可行的小建議。

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
- reply_to_child 要像可靠的大哥哥大姐姐，溫暖、鼓勵、有陪伴感，不要像老師訓話。
- 回覆結構建議：先接住孩子的情緒；再肯定孩子願意說出來或已經做到的努力；若有明確根據，再自然提到優勢；最後給一個小小可行的下一步。
- reply_to_child 控制在 3 到 6 句，句子短一點，適合兒童閱讀。
- 一次只問 1 個主要問題，不要一次丟很多問題給孩子。
- 可以自然引導孩子多說「發生了什麼、當時感覺、做了什麼選擇、哪裡做得不錯、要不要試一個小任務」。
- 如果孩子分享太短，例如「嗨」「不知道」「還好」，請溫柔說明還不太夠判斷優勢，並只追問一個具體問題。
- 不要在 reply_to_child 裡自行宣告精確代幣數；後端會依照孩子分享的具體度附加實際代幣提示。
- 可以用自然口吻提醒：「說得越具體，我越能看見你的優勢，也可能幫你獲得優勢代幣。」
- 不責備、不說教、不過度診斷，也不要要求孩子立刻變好。
- 不要每次都硬判斷優勢。
- 如果只是「今天很累」「不知道」「還好」這類低訊息內容，不要新增優勢。
- 如果孩子低落、自責或挫折，先承接情緒，不急著貼標籤。
- detected_strengths 最多 2 個。
- 如果要提到過去案例，只能使用「可引用的過去匿名案例」中明確存在的內容。
- 如果案例清單沒有相關內容，不可以編造過去事件，只能用一般鼓勵語氣。
- 如果孩子提到危險、自傷、想傷害自己、被傷害、被威脅或嚴重情緒困擾，要先溫柔接住，並明確建議孩子立刻找可信任的大人、老師、輔導老師或家人協助；不要只用一般鼓勵帶過。
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
    if _has_safety_concern(message):
        return _normalize_result(
            {
                "reply_to_child": (
                    "謝謝你把這麼重要的事情說出來，這真的需要被好好照顧。"
                    "你不用一個人撐著，請現在就去找一位可信任的大人、老師、輔導老師或家人陪你。"
                    "如果你正有危險，請立刻離開危險的地方，並請身邊的大人幫你聯絡緊急協助。"
                ),
                "emotion": "需要協助",
                "detected_strengths": [],
                "should_award_tokens": True,
                "tokens_earned": 10,
                "follow_up_question": "你身邊現在有哪一位大人可以馬上陪你嗎？",
                "mode": "mock",
                "error": error,
            },
            message,
        )

    detected = detect_strengths_rule_based(message)
    emotion = _guess_emotion(message)
    if emotion in {"挫折", "低落", "疲累"}:
        reply = (
            "聽起來你今天真的不太容易。謝謝你願意說出來，"
            "這本身就是很勇敢的一小步。你不用一下子就變好，"
            "我們可以先把最卡住的地方慢慢說清楚。"
        )
        if detected:
            reply += f" 我也看到你有一點「{detected[0]['strength_name']}」的影子。"
        reply += " 下一步可以先深呼吸三次，再挑一件最想被理解的事情告訴我。"
    elif detected:
        reply = (
            f"謝謝你跟我分享，這聽起來是很值得記下來的一刻。"
            f"你剛剛說的事情裡，我看到一點「{detected[0]['strength_name']}」。"
        )
        child_id = (child_profile or {}).get("child_id", "")
        profile_case = get_random_strength_case(child_id, detected[0]["strength_name"])
        if profile_case:
            reply += f" 我也想到你過去有一個例子：{profile_case['description']}。"
        reply += " 可以把這件事當成今天的一顆優勢果實，等一下再想想你是怎麼做到的。"
    else:
        reply = (
            "謝謝你願意告訴我。聽起來這件事在你心裡有一點重量，"
            "你願意把它說出來已經很不容易。"
            "我們可以先不急著判斷對錯，只一起看看到底發生了什麼。"
        )

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
    if any(word in message for word in ["生氣", "火大", "憤怒"]):
        return "生氣"
    if any(word in message for word in ["緊張", "焦慮", "擔心"]):
        return "緊張"
    if any(word in message for word in ["煩", "考不好", "失敗", "挫折", "不會"]):
        return "挫折"
    if any(word in message for word in ["累", "疲倦", "想睡"]):
        return "疲累"
    if any(word in message for word in ["難過", "低落", "哭"]):
        return "低落"
    if any(word in message for word in ["開心", "高興", "興奮"]):
        return "開心"
    return "平穩"


def _has_safety_concern(message: str) -> bool:
    concern_words = [
        "自殺",
        "不想活",
        "傷害自己",
        "割腕",
        "想死",
        "被打",
        "被傷害",
        "被威脅",
        "家暴",
        "霸凌到受不了",
    ]
    return any(word in message for word in concern_words)


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
