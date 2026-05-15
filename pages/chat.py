import json
import uuid
from datetime import datetime
from html import escape
from typing import Any

import streamlit as st

from database.db_connection import DatabaseConnectionError
from services.ai_service import analyze_child_message
from services.chat_reward_service import evaluate_chat_token_events, token_event_total
from services.chat_session_service import list_chat_sessions, save_chat_session
from services.child_service import get_child
from services.strength_service import save_chat_log, save_child_strength
from services.token_service import award_chat_tokens


SUGGESTIONS = [
    "我今天有點不開心",
    "我今天做了一件很棒的事",
    "我想知道我的優勢",
    "可以鼓勵我一下嗎？",
    "請給我一個小任務",
]


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

    session = _get_current_session(child)
    st.markdown(
        f"""
        <div class="kid-hero">
            <p class="kid-hero-title">和 AI 夥伴聊聊</p>
            <p class="kid-hero-copy">{escape(str(child["name"]))}，這裡只會顯示本次聊天；過去紀錄收在下方，不會混在一起。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"目前代幣：{child['tokens']}｜本次 session：{session['session_id'][:8]}")

    notice = st.session_state.pop("chat_notice", None)
    if notice:
        _render_notice(notice)

    _render_current_chat(session)
    _render_input(child, session)
    _render_close_controls(child, session)
    _render_history(child["child_id"])


def _get_current_session(child: dict[str, Any]) -> dict[str, Any]:
    child_id = child["child_id"]
    session = st.session_state.get("active_chat_session")
    if not session or session.get("student_id") != child_id or session.get("closed_at"):
        session = _new_session(child_id)
        st.session_state["active_chat_session"] = session
        st.session_state["chat_confirm_close"] = False
    return session


def _new_session(child_id: str) -> dict[str, Any]:
    return {
        "session_id": str(uuid.uuid4()),
        "student_id": child_id,
        "created_at": _now_iso(),
        "closed_at": None,
        "messages": [],
        "token_events": [],
    }


def _render_current_chat(session: dict[str, Any]) -> None:
    st.markdown('<p class="kid-section-title">本次聊天</p>', unsafe_allow_html=True)
    if not session["messages"]:
        st.markdown(
            """
            <div class="kid-card">
                新的聊天已準備好。你可以先用一句話告訴 AI 夥伴今天發生了什麼，或點下面的小提示開始。
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for message in session["messages"]:
        role = message.get("role", "assistant")
        name = "你" if role == "user" else "AI 夥伴"
        _render_bubble(role, name, message.get("content", ""))
        if role == "assistant" and message.get("detected_strengths"):
            _render_strength_chips(message["detected_strengths"])


def _render_input(child: dict[str, Any], session: dict[str, Any]) -> None:
    with st.form("chat_form", clear_on_submit=True, border=False):
        message = st.text_area(
            "輸入本次想聊的內容",
            height=120,
            placeholder="例如：我今天有點生氣，因為我覺得被誤會，但我先去旁邊冷靜。",
        )
        submitted = st.form_submit_button("送出給 AI 夥伴", use_container_width=True)

    st.caption("也可以快速開始：")
    cols = st.columns(len(SUGGESTIONS))
    for index, prompt in enumerate(SUGGESTIONS):
        with cols[index]:
            if st.button(prompt, key=f"chat_suggestion_{index}", use_container_width=True):
                if _submit_message(child, session, prompt):
                    st.rerun()

    if submitted:
        cleaned = message.strip()
        if not cleaned:
            st.warning("可以先打幾個字，慢慢說就好。")
            return
        if _submit_message(child, session, cleaned):
            st.rerun()


def _submit_message(child: dict[str, Any], session: dict[str, Any], cleaned: str) -> bool:
    prior_user_messages = [
        message["content"]
        for message in session["messages"]
        if message.get("role") == "user"
    ]
    session["messages"].append({"role": "user", "content": cleaned, "created_at": _now_iso()})
    user_message_index = len(session["messages"]) - 1

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
        token_events = evaluate_chat_token_events(
            cleaned,
            result["detected_strengths"],
            prior_user_messages,
            user_message_index,
        )
        tokens_earned = token_event_total(token_events)
        if tokens_earned:
            try:
                award_chat_tokens(child["child_id"], tokens_earned)
            except DatabaseConnectionError as exc:
                loading_slot.empty()
                st.error(str(exc))
                return False

    loading_slot.empty()
    session["token_events"].extend(token_events)
    assistant_reply = _with_token_guidance(
        result["reply_to_child"],
        tokens_earned,
        token_events,
        result["emotion"],
    )
    session["messages"].append(
        {
            "role": "assistant",
            "content": assistant_reply,
            "created_at": _now_iso(),
            "emotion": result["emotion"],
            "detected_strengths": result["detected_strengths"],
            "tokens_earned": tokens_earned,
            "follow_up_question": result.get("follow_up_question", ""),
            "mode": result.get("mode", "mock"),
            "error": result.get("error", ""),
        }
    )
    st.session_state["active_chat_session"] = session
    if result.get("mode") == "gemini":
        st.session_state["chat_notice"] = {
            "type": "success",
            "text": "AI 夥伴回覆完成。",
        }
    elif result.get("error"):
        st.session_state["chat_notice"] = {
            "type": "warning",
            "text": "智慧小幫手暫時連不上，先用練習回覆陪你聊。",
        }
    return True


def _render_close_controls(child: dict[str, Any], session: dict[str, Any]) -> None:
    st.markdown('<p class="kid-section-title">結束本次聊天</p>', unsafe_allow_html=True)
    if not session["messages"]:
        st.caption("本次還沒有對話，開始聊天後就可以儲存成歷史紀錄。")
        return

    if st.button("關閉本次聊天", use_container_width=True):
        st.session_state["chat_confirm_close"] = True
        st.rerun()

    if not st.session_state.get("chat_confirm_close"):
        return

    st.warning("確定要關閉本次聊天嗎？關閉後，本次對話會儲存到歷史聊天紀錄中。")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("是，關閉並儲存", use_container_width=True):
            _close_session(child, session)
            st.rerun()
    with col_no:
        if st.button("否，繼續聊天", use_container_width=True):
            st.session_state["chat_confirm_close"] = False
            st.rerun()


def _close_session(child: dict[str, Any], session: dict[str, Any]) -> None:
    session["closed_at"] = _now_iso()
    save_chat_session(session)
    try:
        _save_session_to_legacy_chat_logs(child["child_id"], session)
        _save_detected_strengths(child["child_id"], session)
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return

    st.session_state["active_chat_session"] = _new_session(child["child_id"])
    st.session_state["chat_confirm_close"] = False
    st.session_state["chat_notice"] = {
        "type": "success",
        "text": "本次聊天已儲存到歷史紀錄，新的聊天已準備好。",
    }


def _save_session_to_legacy_chat_logs(child_id: str, session: dict[str, Any]) -> None:
    messages = session.get("messages", [])
    for index, message in enumerate(messages):
        if message.get("role") != "user":
            continue
        assistant = _next_assistant_message(messages, index)
        if not assistant:
            continue
        save_chat_log(
            child_id=child_id,
            user_message=message.get("content", ""),
            ai_reply=assistant.get("content", ""),
            emotion=assistant.get("emotion", ""),
            detected_strengths=assistant.get("detected_strengths", []),
            tokens_earned=int(assistant.get("tokens_earned", 0)),
        )


def _save_detected_strengths(child_id: str, session: dict[str, Any]) -> None:
    messages = session.get("messages", [])
    for index, message in enumerate(messages):
        if message.get("role") != "assistant":
            continue
        evidence = _previous_user_content(messages, index)
        for strength in message.get("detected_strengths", []):
            save_child_strength(
                child_id=child_id,
                strength_name=strength["strength_name"],
                source="chat",
                evidence_text=strength.get("evidence_text") or evidence,
                confidence=float(strength.get("confidence") or 0.7),
            )


def _render_history(child_id: str) -> None:
    sessions = list_chat_sessions(child_id, limit=10)
    with st.expander("歷史聊天紀錄", expanded=False):
        if not sessions:
            st.caption("目前還沒有已關閉的聊天 session。")
            return
        for session in sessions:
            label = _session_label(session)
            with st.container(border=True):
                st.write(f"**{label}**")
                st.caption(
                    f"Session：{session.get('session_id', '')[:8]}｜"
                    f"訊息 {len(session.get('messages', []))} 則｜"
                    f"代幣 +{token_event_total(session.get('token_events', []))}"
                )
                with st.expander("查看原始對話", expanded=False):
                    for message in session.get("messages", []):
                        name = "你" if message.get("role") == "user" else "AI 夥伴"
                        st.markdown(f"**{name}：** {message.get('content', '')}")


def _with_token_guidance(
    reply: str,
    tokens_earned: int,
    token_events: list[dict[str, Any]],
    emotion: str,
) -> str:
    if emotion == "需要協助":
        return reply
    if tokens_earned > 0:
        reason_text = _token_reason_text(token_events)
        return f"{reply}\n\n我看見你{reason_text}，這次你獲得了 {tokens_earned} 枚優勢代幣。"
    return (
        f"{reply}\n\n這還不太夠讓我判斷你的優勢。"
        "你可以再告訴我：當時發生了什麼事，或你做了什麼選擇嗎？"
    )


def _token_reason_text(token_events: list[dict[str, Any]]) -> str:
    labels = {
        "shared_specific_event": "分享了具體事件",
        "shared_feeling": "說出了自己的感受",
        "shared_action_or_choice": "說出了行動或選擇",
        "showed_strength": "展現了可以判斷的優勢",
        "completed_small_task": "完成了小任務或反思",
    }
    reasons = [labels.get(event.get("reason"), "認真分享") for event in token_events]
    return "、".join(dict.fromkeys(reasons))


def _render_notice(notice: dict[str, str]) -> None:
    if notice.get("type") == "warning":
        st.warning(notice.get("text", ""))
    else:
        st.success(notice.get("text", ""))


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


def _render_strength_chips(strengths: list[dict[str, Any]]) -> None:
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


def _next_assistant_message(messages: list[dict[str, Any]], start_index: int) -> dict[str, Any] | None:
    for message in messages[start_index + 1 :]:
        if message.get("role") == "assistant":
            return message
        if message.get("role") == "user":
            return None
    return None


def _previous_user_content(messages: list[dict[str, Any]], start_index: int) -> str:
    for message in reversed(messages[:start_index]):
        if message.get("role") == "user":
            return str(message.get("content", ""))
    return ""


def _session_label(session: dict[str, Any]) -> str:
    closed_at = session.get("closed_at") or session.get("created_at") or ""
    return closed_at.replace("T", " ")[:19] if closed_at else "未命名聊天"


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")
