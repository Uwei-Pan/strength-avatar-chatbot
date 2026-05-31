from html import escape

import streamlit as st

from database.db_connection import DatabaseConnectionError
from services.avatar_assets import get_outfit_profile, outfit_visual_html
from services.child_service import get_child, update_selected_outfit
from services.shop_service import list_shop_outfits, purchase_outfit
from services.token_service import InsufficientTokensError


def render() -> None:
    child_id = st.session_state.get("child_id")
    try:
        child = get_child(child_id)
        outfits = list_shop_outfits(child_id)
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return

    if not child:
        st.error("請先登入。")
        return

    st.markdown(
        """
        <div class="kid-hero">
            <p class="kid-hero-title">服裝商店</p>
            <p class="kid-hero-copy">用努力收集到的代幣，替角色解鎖新的冒險造型。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"目前代幣：{child['tokens']}")

    owned = [item for item in outfits if item["is_owned"]]
    available = [item for item in outfits if not item["is_owned"]]

    tab_shop, tab_owned = st.tabs(["可購買", "已擁有"])

    with tab_shop:
        if not available:
            st.info("目前所有服裝都已解鎖。")
        for outfit in available:
            _render_shop_item(child_id, outfit)

    with tab_owned:
        if not owned:
            st.info("目前還沒有服裝。")
        for outfit in owned:
            _render_owned_item(child_id, outfit, equipped=outfit.get("outfit_id") == child.get("selected_outfit"))


def _render_shop_item(child_id: str, outfit: dict) -> None:
    profile = get_outfit_profile(outfit)
    strength = profile.get("strength_name") or "自由搭配"
    buff = profile.get("buff") or {}
    with st.container(border=True):
        cols = st.columns([4, 1])
        with cols[0]:
            st.markdown(
                f"""
                <div class="shop-item-inline">
                    {outfit_visual_html(profile, "is-small")}
                    <div>
                        <strong>{escape(str(profile["display_name"]))}</strong>
                        <p>{escape(str(profile["short_description"]))}</p>
                        <p class="gear-buff-line">{escape(str(buff.get("buff_label") or "外觀裝備"))}</p>
                        <span class="kid-tag shop-status-available">可購買</span>
                        <span class="kid-tag {escape(str(profile["accent"]))}">優勢：{escape(str(strength))}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with cols[1]:
            st.metric("價格", int(outfit["cost"]))
            if st.button("購買", key=f"buy_{outfit['outfit_id']}", use_container_width=True):
                try:
                    purchase_outfit(child_id, outfit["outfit_id"])
                except (DatabaseConnectionError, InsufficientTokensError, ValueError) as exc:
                    st.error(str(exc))
                else:
                    st.success("購買成功，已解鎖服裝。")
                    st.rerun()


def _render_owned_item(child_id: str, outfit: dict, *, equipped: bool = False) -> None:
    profile = get_outfit_profile(outfit)
    strength = profile.get("strength_name") or "自由搭配"
    buff = profile.get("buff") or {}
    equipped_class = " is-equipped" if equipped else ""
    with st.container(border=True):
        cols = st.columns([4, 1])
        with cols[0]:
            st.markdown(
                f"""
                <div class="shop-item-inline{equipped_class}">
                    {outfit_visual_html(profile, "is-small")}
                    <div>
                        <strong>{escape(str(profile["display_name"]))}</strong>
                        <p>{escape(str(profile["short_description"]))}</p>
                        <p class="gear-buff-line">{escape(str(buff.get("buff_label") or "外觀裝備"))}</p>
                        <span class="kid-tag {escape(str(profile["accent"]))}">優勢：{escape(str(strength))}</span>
                        <span class="kid-tag shop-status-owned">已擁有</span>
                        {('<span class="kid-tag chip-a">目前裝備中</span>' if equipped else '')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with cols[1]:
            if st.button(
                "已裝備" if equipped else "裝備",
                key=f"shop_equip_{outfit['outfit_id']}",
                disabled=equipped,
                use_container_width=True,
            ):
                try:
                    update_selected_outfit(child_id, outfit["outfit_id"])
                except (DatabaseConnectionError, ValueError) as exc:
                    st.error(str(exc))
                    return
                st.success("服裝已更新。")
                st.rerun()
