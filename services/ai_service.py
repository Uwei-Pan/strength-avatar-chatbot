import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from services.strength_service import (
    detect_strengths_rule_based,
    get_strength_definition_by_name,
    normalize_strength_name,
)
from services.student_profile_service import (
    get_random_strength_case,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
ENV_LOCAL_PATH = PROJECT_ROOT / ".env.local"
ENVC_PATH = PROJECT_ROOT / ".envc"
PLACEHOLDER_API_KEYS = {
    "",
    "your_gemini_api_key_here",
    "your_api_key_here",
    "你的_api_key",
    "change_me",
}
DIARY_STRENGTH_CONFIDENCE_THRESHOLD = 0.65
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"
DIARY_GEMINI_MIN_CHINESE_CHARS = 10
DIARY_GEMINI_MAX_INPUT_CHARS = 500
DIARY_GEMINI_MAX_OUTPUT_TOKENS = 150
CHAT_GEMINI_MAX_OUTPUT_TOKENS = 180
REFLECTION_GEMINI_MAX_OUTPUT_TOKENS = 120

load_dotenv(dotenv_path=ENVC_PATH, override=False)
load_dotenv(dotenv_path=ENV_PATH, override=True)
load_dotenv(dotenv_path=ENV_LOCAL_PATH, override=True)


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

ALLOWED_EVIDENCE_SOURCES = {
    "counseling_record",
    "journal",
    "task",
    "game_response",
    "platform_interaction",
}


def _load_ai_environment() -> None:
    load_dotenv(dotenv_path=ENVC_PATH, override=False)
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    load_dotenv(dotenv_path=ENV_LOCAL_PATH, override=True)


def get_gemini_api_key() -> str:
    _load_ai_environment()
    api_key = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
    if api_key and api_key.lower() not in PLACEHOLDER_API_KEYS:
        return api_key
    secret_key = _get_streamlit_secret("GEMINI_API_KEY")
    if secret_key and secret_key.lower() not in PLACEHOLDER_API_KEYS:
        return secret_key
    return ""


def get_gemini_model() -> str:
    _load_ai_environment()
    model = os.getenv("GEMINI_MODEL", "").strip().strip('"').strip("'")
    model = model or _get_streamlit_secret("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
    return model if _is_allowed_flash_model(model) else DEFAULT_GEMINI_MODEL


def get_gemini_model_candidates() -> list[str]:
    return [get_gemini_model()]


def _is_allowed_flash_model(model: str) -> bool:
    lowered = model.strip().lower()
    return bool(lowered) and "gemini" in lowered and "flash" in lowered and "pro" not in lowered


def _get_streamlit_secret(name: str) -> str:
    try:
        import streamlit as st

        return str(st.secrets.get(name, "")).strip().strip('"').strip("'")
    except Exception:
        return ""


def get_gemini_setup_status() -> dict[str, Any]:
    _load_ai_environment()
    api_key = get_gemini_api_key()
    key_source = ""
    value = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
    if value and value.lower() not in PLACEHOLDER_API_KEYS:
        key_source = "GEMINI_API_KEY"
    else:
        secret_value = _get_streamlit_secret("GEMINI_API_KEY")
        if secret_value and secret_value.lower() not in PLACEHOLDER_API_KEYS:
            key_source = "st.secrets.GEMINI_API_KEY"
    return {
        "has_api_key": bool(api_key),
        "key_source": key_source,
        "model": get_gemini_model(),
        "model_candidates": get_gemini_model_candidates(),
        "env_path": str(ENV_PATH),
        "env_exists": ENV_PATH.exists(),
        "env_local_exists": ENV_LOCAL_PATH.exists(),
        "envc_exists": ENVC_PATH.exists(),
    }


def analyze_child_message(child_profile: dict[str, Any], message: str) -> dict[str, Any]:
    _load_ai_environment()
    cleaned = message.strip()
    if not cleaned:
        return {
            **DEFAULT_RESULT,
            "reply_to_child": "你可以慢慢來，想到什麼再告訴我就好。",
            "should_award_tokens": False,
            "tokens_earned": 0,
        }

    api_key = get_gemini_api_key()
    if not api_key:
        return _mock_analyze(cleaned, "沒有設定有效的 GEMINI_API_KEY，使用 mock mode。", child_profile)

    try:
        return _analyze_with_gemini(child_profile, cleaned, api_key)
    except Exception as exc:
        return _mock_analyze(cleaned, _format_gemini_error(exc), child_profile)


def analyze_diary_entry(child_profile: dict[str, Any], content: str) -> dict[str, Any]:
    _load_ai_environment()
    cleaned = content.strip()
    if not cleaned:
        return _diary_fallback_result("謝謝你願意記錄今天。")
    if _count_chinese_chars(cleaned) < DIARY_GEMINI_MIN_CHINESE_CHARS:
        return _diary_fallback_result("日記已儲存，謝謝你願意記錄今天。", mode="local_skip")

    api_key = get_gemini_api_key()
    if not api_key:
        return _diary_fallback_result(
            "日記已儲存，謝謝你分享。",
            error="沒有設定有效的 GEMINI_API_KEY，已先儲存日記。",
        )

    try:
        return _analyze_diary_with_gemini(child_profile, cleaned[:DIARY_GEMINI_MAX_INPUT_CHARS], api_key)
    except Exception as exc:
        return _diary_fallback_result(
            "日記已儲存，AI 小幫手晚點再來幫你整理。",
            error=_format_gemini_error(exc),
        )


def validate_reflection_answer(
    child_profile: dict[str, Any],
    question: str,
    answer: str,
) -> dict[str, Any]:
    _load_ai_environment()
    cleaned = answer.strip()
    local_result = _rule_validate_reflection(cleaned)
    if not local_result["is_valid"]:
        return local_result

    api_key = get_gemini_api_key()
    if not api_key:
        return {
            **local_result,
            "mode": "mock",
            "error": "沒有設定有效的 GEMINI_API_KEY，使用本機規則確認。",
        }

    try:
        return _validate_reflection_with_gemini(child_profile, question, cleaned, api_key)
    except Exception as exc:
        return {
            **local_result,
            "mode": "mock",
            "error": _format_gemini_error(exc),
        }


def _analyze_diary_with_gemini(
    child_profile: dict[str, Any],
    content: str,
    api_key: str,
) -> dict[str, Any]:
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        return _diary_fallback_result(
            "日記已儲存，AI 小幫手晚點再來幫你整理。",
            error=f"缺少 google-genai 套件：{exc}",
        )

    client = genai.Client(api_key=api_key)
    prompt = f"""
你是兒童日記優勢判斷助手。
請根據日記內容判斷是否明確出現以下任一優勢：
仁慈、勇敢、勤奮、希望、感恩、自我規範、社交智慧、真誠、好奇、創造力、領導、團隊合作、公平、寬恕、謙虛、審慎、幽默、愛、愛學習、判斷力、觀察力、毅力、欣賞美與卓越、靈性。

規則：
1. 只有明確出現行為或想法時才判斷優勢。
2. 不明確就 has_strength=false。
3. 不要硬判斷。
4. 只回傳 JSON，不要其他文字。

日記：
{content}

回傳格式：
{{
  "has_strength": true/false,
  "strength_name": "優勢名稱或 null",
  "confidence": 0到1,
  "encouragement": "一句溫柔鼓勵"
}}
"""
    response, used_model = _generate_gemini_content(
        client,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            max_output_tokens=DIARY_GEMINI_MAX_OUTPUT_TOKENS,
            temperature=0.2,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
        max_retries=1,
    )
    parsed = _parse_json(getattr(response, "text", "") or "")
    strength = _diary_strength_from_json(parsed, content)
    encouragement = _safe_diary_encouragement(
        str(parsed.get("encouragement") or "").strip(),
        has_strength=bool(strength),
    )
    return {
        "reply_to_child": encouragement,
        "emotion": _guess_emotion(content),
        "detected_strengths": [strength] if strength else [],
        "should_award_tokens": True,
        "tokens_earned": 0,
        "follow_up_question": "",
        "mode": "gemini",
        "error": "",
        "model": used_model,
        "diary_analysis": {
            "has_strength": bool(strength),
            "strength_name": strength["strength_name"] if strength else None,
            "confidence": strength["confidence"] if strength else 0,
            "reason": str(parsed.get("reason") or ""),
            "encouragement": encouragement,
        },
    }


def _diary_strength_from_json(parsed: dict[str, Any], content: str) -> dict[str, Any] | None:
    if not bool(parsed.get("has_strength")):
        return None
    strength_name = normalize_strength_name(str(parsed.get("strength_name") or ""))
    if strength_name not in ALLOWED_STRENGTH_NAMES:
        return None
    try:
        confidence = float(parsed.get("confidence") or 0)
    except (TypeError, ValueError):
        confidence = 0
    confidence = max(0.0, min(1.0, confidence))
    if confidence < DIARY_STRENGTH_CONFIDENCE_THRESHOLD:
        return None
    reason = str(parsed.get("reason") or "")
    definition = get_strength_definition_by_name(strength_name) or {}
    return {
        "strength_name": strength_name,
        "confidence_level": _clean_confidence_level("", confidence),
        "confidence": confidence,
        "evidence_count": 1,
        "evidence_sources": ["journal"],
        "evidence_quotes": [content[:220]],
        "evidence_text": content,
        "reason": reason,
        "reasoning_summary": reason or f"日記中呈現了「{strength_name}」的具體線索。",
        "child_friendly_feedback": str(
            parsed.get("encouragement")
            or definition.get("child_friendly_description")
            or "謝謝你願意分享今天。"
        ),
        "teacher_facing_explanation": (
            f"Gemini 依日記文字判斷可能呈現「{strength_name}」，"
            f"confidence={confidence:.2f}；此紀錄不是正式心理測驗，仍需持續觀察。"
        ),
    }


def _diary_fallback_result(reply: str, *, error: str = "", mode: str = "fallback") -> dict[str, Any]:
    return {
        "reply_to_child": reply,
        "emotion": "平穩",
        "detected_strengths": [],
        "should_award_tokens": True,
        "tokens_earned": 0,
        "follow_up_question": "",
        "mode": mode,
        "error": error,
        "diary_analysis": {
            "has_strength": False,
            "strength_name": None,
            "confidence": 0,
            "reason": "",
            "encouragement": reply,
        },
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
    except ImportError as exc:
        return {
            **_rule_validate_reflection(answer),
            "mode": "mock",
            "error": f"缺少 google-genai 套件：{exc}",
        }

    client = genai.Client(api_key=api_key)
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
- 必須至少一句完整想法，約 10 個中文字/字元以上。
- 合格回答要有具體內容，例如事件、感受、行動、想法、想再試一次的方法、或提到某個優勢。
- 如果只是重複字、亂打、只有「不知道」「還好」「可以」「我要復活」、無意義符號、或明顯敷衍，請判斷不合格。
- 不要責備孩子；提醒要短、溫柔、明確。
"""
    response, _model = _generate_gemini_content(
        client,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            max_output_tokens=REFLECTION_GEMINI_MAX_OUTPUT_TOKENS,
            temperature=0.2,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
        max_retries=1,
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
    compact = re.sub(r"\s+", "", cleaned)
    if len(compact) < 10:
        return {
            **REFLECTION_VALIDATION_FALLBACK,
            "reason": "回答太短。",
            "gentle_prompt": "請寫滿 10 個字以上，例如：我想慢慢移動，不要太急。",
        }

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
    except ImportError as exc:
        return _mock_analyze(message, f"缺少 google-genai 套件：{exc}", child_profile)

    client = genai.Client(api_key=api_key)
    strengths = [
        item.get("name_zh")
        for item in child_profile.get("owned_strengths", [])
        if item.get("name_zh")
    ]
    # 調整聊天回覆長度與語氣時，優先修改下方「規則」段落。
    prompt = f"""
你是一位溫暖、支持、鼓勵孩子的 ai-for-children AI 夥伴。請用繁體中文回覆。
你的任務不是批評、命令或診斷孩子，而是陪孩子一起理解感受、看見自己的優勢，並給出簡單可行的小建議。
你會使用 24 個成長亮點作為觀察參考，但不得要求孩子填寫問卷，也不得宣稱這是正式心理測驗。

孩子資料：
- 名字：{child_profile.get("name", "孩子")}
- 已知優勢：{", ".join(sorted(set(strengths))) if strengths else "尚未提供"}

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
      "confidence": 0.0
    }}
  ],
  "follow_up_question": "一個簡單追問"
}}

