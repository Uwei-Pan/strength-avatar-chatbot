import streamlit as st

from database.db_connection import DatabaseConnectionError
from services.child_service import get_child


CHARACTER_LABELS = {
    "fox": "狐狸",
    "cat": "貓咪",
    "rabbit": "兔子",
    "inventor": "小小發明家",
}


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
    col2.metric("角色", CHARACTER_LABELS.get(child["selected_character"], child["selected_character"]))
    col3.metric("服裝", _selected_outfit_name(child))

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
        st.info("還沒有儲存的優勢紀錄。")


def _selected_outfit_name(child: dict) -> str:
    selected = child.get("selected_outfit")
    for outfit in child.get("unlocked_outfits", []):
        if outfit["outfit_id"] == selected:
            return outfit["display_name"]
    return "尚未選擇"
