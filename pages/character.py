import streamlit as st

from database.db_connection import DatabaseConnectionError
from services.child_service import get_child, update_selected_outfit


CHARACTER_LABELS = {
    "fox": "狐狸",
    "cat": "貓咪",
    "rabbit": "兔子",
}


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

    st.title("角色與服裝")
    st.metric("目前角色", CHARACTER_LABELS.get(child["selected_character"], child["selected_character"]))
    st.metric("目前服裝", child["selected_outfit"] or "尚未選擇")

    outfits = child["unlocked_outfits"]
    if not outfits:
        st.info("目前還沒有解鎖服裝。")
        return

    labels = {
        outfit["outfit_id"]: f"{outfit['display_name']} ({outfit['outfit_id']})"
        for outfit in outfits
    }
    selected = st.selectbox(
        "切換服裝",
        options=list(labels.keys()),
        format_func=lambda outfit_id: labels[outfit_id],
        index=max(
            0,
            list(labels.keys()).index(child["selected_outfit"])
            if child["selected_outfit"] in labels
            else 0,
        ),
    )
    if st.button("套用服裝", use_container_width=True):
        try:
            update_selected_outfit(child_id, selected)
        except (DatabaseConnectionError, ValueError) as exc:
            st.error(str(exc))
            return
        st.success("服裝已更新。")
        st.rerun()

    st.subheader("已解鎖")
    for outfit in outfits:
        st.write(f"**{outfit['display_name']}**")
        st.caption(f"來源：{outfit['unlocked_source']}")