規則：
- reply_to_child 要像可靠的大哥哥大姐姐，溫暖、鼓勵、有陪伴感，不要像老師訓話。
- reply_to_child 請短而溫柔：最多 2 句，總長 55 個中文字以內。
- 回覆結構建議：一句接住孩子的情緒；一句肯定具體努力或亮點；一句給小小下一步或追問。不要每次都完整長篇整理。
- 如果要提到優勢，只提 1 個最明確的優勢，並用一句話說完，不要長篇解釋。
- 一次只問 1 個主要問題，不要一次丟很多問題給孩子。
- follow_up_question 也要短，只留 1 個清楚問題，約 14 個中文字以內。
- 可以自然引導孩子多說「發生了什麼、當時感覺、做了什麼選擇、哪裡做得不錯、要不要試一個小任務」。
- 如果孩子分享太短，例如「嗨」「不知道」「還好」，請溫柔說明還需要多一點故事才能看見亮點，並只追問一個具體問題。
- 如果孩子說的是負面內容、被誤會、被罵、衝突、生氣、難過、委屈或壓力，請先承接情緒並追問細節；detected_strengths 回傳 []，不要急著判斷優勢。
- 不要在 reply_to_child 裡自行宣告精確代幣數；後端會依照孩子分享的具體度附加實際代幣提示。
- 可以用自然口吻提醒：「說得越具體，我越能看見你的亮點，也可能幫你獲得優勢代幣。」
- 不責備、不說教、不過度診斷，也不要要求孩子立刻變好。
- 不要每次都硬整理優勢。
- 如果只是「今天很累」「不知道」「還好」這類低訊息內容，不要新增優勢。
- 如果具體行為紀錄還不夠完整，detected_strengths 請留空，或將 confidence_level 設為 low 並在 reasoning_summary 標示「可以繼續觀察」。
- 如果兩項優勢證據量接近，可以在 reasoning_summary 說「相近」或「可能並列」，不要強行排序。
- 不要說任何優勢是弱點，也不要把孩子和其他學生比較。
- 優勢是可成長的觀察，不是固定人格標籤。
- 如果孩子低落、自責或挫折，先承接情緒，不急著貼標籤。
- detected_strengths 最多 1 個，沒有明確證據就回傳 []。
- 如果要提到過去案例，只能使用「可引用的過去匿名案例」中明確存在的內容。
- 如果案例清單沒有相關內容，不可以編造過去事件，只能用一般鼓勵語氣。
- 如果孩子提到危險、自傷、想傷害自己、被傷害、被威脅或嚴重情緒困擾，要先溫柔接住，並明確建議孩子立刻找可信任的大人、老師、輔導老師或家人協助；不要只用一般鼓勵帶過。
"""
    response, used_model = _generate_gemini_content(
        client,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            max_output_tokens=CHAT_GEMINI_MAX_OUTPUT_TOKENS,
            temperature=0.2,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
        max_retries=1,
    )
    raw_text = getattr(response, "text", "") or ""
    result = _normalize_result(_parse_json(raw_text), message)
    result["mode"] = "gemini"
    result["error"] = ""
    result["model"] = used_model
    result["estimated_tokens_used"] = _estimate_text_tokens(prompt) + _estimate_text_tokens(raw_text)
    return result


def _generate_gemini_content(client: Any, *, contents: str, config: Any, max_retries: int = 1):
    errors = []
    for model in get_gemini_model_candidates():
        for attempt in range(max_retries + 1):
            try:
                return client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                ), model
            except Exception as exc:
                errors.append((model, exc))
                if not _is_retryable_gemini_error(exc) or attempt >= max_retries:
                    break
    if len(errors) == 1:
        raise errors[0][1]
    summary = "；".join(
        f"{model}: {type(exc).__name__}: {str(exc)[:180]}"
        for model, exc in errors
    )
    raise RuntimeError(f"Gemini 模型都暫時無法使用：{summary}")


def _is_retryable_gemini_error(exc: Exception) -> bool:
    message = str(exc).lower()
    retryable_markers = [
        "503",
        "unavailable",
        "high demand",
        "429",
        "resource_exhausted",
        "quota",
        "not_found",
        "404",
    ]
    return any(marker in message for marker in retryable_markers)


def _parse_json(raw_text: str) -> dict[str, Any]:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _count_chinese_chars(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def _estimate_text_tokens(text: str) -> int:
    compact = str(text or "")
    if not compact:
        return 0
    chinese_chars = _count_chinese_chars(compact)
    non_chinese_chars = max(0, len(compact) - chinese_chars)
    return max(1, int(chinese_chars * 1.1 + non_chinese_chars / 4) + 1)


def _safe_diary_encouragement(text: str, *, has_strength: bool) -> str:
    fallback = "日記已儲存，謝謝你願意記錄今天。"
    cleaned = text.strip() or fallback
    if has_strength:
        return cleaned
    blocked_phrases = [
        "沒有優勢",
        "未看見優勢",
        "判斷不出優勢",
        "看不出優勢",
        "沒有明確優勢",
        "未判斷出",
    ]
    if any(phrase in cleaned for phrase in blocked_phrases):
        return fallback
    return cleaned


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
            "我們可以先不急著分對錯，只一起看看到底發生了什麼。"
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
    lowered = message.lower()
    if "503" in lowered or "unavailable" in lowered or "high demand" in lowered:
        return (
            "Gemini API 目前回覆忙碌或暫時不可用，已先使用 mock mode："
            f"{type(exc).__name__}: {message[:260]}"
        )
    if "429" in lowered or "resource_exhausted" in lowered or "quota" in lowered:
        return (
            "Gemini API 配額暫時用完或被限流，已先使用 mock mode："
            f"{type(exc).__name__}: {message[:260]}"
        )
    if "api key" in lowered or "permission" in lowered or "403" in lowered or "401" in lowered:
        return (
            "Gemini API key 或權限可能需要確認，已先使用 mock mode："
            f"{type(exc).__name__}: {message[:260]}"
        )
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
        item["confidence_level"] = _clean_confidence_level(
            str(item.get("confidence_level") or ""),
            item.get("confidence"),
        )
        item["confidence"] = _confidence_value(item.get("confidence"), item["confidence_level"])
        item["evidence_count"] = _clean_evidence_count(item)
        item["evidence_sources"] = _clean_evidence_sources(item.get("evidence_sources"))
        item["evidence_quotes"] = _clean_evidence_quotes(item.get("evidence_quotes"), item.get("evidence_text"))
        item["evidence_text"] = str(item.get("evidence_text") or (item["evidence_quotes"][0] if item["evidence_quotes"] else ""))
        item["reason"] = str(item.get("reason") or item.get("reasoning_summary") or "")
        item["reasoning_summary"] = str(item.get("reasoning_summary") or item["reason"] or "需要更多觀察。")
        definition = get_strength_definition_by_name(strength_name) or {}
        item["child_friendly_feedback"] = str(
            item.get("child_friendly_feedback")
            or definition.get("child_friendly_description")
            or f"我看到你有一點「{strength_name}」的表現。"
        )
        item["teacher_facing_explanation"] = str(
            item.get("teacher_facing_explanation")
            or (
                f"此觀察依據具體行為文字與「{strength_name}」的行為描述；"
                "不是正式心理測驗結果，紀錄較少時需持續陪伴觀察。"
            )
        )
        cleaned.append(item)
        seen.add(strength_name)
        if len(cleaned) >= 2:
            break
    return cleaned


def _clean_confidence_level(value: str, confidence: Any) -> str:
    lowered = value.strip().lower()
    if lowered in {"high", "medium", "low"}:
        return lowered
    try:
        numeric = float(confidence)
    except (TypeError, ValueError):
        numeric = 0.7
    if numeric >= 0.8:
        return "high"
    if numeric >= 0.55:
        return "medium"
    return "low"


def _confidence_value(value: Any, level: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = {"high": 0.86, "medium": 0.68, "low": 0.45}.get(level, 0.68)
    return max(0.0, min(1.0, numeric))


def _clean_evidence_count(item: dict[str, Any]) -> int:
    try:
        count = int(item.get("evidence_count") or 0)
    except (TypeError, ValueError):
        count = 0
    quotes = item.get("evidence_quotes")
    if isinstance(quotes, list):
        count = max(count, len([quote for quote in quotes if str(quote).strip()]))
    if item.get("evidence_text"):
        count = max(count, 1)
    return count


def _clean_evidence_sources(value: Any) -> list[str]:
    if not isinstance(value, list):
        value = [value] if value else ["platform_interaction"]
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
    sources = []
    for source in value:
        normalized = source_map.get(str(source or "").strip(), "platform_interaction")
        if normalized in ALLOWED_EVIDENCE_SOURCES and normalized not in sources:
            sources.append(normalized)
    return sources or ["platform_interaction"]


def _clean_evidence_quotes(value: Any, fallback: Any) -> list[str]:
    quotes = value if isinstance(value, list) else []
    cleaned = []
    for quote in quotes:
        text = str(quote or "").strip()
        if text:
            cleaned.append(text[:220])
    if not cleaned and fallback:
        cleaned.append(str(fallback).strip()[:220])
    return cleaned[:3]
