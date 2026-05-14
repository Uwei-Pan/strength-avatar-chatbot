import json
from html import escape

import streamlit as st

from database.db_connection import DatabaseConnectionError
from services.ai_service import analyze_child_message
from services.child_service import get_child
from services.strength_service import list_chat_logs, save_chat_log, save_child_strength
from services.token_service import award_chat_tokens


SUGGESTION_GROUPS = {
    "心情陪伴": [
        "我今天心情不太好，可以陪我聊聊嗎？",
        "我今天有點生氣，可以怎麼辦？",
        "可以鼓勵我一下嗎？",
    ],
    "優勢探索": [
        "我今天做了一件很棒的事！",
        "你覺得我有哪些優勢？",
        "我想知道我過去展現過哪些優點。",
    ],
    "人際困擾": [
        "我不知道怎麼跟同學相處，可以給我建議嗎？",
    ],
    "每日小任務": [
        "請給我一個小任務，讓我練習自己的優勢。",
    ],
}


def render() -> None:
    child_id = st.session_state.get("child_id")
    try:
        child = get_child(child_id)
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return

    if not child:
        st.error("請先登入。")
        return

    st.markdown(
        f"""
        <div class="kid-hero">
            <p class="kid-hero-title">和 AI 夥伴聊聊</p>
            <p class="kid-hero-copy">{escape(str(child["name"]))}，你可以說心情、困擾、也可以分享今天做得很棒的小事。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"目前代幣：{child['tokens']}")

    notice = st.session_state.pop("chat_notice", None)
    if notice:
        notice_type = notice.get("type", "success")
        text = notice.get("text", "")
        if notice_type == "warning":
            st.warning(text)
        else:
            st.success(text)

    _render_suggestions(child)
    _render_chat_history(child_id)

    with st.form("chat_form", clear_on_submit=True):
        message = st.text_area(
            "你想分享什麼？",
            height=140,
            placeholder="可以慢慢說，例如：我今天有點緊張，或我今天幫了同學。",
        )
        submitted = st.form_submit_button("送出給 AI 夥伴", use_container_width=True)

    if submitted:
        cleaned = message.strip()
        if not cleaned:
            st.warning("可以先打幾個字，慢慢說就好。")
            return

        if _submit_message(child, cleaned):
            st.rerun()


def _submit_message(child: dict, cleaned: str) -> bool:
    child_id = child["child_id"]
    loading_slot = st.empty()
    with loading_slot.container():
        st.markdown(
            """
            <div class="thinking-card">
                <span class="thinking-dots"><span></span><span></span><span></span></span>
                <span>AI 夥伴正在想一想，幫你整理回覆...</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.spinner("正在幫你整理回覆，請等一下喔！"):
        result = analyze_child_message(child, cleaned)
        tokens_earned = 0
        try:
            if result["should_award_tokens"]:
                award_chat_tokens(child_id)
                tokens_earned = result["tokens_earned"]

            save_chat_log(
                child_id=child_id,
                user_message=cleaned,
                ai_reply=result["reply_to_child"],
                emotion=result["emotion"],
                detected_strengths=result["detected_strengths"],
                tokens_earned=tokens_earned,
            )

            for strength in result["detected_strengths"]:
                save_child_strength(
                    child_id=child_id,
                    strength_name=strength["strength_name"],
                    source="chat",
                    evidence_text=strength.get("evidence_text") or cleaned,
                    confidence=float(strength.get("confidence") or 0.7),
                )
        except DatabaseConnectionError as exc:
            loading_slot.empty()
            st.error(str(exc))
            return False

    loading_slot.empty()
    if result.get("mode") == "gemini":
        st.session_state["chat_notice"] = {
            "type": "success",
            "text": f"AI 夥伴回覆完成，獲得 +{tokens_earned} 代幣。",
        }
    else:
        st.session_state["chat_notice"] = {
            "type": "warning",
            "text": f"智慧小幫手暫時連不上，先用練習回覆陪你聊。獲得 +{tokens_earned} 代幣。",
        }
    return True


def _render_suggestions(child: dict) -> None:
    st.markdown('<p class="kid-section-title">可以點一個主題開始</p>', unsafe_allow_html=True)
    for category, prompts in SUGGESTION_GROUPS.items():
        st.markdown(f'<div class="prompt-category">{escape(category)}</div>', unsafe_allow_html=True)
        cols = st.columns(2)
        for index, prompt in enumerate(prompts):
            with cols[index % 2]:
                label = _short_prompt_label(prompt)
                if st.button(label, key=f"prompt_{category}_{index}", use_container_width=True):
                    if _submit_message(child, prompt):
                        st.rerun()


def _render_chat_history(child_id: str) -> None:
    st.markdown('<p class="kid-section-title">聊天小窗</p>', unsafe_allow_html=True)
    try:
        logs = list_chat_logs(child_id, limit=8)
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return

    if not logs:
        st.markdown(
            """
            <div class="kid-card">
                這裡還沒有聊天紀錄。你可以按上面的提示語，也可以自己打字告訴 AI 夥伴今天發生了什麼。
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for log in reversed(logs):
        _render_bubble("user", "你", log.get("user_message", ""))
        _render_bubble("ai", "AI 夥伴", log.get("ai_reply", ""))
        strengths = _parse_strengths(log.get("detected_strengths_json"))
        if strengths:
            _render_strength_chips(strengths)


def _render_bubble(role: str, name: str, content: str) -> None:
    bubble_class = "chat-bubble-user" if role == "user" else "chat-bubble-ai"
    st.markdown(
        f"""
        <div class="chat-bubble {bubble_class}">
            <span class="chat-name">{escape(name)}</span>
            {escape(str(content))}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _parse_strengths(raw_value) -> list[dict]:
    if not raw_value:
        return []
    if isinstance(raw_value, list):
        return raw_value
    try:
        return json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        return []


def _render_strength_chips(strengths: list[dict]) -> None:
    color_classes = ["chip-a", "chip-b", "chip-c", "chip-d", "chip-e", "chip-f"]
    chips = []
    for index, strength in enumerate(strengths):
        strength_name = strength.get("strength_name", "優勢")
        reason = strength.get("reason", "")
        chip_class = color_classes[index % len(color_classes)]
        chips.append(
            f'<span class="strength-chip {chip_class}" title="{escape(str(reason))}">'
            f'{escape(str(strength_name))}</span>'
        )
    st.markdown(f'<div class="kid-badge-row">{"".join(chips)}</div>', unsafe_allow_html=True)


def _short_prompt_label(prompt: str) -> str:
    labels = {
        "我今天心情不太好，可以陪我聊聊嗎？": "心情不太好，想聊聊",
        "我今天做了一件很棒的事！": "分享一件很棒的事",
        "你覺得我有哪些優勢？": "看看我的優勢",
        "我不知道怎麼跟同學相處，可以給我建議嗎？": "同學相處的小建議",
        "我今天有點生氣，可以怎麼辦？": "生氣時可以怎麼辦",
        "請給我一個小任務，讓我練習自己的優勢。": "給我一個優勢小任務",
        "我想知道我過去展現過哪些優點。": "回顧過去的優點",
        "可以鼓勵我一下嗎？": "鼓勵我一下",
    }
    return labels.get(prompt, prompt)
