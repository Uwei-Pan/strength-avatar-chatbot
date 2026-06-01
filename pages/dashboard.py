from html import escape

import streamlit as st

from database.db_connection import DatabaseConnectionError
from services.avatar_assets import (
    character_visual_html,
    get_character_profile,
    get_selected_outfit_profile,
    outfit_visual_html,
)
from services.child_service import get_child


SOURCE_LABELS = {
    "initial_profile": "初始資料",
    "counseling_record": "過去紀錄",
    "chat": "聊天",
    "diary": "心情日記",
    "journal": "心情日記",
    "todo": "任務",
    "task": "任務",
    "game": "遊戲",
    "game_reflection": "遊戲回答",
    "game_response": "遊戲回答",
    "platform_interaction": "平台互動",
}


def render() -> None:
    st.markdown('<div class="dashboard-page-scope"></div>', unsafe_allow_html=True)
    child_id = st.session_state.get("child_id")
    try:
        child = get_child(child_id)
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return

    if not child:
        st.error("找不到孩子資料，請重新登入。")
        return

    st.markdown(
        f"""
        <div class="kid-hero">
            <p class="kid-hero-title">{escape(str(child["name"]))}的優勢基地</p>
            <p class="kid-hero-copy">今天也可以慢慢收集自己的優勢力量，一次一小步就很好。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    character = get_character_profile(child.get("selected_character"))
    outfit = get_selected_outfit_profile(child)
    ability = character.get("ability") or {}
    st.markdown(
        f"""
        <div class="dashboard-stat-grid">
            <div class="dashboard-stat-card">
                <span>代幣</span>
                <strong>{escape(str(child["tokens"]))}</strong>
            </div>
            <div class="dashboard-stat-card">
                <span>角色</span>
                <strong>{escape(str(character["display_name"]))}</strong>
            </div>
            <div class="dashboard-stat-card">
                <span>服裝</span>
                <strong>{escape(str(outfit["display_name"]))}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="avatar-profile-card">
            <div class="avatar-figure">{character_visual_html(character, "is-large")}</div>
            <div>
                <span class="kid-tag {escape(character["accent"])}">{escape(character["title"])}</span>
                <h3>{escape(character["display_name"])}穿著{escape(outfit["display_name"])}</h3>
                <p>{escape(character["description"])}</p>
                <p class="gear-buff-line">角色助力：{escape(str(ability.get("ability_name") or "穩穩陪伴"))}｜{escape(str(ability.get("ability_description") or "角色會陪你一起完成挑戰。"))}</p>
                <div class="equipment-preview-card">
                    {outfit_visual_html(outfit, "is-small")}
                    <div>
                        <strong>{escape(outfit["display_name"])}</strong>
                        <p>{escape(str(outfit["short_description"]))}</p>
                        <p class="gear-buff-line">{escape(str((outfit.get("buff") or {}).get("buff_label") or "外觀裝備"))}</p>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<p class="kid-section-title">已擁有的優勢</p>', unsafe_allow_html=True)
    st.caption("這裡收藏你曾經展現過的亮點，每一次分享都會讓我們更認識你的成長。")
    unique_strengths = {}
    for item in child["owned_strengths"]:
        unique_strengths[item["name_zh"]] = item

    if unique_strengths:
        _render_strength_tags(list(unique_strengths))
        for strength in unique_strengths.values():
            st.markdown(
                f"""
                <div class="growth-story-card">
                    <strong>{escape(str(strength["name_zh"]))}</strong>
                    <p>你正在展現這個亮點，這是一段很棒的成長足跡。</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander(f"看看我的成長小故事｜{strength['name_zh']}"):
                source_label = SOURCE_LABELS.get(str(strength.get("source")), str(strength.get("source") or "其他"))
                if strength.get("evidence_text"):
                    st.write(strength["evidence_text"])
                else:
                    st.write("這個亮點正在慢慢累積更多故事。")
                st.caption(f"來源：{source_label}")
    else:
        st.info("還沒有儲存的優勢紀錄。")

def _render_strength_tags(strength_names: list[str]) -> None:
    chips = []
    color_classes = ["chip-a", "chip-b", "chip-c", "chip-d", "chip-e", "chip-f"]
    for index, name in enumerate(strength_names):
        chip_class = color_classes[index % len(color_classes)]
        chips.append(f'<span class="strength-chip {chip_class}">{escape(str(name))}</span>')
    st.markdown(
        f'<div class="kid-badge-row">{"".join(chips)}</div>',
        unsafe_allow_html=True,
    )
