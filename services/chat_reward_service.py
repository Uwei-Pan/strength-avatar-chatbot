import re
from typing import Any


LOW_SIGNAL_MESSAGES = {
    "嗨",
    "哈囉",
    "hi",
    "hello",
    "不知道",
    "還好",
    "沒事",
    "普通",
    "無聊",
    "拿代幣",
}

EMOTION_WORDS = [
    "開心",
    "高興",
    "難過",
    "生氣",
    "害怕",
    "緊張",
    "焦慮",
    "累",
    "委屈",
    "失望",
    "挫折",
    "被誤會",
    "不開心",
]

EVENT_WORDS = [
    "今天",
    "昨天",
    "早上",
    "下課",
    "上課",
    "同學",
    "老師",
    "家人",
    "朋友",
    "考試",
    "作業",
    "比賽",
    "發生",
    "事情",
]

ACTION_WORDS = [
    "幫",
    "撿",
    "分享",
    "安慰",
    "完成",
    "練習",
    "努力",
    "冷靜",
    "道歉",
    "選擇",
    "試著",
    "忍住",
    "告訴",
    "謝謝",
]

TASK_WORDS = [
    "小任務",
    "任務",
    "我做到了",
    "我試著",
    "我練習",
    "我完成",
]


def evaluate_chat_token_events(
    message: str,
    detected_strengths: list[dict[str, Any]],
    prior_user_messages: list[str],
    message_index: int,
) -> list[dict[str, Any]]:
    text = message.strip()
    if _is_low_signal(text) or _is_repeated(text, prior_user_messages):
        return []

    candidates: list[tuple[str, int]] = []
    if _has_specific_event(text):
        candidates.append(("shared_specific_event", 1))
    if _has_any(text, EMOTION_WORDS):
        candidates.append(("shared_feeling", 1))
    if detected_strengths:
        candidates.append(("showed_strength", 2))
    if _has_any(text, ACTION_WORDS):
        candidates.append(("shared_action_or_choice", 1))
    if _has_any(text, TASK_WORDS):
        candidates.append(("completed_small_task", 2))

    events: list[dict[str, Any]] = []
    total = 0
    for reason, tokens in candidates:
        available = 3 - total
        if available <= 0:
            break
        awarded = min(tokens, available)
        events.append(
            {
                "reason": reason,
                "tokens": awarded,
                "message_index": message_index,
            }
        )
        total += awarded
    return events


def token_event_total(events: list[dict[str, Any]]) -> int:
    return sum(int(event.get("tokens", 0)) for event in events)


def _is_low_signal(text: str) -> bool:
    normalized = _fingerprint(text)
    return len(normalized) <= 4 or normalized in {_fingerprint(item) for item in LOW_SIGNAL_MESSAGES}


def _is_repeated(text: str, prior_user_messages: list[str]) -> bool:
    current = _fingerprint(text)
    return any(_fingerprint(prior) == current for prior in prior_user_messages)


def _has_specific_event(text: str) -> bool:
    return len(text) >= 8 and _has_any(text, EVENT_WORDS) and _has_any(text, ACTION_WORDS)


def _has_any(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)


def _fingerprint(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()
