import streamlit as st

from database.db_connection import DatabaseConnectionError
from services.ai_service import analyze_child_message
from services.child_service import get_child
from services.strength_service import save_chat_log, save_child_strength
from services.token_service import award_chat_tokens


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

    st.title("和 AI 說說今天")
    st.caption(f"目前代幣：{child['tokens']}")

    with st.form("chat_form", clear_on_submit=True):
        message = st.text_area("你想分享什麼？", height=140)
        submitted = st.form_submit_button("送出")

    if submitted:
        cleaned = message.strip()
        if not cleaned:
            st.warning("可以先打幾個字，慢慢說就好。")
            return

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
            st.error(str(exc))
            return

        st.success(f"+{tokens_earned} tokens")
        st.markdown(f"**AI：** {result['reply_to_child']}")
        if result["follow_up_question"]:
            st.write(result["follow_up_question"])
        if result["detected_strengths"]:
            st.subheader("這次可能看到的優勢")
            for strength in result["detected_strengths"]:
                st.write(
                    f"**{strength['strength_name']}** "
                    f"({float(strength.get('confidence', 0)):.2f})"
                )
                st.caption(strength.get("reason", ""))
        else:
            st.info("這次先不新增優勢標籤，只把聊天記錄存起來。")
