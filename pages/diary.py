import json

import streamlit as st

from database.db_connection import DatabaseConnectionError
from services.child_service import get_child
from services.diary_service import create_diary_entry, list_diary_entries


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
        """
        <div class="kid-hero">
            <p class="kid-hero-title">心情日記</p>
            <p class="kid-hero-copy">記下今天的感覺和努力，小幫手會陪你一起看見優勢。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"目前代幣：{child['tokens']}")

    with st.form("diary_form", clear_on_submit=True):
        content = st.text_area(
            "今天想記下什麼？",
            height=160,
            placeholder="例如：今天最開心、最難過，或最想分享的一件小事。",
        )
        submitted = st.form_submit_button("儲存日記")

    if submitted:
        cleaned = content.strip()
        if not cleaned:
            st.warning("先寫下一點點今天的心情，再交給小幫手保存。")
        elif len(cleaned) < 3:
            st.warning("可以再多寫幾個字，讓小幫手更了解你今天的狀態。")
        else:
            try:
                result = create_diary_entry(child, cleaned)
            except DatabaseConnectionError as exc:
                st.error(str(exc))
            else:
                if int(result.get("tokens_earned") or 0) > 0:
                    st.success(f"日記已儲存，獲得 +{result['tokens_earned']} 代幣")
                else:
                    st.success("日記已儲存，謝謝你願意記錄今天。")
                for message in result.get("token_messages", [])[1:]:
                    st.caption(message)
                if result.get("mode") == "gemini":
                    st.caption("AI 小幫手已幫你整理這篇日記。")
                elif result.get("error"):
                    st.info("日記已儲存，AI 小幫手晚點再來幫你整理。")
                st.markdown(f"**小幫手：** {result['reply_to_child']}")
                if result["detected_strengths"]:
                    st.write("這篇日記裡有一些亮點：")
                    _render_strength_chips(result["detected_strengths"])

    st.markdown('<p class="kid-section-title">最近的日記</p>', unsafe_allow_html=True)
    try:
        entries = list_diary_entries(child_id)
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return

    if not entries:
        st.info("還沒有日記。")
        return

    for entry in entries:
        with st.expander(f"{entry['created_at']}｜+{entry['tokens_earned']} 代幣"):
            st.write(entry["content"])
            if entry.get("ai_reply"):
                st.markdown(f"**小幫手：** {entry['ai_reply']}")
            strengths = _parse_strengths(entry.get("detected_strengths_json"))
            if strengths:
                st.caption("優勢")
                _render_strength_chips(strengths)


def _parse_strengths(raw_value):
    if not raw_value:
        return []
    if isinstance(raw_value, list):
        return raw_value
    try:
        return json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        return []


def _render_strength_chips(strengths: list[dict]) -> None:
    cols = st.columns(min(len(strengths), 4))
    for index, strength in enumerate(strengths):
        with cols[index % len(cols)]:
            st.caption(strength.get("strength_name", "優勢"))
