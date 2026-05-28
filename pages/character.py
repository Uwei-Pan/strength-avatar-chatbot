from html import escape

import streamlit as st

from database.db_connection import DatabaseConnectionError
from services.avatar_assets import (
    character_visual_html,
    get_character_profile,
    get_outfit_profile,
    get_selected_outfit_profile,
    list_character_profiles,
    outfit_visual_html,
)
from services.child_service import get_child, update_selected_character, update_selected_outfit


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
    current_character = get_character_profile(child.get("selected_character"))
    current_outfit = get_selected_outfit_profile(child)
    current_ability = current_character.get("ability") or {}
    st.markdown(
        f"""
        <div class="avatar-profile-card">
            <div class="avatar-figure">{character_visual_html(current_character, "is-large")}</div>
            <div>
                <span class="kid-tag {escape(current_character["accent"])}">目前角色</span>
                <h3>{escape(current_character["display_name"])}｜{escape(current_character["title"])}</h3>
                <p>{escape(current_character["description"])}</p>
                <p class="gear-buff-line">角色助力：{escape(str(current_ability.get("ability_name") or "穩穩陪伴"))}｜{escape(str(current_ability.get("ability_description") or "角色會陪你一起完成挑戰。"))}</p>
                <div class="equipment-preview-card">
                    {outfit_visual_html(current_outfit, "is-small")}
                    <div>
                        <strong>{escape(current_outfit["display_name"])}</strong>
                        <p>{escape(str(current_outfit["short_description"]))}</p>
                        <p class="gear-buff-line">{escape(str((current_outfit.get("buff") or {}).get("buff_label") or "外觀裝備"))}</p>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<p class="kid-section-title">選擇角色</p>', unsafe_allow_html=True)
    profiles = list_character_profiles()
    for row_start in range(0, len(profiles), 4):
        row_profiles = profiles[row_start : row_start + 4]
        character_cols = st.columns(len(row_profiles))
        for index, profile in enumerate(row_profiles):
            with character_cols[index]:
                disabled = child["selected_character"] == profile["key"]
                ability = profile.get("ability") or {}
                st.markdown(
                    f"""
                    <div class="character-card">
                        {character_visual_html(profile)}
                        <strong>{escape(profile["display_name"])}</strong>
                        <span>{escape(profile["title"])}</span>
                        <p>{escape(profile["description"])}</p>
                        <p class="gear-buff-line">{escape(str(ability.get("ability_name") or "穩穩陪伴"))}</p>
                        <p>{escape(str(ability.get("ability_description") or "角色會陪你一起完成挑戰。"))}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(
                    "使用中" if disabled else "選擇",
                    key=f"character_{profile['key']}",
                    disabled=disabled,
                    use_container_width=True,
                ):
                    try:
                        update_selected_character(child_id, profile["key"])
                    except DatabaseConnectionError as exc:
                        st.error(str(exc))
                        return
                    st.success("角色已更新。")
                    st.rerun()

    outfits = child["unlocked_outfits"]
    if not outfits:
        st.info("目前還沒有解鎖服裝。")
        return

    labels = {outfit["outfit_id"]: get_outfit_profile(outfit)["display_name"] for outfit in outfits}
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
    for row_start in range(0, len(outfits), 3):
        cols = st.columns(min(3, len(outfits) - row_start))
        for index, outfit in enumerate(outfits[row_start : row_start + 3]):
            with cols[index]:
                _render_outfit_card(outfit, owned=True, equipped=outfit.get("outfit_id") == child.get("selected_outfit"))


def _source_label(source: str) -> str:
    labels = {
        "seed": "一開始就擁有",
        "counseling_record": "從過去的優勢紀錄解鎖",
        "chat": "聊天時發現優勢",
        "diary": "日記裡發現優勢",
        "shop_purchase": "在商店購買",
    }
    return labels.get(source, "已解鎖")


def _render_outfit_card(outfit: dict, *, owned: bool, equipped: bool = False) -> None:
    profile = get_outfit_profile(outfit)
    strength = profile.get("strength_name") or "自由搭配"
    source = _source_label(str(profile.get("unlocked_source") or ""))
    buff = profile.get("buff") or {}
    equipped_class = " is-equipped" if equipped else ""
    st.markdown(
        f"""
        <div class="outfit-card{equipped_class}">
            {outfit_visual_html(profile)}
            <strong>{escape(str(profile["display_name"]))}</strong>
            <p>{escape(str(profile["short_description"]))}</p>
            <p class="gear-buff-line">{escape(str(buff.get("buff_label") or "外觀裝備"))}</p>
            <span class="kid-tag {escape(str(profile["accent"]))}">優勢：{escape(str(strength))}</span>
            <span class="kid-tag chip-b">{escape(source if owned else "可解鎖")}</span>
            {('<span class="kid-tag chip-a">裝備中</span>' if equipped else '')}
        </div>
        """,
        unsafe_allow_html=True,
    )
