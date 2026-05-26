import streamlit as st

from database.db_connection import DatabaseConnectionError
from services.child_service import authenticate_child


def render() -> None:
    st.markdown(
        """
        <div class="kid-hero">
            <p class="kid-hero-title">優勢探索小幫手</p>
            <p class="kid-hero-copy">登入你的優勢基地，和 AI 夥伴一起記下今天的小發現。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        username = st.text_input("帳號", value="studentB", placeholder="例如：studentB")
        password = st.text_input("密碼", type="password", value="1234", placeholder="請輸入你的密碼")
        submitted = st.form_submit_button("進入我的基地", use_container_width=True)

    if submitted:
        try:
            child = authenticate_child(username, password)
        except DatabaseConnectionError as exc:
            st.error(str(exc))
            st.info("請先設定 .env 並執行 `python database/init_db.py`。")
            return

        if not child:
            st.error("帳號或密碼不正確。")
            return

        st.session_state["child_id"] = child["child_id"]
        st.session_state["page"] = "dashboard"
        st.rerun()

    st.markdown(
        """
        <div class="kid-card">
            帳號是學生姓名，試用版可以輸入
            <span class="kid-tag chip-c">studentB</span>
            <span class="kid-tag chip-d">studentC</span>
            <span class="kid-tag chip-e">studentD</span>
            這類格式；例如 <span class="kid-tag chip-c">studentB</span>。密碼都是
            <span class="kid-tag chip-a">1234</span>。
        </div>
        """,
        unsafe_allow_html=True,
    )
