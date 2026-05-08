import streamlit as st

from database.db_connection import DatabaseConnectionError
from services.child_service import get_child
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

    st.title("商城")
    st.caption(f"目前代幣：{child['tokens']}")

    owned = [item for item in outfits if item["is_owned"]]
    available = [item for item in outfits if not item["is_owned"]]

    tab_shop, tab_owned = st.tabs(["可購買", "已擁有"])

    with tab_shop:
        if not available:
            st.info("目前所有服裝都已解鎖。")
        for outfit in available:
            with st.container(border=True):
                cols = st.columns([4, 1, 1])
                with cols[0]:
                    st.write(f"**{outfit['display_name']}**")
                    detail = outfit["outfit_id"]
                    if outfit.get("strength_name"):
                        detail += f"｜相關優勢：{outfit['strength_name']}"
                    st.caption(detail)
                with cols[1]:
                    st.metric("價格", int(outfit["cost"]))
                with cols[2]:
                    if st.button("購買", key=f"buy_{outfit['outfit_id']}", use_container_width=True):
                        try:
                            purchase_outfit(child_id, outfit["outfit_id"])
                        except (DatabaseConnectionError, InsufficientTokensError, ValueError) as exc:
                            st.error(str(exc))
                        else:
                            st.success("購買成功，已解鎖服裝。")
                            st.rerun()

    with tab_owned:
        if not owned:
            st.info("目前還沒有服裝。")
        for outfit in owned:
            with st.container(border=True):
                st.write(f"**{outfit['display_name']}**")
                caption = outfit["outfit_id"]
                if outfit.get("strength_name"):
                    caption += f"｜相關優勢：{outfit['strength_name']}"
                st.caption(caption)
