import streamlit as st

from database.db_connection import DatabaseConnectionError
from services.child_service import authenticate_child


def render() -> None:
    st.title("優勢探索小幫手")
    st.caption("請用試用帳號登入")

    with st.form("login_form"):
        username = st.text_input("帳號", value="studentB")
        password = st.text_input("密碼", type="password", value="1234")
        submitted = st.form_submit_button("登入")

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

    st.divider()
    st.write("帳號為你的名字：試用版為`student字母`，密碼都是 `1234`。")
