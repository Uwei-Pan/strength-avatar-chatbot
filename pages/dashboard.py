import streamlit as st

from database.db_connection import DatabaseConnectionError
from services.child_service import get_child


FEATURES = [
    ("Chat", "chat"),
    ("Snake Game", "snake_game"),
    ("Character / Outfit", "character"),
    ("Diary", "diary"),
    ("Todo List", "todo"),
    ("Shop", "shop"),
]


def render() -> None:
    child_id = st.session_state.get("child_id")
    try:
        child = get_child(child_id)
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return

    if not child:
        st.error("找不到孩子資料，請重新登入。")
        return

    st.title(f"{child['name']}的優勢基地")
    col1, col2, col3 = st.columns(3)
    col1.metric("代幣", child["tokens"])
    col2.metric("角色", child["selected_character"])
    col3.metric("服裝", child["selected_outfit"] or "尚未選擇")

    st.subheader("已擁有的優勢")
    unique_strengths = {}
    for item in child["owned_strengths"]:
        unique_strengths[item["name_zh"]] = item

    if unique_strengths:
        for strength in unique_strengths.values():
            with st.expander(f"{strength['name_zh']}｜{strength['category']}"):
                st.write(strength["evidence_text"])
                st.caption(f"來源：{strength['source']}")
    else:
        st.info("還沒有儲存的優勢 evidence。")

    st.subheader("功能入口")
    cols = st.columns(3)
    for index, (label, page_key) in enumerate(FEATURES):
        with cols[index % 3]:
            if st.button(label, use_container_width=True):
                st.session_state["page"] = page_key
                st.rerun()
