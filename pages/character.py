from html import escape

import streamlit as st

from database.db_connection import DatabaseConnectionError
from services.child_service import get_child, update_selected_character, update_selected_outfit


CHARACTER_LABELS = {
    "fox": "狐狸",
    "cat": "貓咪",
    "rabbit": "兔子",
    "inventor": "小小發明家",
}

CHARACTER_OPTIONS = ["fox", "cat", "rabbit", "inventor"]


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
            <p class="kid-hero-title">角色與服裝</p>
            <p class="kid-hero-copy">幫你的優勢角色換上喜歡的樣子，讓每一次練習都更有自己的風格。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.metric("目前角色", CHARACTER_LABELS.get(child["selected_character"], child["selected_character"]))
    st.metric("目前服裝", _selected_outfit_name(child))

    st.markdown('<p class="kid-section-title">選擇角色</p>', unsafe_allow_html=True)
    character_cols = st.columns(len(CHARACTER_OPTIONS))
    for index, character_key in enumerate(CHARACTER_OPTIONS):
        with character_cols[index]:
            label = CHARACTER_LABELS.get(character_key, character_key)
            disabled = child["selected_character"] == character_key
            if st.button(label, key=f"character_{character_key}", disabled=disabled, use_container_width=True):
                try:
                    update_selected_character(child_id, character_key)
                except DatabaseConnectionError as exc:
                    st.error(str(exc))
                    return
                st.success("角色已更新。")
                st.rerun()

    outfits = child["unlocked_outfits"]
    if not outfits:
        st.info("目前還沒有解鎖服裝。")
        return

    labels = {
        outfit["outfit_id"]: outfit["display_name"]
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

    st.markdown('<p class="kid-section-title">已解鎖</p>', unsafe_allow_html=True)
    for outfit in outfits:
        st.markdown(
            f"""
            <div class="kid-card">
                <strong>{escape(str(outfit["display_name"]))}</strong><br>
                <span class="kid-tag chip-b">解鎖方式：{escape(_source_label(outfit["unlocked_source"]))}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _source_label(source: str) -> str:
    labels = {
        "seed": "一開始就擁有",
        "counseling_record": "從過去的優勢紀錄解鎖",
        "chat": "聊天時發現優勢",
        "diary": "日記裡發現優勢",
        "shop_purchase": "在商店購買",
    }
    return labels.get(source, "已解鎖")


def _selected_outfit_name(child: dict) -> str:
    selected = child.get("selected_outfit")
    for outfit in child.get("unlocked_outfits", []):
        if outfit["outfit_id"] == selected:
            return outfit["display_name"]
    return "尚未選擇"
