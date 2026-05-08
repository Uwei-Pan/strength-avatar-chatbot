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

    st.title("日記")
    st.caption(f"目前代幣：{child['tokens']}")

    with st.form("diary_form", clear_on_submit=True):
        content = st.text_area("今天想記下什麼？", height=160)
        submitted = st.form_submit_button("儲存日記")

    if submitted:
        cleaned = content.strip()
        if len(cleaned) < 3:
            st.warning("可以多寫一點點，讓 AI 更了解你今天的狀態。")
        else:
            try:
                result = create_diary_entry(child, cleaned)
            except DatabaseConnectionError as exc:
                st.error(str(exc))
            else:
                st.success(f"日記已儲存，獲得 +{result['tokens_earned']} tokens")
                if result.get("mode") == "gemini":
                    st.caption("AI mode: Gemini")
                elif result.get("error"):
                    st.warning(result["error"])
                st.markdown(f"**AI：** {result['reply_to_child']}")
                if result["detected_strengths"]:
                    st.write("這篇日記可能看到：")
                    st.write("、".join(item["strength_name"] for item in result["detected_strengths"]))

    st.subheader("最近的日記")
    try:
        entries = list_diary_entries(child_id)
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return

    if not entries:
        st.info("還沒有日記。")
        return

    for entry in entries:
        with st.expander(f"{entry['created_at']}｜+{entry['tokens_earned']} tokens"):
            st.write(entry["content"])
            if entry.get("ai_reply"):
                st.markdown(f"**AI：** {entry['ai_reply']}")
            strengths = _parse_strengths(entry.get("detected_strengths_json"))
            if strengths:
                st.caption("優勢：" + "、".join(item["strength_name"] for item in strengths))


def _parse_strengths(raw_value):
    if not raw_value:
        return []
    if isinstance(raw_value, list):
        return raw_value
    try:
        return json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        return []
