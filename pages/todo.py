from datetime import date

import streamlit as st

from database.db_connection import DatabaseConnectionError
from services.child_service import get_child
from services.todo_service import complete_todo, create_todo, delete_todo, list_todos


COUNSELOR_TASK_REVIEW_PASSWORD = "1234"  # TODO: move this to environment config or counselor account permissions.


def _get_counselor_task_review_password() -> str:
    return COUNSELOR_TASK_REVIEW_PASSWORD


def render() -> None:
    _init_task_review_state()
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
            <p class="kid-hero-title">任務小清單</p>
            <p class="kid-hero-copy">把大事情拆成小任務，完成一格就是一次很棒的前進。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"目前代幣：{child['tokens']}")

    with st.form("todo_form", clear_on_submit=True):
        title = st.text_input(
            "任務名稱",
            placeholder="例如：完成數學作業、整理書包、幫忙倒垃圾",
        )
        description = st.text_area(
            "補充說明",
            height=80,
            placeholder="這個任務可以很小，只要你願意開始就很棒！",
        )
        due_date = st.date_input("截止日期", value=None)
        reward = st.number_input("完成獎勵代幣", min_value=1, max_value=50, value=10)
        submitted = st.form_submit_button("新增任務")

    if submitted:
        cleaned_title = title.strip()
        if not cleaned_title:
            st.warning("先寫下一個今天想完成的小任務。")
        else:
            st.session_state["pending_task_review"] = {
                "child_id": child_id,
                "title": cleaned_title,
                "description": description.strip(),
                "due_date": due_date if isinstance(due_date, date) else None,
                "tokens_reward": int(reward),
            }
            st.info("這個任務需要輔導員幫你確認一下喔。任務確認後，就會加入你的清單。")

    _render_pending_task_review()

    st.markdown('<p class="kid-section-title">任務清單</p>', unsafe_allow_html=True)
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
            cols = st.columns([4, 1, 1, 1])
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
                    st.session_state["pending_task_completion_review"] = {
                        "child_id": child_id,
                        "todo_id": int(todo["id"]),
                        "title": str(todo.get("title") or "任務"),
                        "tokens_reward": int(todo.get("tokens_reward") or 0),
                    }
                    st.info("這個完成紀錄需要輔導員幫你確認一下喔。")
            with cols[3]:
                if st.button("刪除", key=f"todo_delete_{todo['id']}", use_container_width=True):
                    try:
                        delete_todo(child_id, int(todo["id"]))
                    except (DatabaseConnectionError, ValueError) as exc:
                        st.error(str(exc))
                    else:
                        st.success("任務已刪除。")
                        st.rerun()

    _render_pending_task_completion_review()


def _init_task_review_state() -> None:
    st.session_state.setdefault("pending_task_review", None)
    st.session_state.setdefault("task_review_nonce", 0)
    st.session_state.setdefault("pending_task_completion_review", None)
    st.session_state.setdefault("task_completion_review_nonce", 0)


def _render_pending_task_review() -> None:
    pending = st.session_state.get("pending_task_review")
    if not isinstance(pending, dict):
        return

    st.markdown('<p class="kid-section-title">輔導員確認</p>', unsafe_allow_html=True)
    st.info("請輔導員輸入審核密碼，確認任務內容。任務確認後，就會加入你的清單。")
    with st.container(border=True):
        st.write(f"**待確認任務：** {pending.get('title', '')}")
        if pending.get("description"):
            st.caption(str(pending["description"]))
        st.caption(f"完成後獎勵：{int(pending.get('tokens_reward') or 0)} 代幣")
        password = st.text_input(
            "請輔導員輸入審核密碼",
            type="password",
            key=f"task_review_password_{st.session_state['task_review_nonce']}",
        )
        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button("確認新增", key="confirm_pending_task", use_container_width=True):
                review_password = _get_counselor_task_review_password()
                if password != review_password:
                    st.warning("密碼不正確，請再請輔導員確認一次。")
                    return
                try:
                    create_todo(
                        child_id=str(pending["child_id"]),
                        title=str(pending["title"]),
                        description=str(pending.get("description") or ""),
                        due_date=pending.get("due_date") if isinstance(pending.get("due_date"), date) else None,
                        tokens_reward=int(pending.get("tokens_reward") or 1),
                    )
                except DatabaseConnectionError as exc:
                    st.error(str(exc))
                    return
                st.session_state["pending_task_review"] = None
                st.session_state["task_review_nonce"] += 1
                st.success("任務已確認並加入清單。")
                st.rerun()
        with col_cancel:
            if st.button("先不要新增", key="cancel_pending_task", use_container_width=True):
                st.session_state["pending_task_review"] = None
                st.session_state["task_review_nonce"] += 1
                st.info("已先保留空間，之後想新增任務時再寫就好。")
                st.rerun()


def _render_pending_task_completion_review() -> None:
    pending = st.session_state.get("pending_task_completion_review")
    if not isinstance(pending, dict):
        return

    st.markdown('<p class="kid-section-title">完成確認</p>', unsafe_allow_html=True)
    st.info("請輔導員輸入審核密碼，確認這個任務已經完成。確認後，代幣才會加入。")
    with st.container(border=True):
        st.write(f"**待確認完成：** {pending.get('title', '')}")
        st.caption(f"確認後獎勵：{int(pending.get('tokens_reward') or 0)} 代幣")
        password = st.text_input(
            "請輔導員輸入完成審核密碼",
            type="password",
            key=f"task_completion_review_password_{st.session_state['task_completion_review_nonce']}",
        )
        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button("確認完成", key="confirm_pending_task_completion", use_container_width=True):
                review_password = _get_counselor_task_review_password()
                if password != review_password:
                    st.warning("密碼不正確，請再請輔導員確認一次。")
                    return
                try:
                    earned = complete_todo(str(pending["child_id"]), int(pending["todo_id"]))
                except (DatabaseConnectionError, ValueError) as exc:
                    st.error(str(exc))
                    return
                st.session_state["pending_task_completion_review"] = None
                st.session_state["task_completion_review_nonce"] += 1
                st.success(f"任務已確認完成，獲得 +{earned} 代幣")
                st.rerun()
        with col_cancel:
            if st.button("先不要完成", key="cancel_pending_task_completion", use_container_width=True):
                st.session_state["pending_task_completion_review"] = None
                st.session_state["task_completion_review_nonce"] += 1
                st.info("已先取消完成確認，可以等輔導員確認後再按一次完成。")
                st.rerun()
