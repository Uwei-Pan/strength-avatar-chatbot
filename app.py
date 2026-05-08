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
    "dashboard": "Dashboard",
    "chat": "Chat",
    "snake_game": "Snake Game",
    "character": "Character / Outfit",
    "diary": "Diary",
    "todo": "Todo List",
    "shop": "Shop",
}


def main() -> None:
    st.set_page_config(page_title="兒少優勢探索 AI", page_icon="★", layout="wide")
    _inject_style()

    if "page" not in st.session_state:
        st.session_state["page"] = "dashboard"

    if not st.session_state.get("child_id"):
        login.render()
        return

    with st.sidebar:
        st.title("優勢探索")
        for page_key, label in PAGE_LABELS.items():
            if st.button(label, use_container_width=True):
                st.session_state["page"] = page_key
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
