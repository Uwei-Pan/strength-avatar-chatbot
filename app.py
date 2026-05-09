import streamlit as st

from pages import character, chat, dashboard, diary, login, shop, snake_game, todo


PAGES = {
    "dashboard": dashboard.render,
    "chat": chat.render,
    "snake_game": snake_game.render,
    "character": character.render,
    "diary": diary.render,
    "todo": todo.render,
    "shop": shop.render,
}

PAGE_LABELS = {
    "dashboard": "我的首頁",
    "chat": "和小幫手聊聊",
    "snake_game": "優勢果實遊戲",
    "character": "角色與服裝",
    "diary": "心情日記",
    "todo": "任務小清單",
    "shop": "服裝商店",
}


def main() -> None:
    st.set_page_config(page_title="優勢探索日記", page_icon="★", layout="wide")
    _inject_style()

    if "page" not in st.session_state:
        st.session_state["page"] = "dashboard"

    if not st.session_state.get("child_id"):
        login.render()
        return

    with st.sidebar:
        st.title("功能選單")
        current_page = st.session_state.get("page", "dashboard")
        page_keys = list(PAGE_LABELS.keys())
        selected_page = st.radio(
            "頁面",
            options=page_keys,
            format_func=lambda page_key: PAGE_LABELS[page_key],
            index=page_keys.index(current_page) if current_page in page_keys else 0,
            label_visibility="collapsed",
        )
        if selected_page != current_page:
            st.session_state["page"] = selected_page
            st.rerun()
        st.divider()
        if st.button("登出", use_container_width=True):
            for key in ["child_id", "page", "snake_state", "snake_started", "snake_saved"]:
                st.session_state.pop(key, None)
            st.rerun()

    page_key = st.session_state.get("page", "dashboard")
    render_page = PAGES.get(page_key, dashboard.render)
    render_page()


def _inject_style() -> None:
    st.markdown(
        """
        <style>
        .stButton button {
            min-height: 42px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
