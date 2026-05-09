from datetime import date

import streamlit as st

from database.db_connection import DatabaseConnectionError
from services.child_service import get_child
from services.todo_service import complete_todo, create_todo, list_todos


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

    st.title("任務小清單")
    st.caption(f"目前代幣：{child['tokens']}")

    with st.form("todo_form", clear_on_submit=True):
        title = st.text_input("任務名稱")
        description = st.text_area("補充說明", height=80)
        due_date = st.date_input("截止日期", value=None)
        reward = st.number_input("完成獎勵代幣", min_value=1, max_value=50, value=10)
        submitted = st.form_submit_button("新增任務")

    if submitted:
        if not title.strip():
            st.warning("請輸入任務名稱。")
        else:
            try:
                create_todo(
                    child_id=child_id,
                    title=title,
                    description=description,
                    due_date=due_date if isinstance(due_date, date) else None,
                    tokens_reward=int(reward),
                )
            except DatabaseConnectionError as exc:
                st.error(str(exc))
            else:
                st.success("任務已新增。")
                st.rerun()

    st.subheader("任務清單")
    try:
        todos = list_todos(child_id)
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return

    if not todos:
        st.info("目前沒有任務。")
        return

    for todo in todos:
        completed = bool(todo["is_completed"])
        label = "已完成" if completed else "進行中"
        with st.container(border=True):
            cols = st.columns([4, 1, 1])
            with cols[0]:
                st.write(f"**{todo['title']}**")
                if todo.get("description"):
                    st.caption(todo["description"])
                meta = f"{label}｜獎勵 {todo['tokens_reward']} 代幣"
                if todo.get("due_date"):
                    meta += f"｜截止 {todo['due_date']}"
                st.caption(meta)
            with cols[1]:
                st.write(label)
            with cols[2]:
                if not completed and st.button("完成", key=f"todo_done_{todo['id']}", use_container_width=True):
                    try:
                        earned = complete_todo(child_id, int(todo["id"]))
                    except (DatabaseConnectionError, ValueError) as exc:
                        st.error(str(exc))
                    else:
                        st.success(f"完成任務，獲得 +{earned} 代幣")
                        st.rerun()
