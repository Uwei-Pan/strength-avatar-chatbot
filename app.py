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
        :root {
            --kid-cream: #fff7d6;
            --kid-sky: #d8f0ff;
            --kid-blue: #48a8f5;
            --kid-orange: #ff9f43;
            --kid-green: #69c779;
            --kid-pink: #ff8fc3;
            --kid-purple: #a98bff;
            --kid-yellow: #ffe16a;
            --kid-card: rgba(255, 255, 255, 0.9);
            --kid-ink: #2f3a5f;
            --kid-muted: #65718e;
            --kid-border: rgba(72, 168, 245, 0.18);
            --kid-shadow: 0 18px 45px rgba(95, 111, 143, 0.16);
            --kid-soft-shadow: 0 10px 26px rgba(95, 111, 143, 0.12);
        }

        .stApp {
            color: var(--kid-ink);
            background:
                linear-gradient(135deg, rgba(255, 247, 214, 0.98) 0%, rgba(216, 240, 255, 0.96) 54%, rgba(235, 229, 255, 0.92) 100%),
                repeating-linear-gradient(45deg, rgba(255, 255, 255, 0.22) 0 12px, rgba(255, 255, 255, 0) 12px 24px);
        }

        [data-testid="stHeader"] {
            background: rgba(255, 247, 214, 0.58);
            backdrop-filter: blur(12px);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #fff8dc 0%, #e1f4ff 58%, #f3ecff 100%);
            border-right: 1px solid rgba(72, 168, 245, 0.18);
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: var(--kid-ink);
        }

        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span {
            color: #25306f !important;
            font-weight: 800;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label {
            border-radius: 16px;
            padding: 0.35rem 0.45rem;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            background: rgba(255, 255, 255, 0.52);
        }

        [data-testid="stSidebar"] [role="radio"][aria-checked="true"] span,
        [data-testid="stSidebar"] [role="radio"][aria-checked="true"] p {
            color: #0c63b8 !important;
            font-weight: 900;
        }

        [data-testid="stAppViewContainer"] .main .block-container {
            padding-top: 2.2rem;
            padding-bottom: 4rem;
            max-width: 1120px;
        }

        h1, h2, h3 {
            color: var(--kid-ink);
            letter-spacing: 0;
        }

        h1 {
            font-size: clamp(2rem, 3.1vw, 3.1rem);
            line-height: 1.15;
        }

        p, li, label, textarea, input, .stMarkdown {
            line-height: 1.75;
        }

        .stButton button,
        [data-testid="stFormSubmitButton"] button,
        button[kind="primary"],
        button[kind="secondary"],
        button[kind="tertiary"] {
            min-height: 44px;
            border: 0 !important;
            border-radius: 18px !important;
            color: #172060 !important;
            background: linear-gradient(180deg, #fff5bc 0%, #ffb554 100%) !important;
            box-shadow: 0 8px 0 #dc7b28, var(--kid-soft-shadow) !important;
            font-weight: 900 !important;
            text-shadow: 0 1px 0 rgba(255, 255, 255, 0.5);
            transition: transform 150ms ease, box-shadow 150ms ease, filter 150ms ease;
        }

        .stButton button *,
        [data-testid="stFormSubmitButton"] button *,
        button[kind="primary"] *,
        button[kind="secondary"] *,
        button[kind="tertiary"] * {
            color: #172060 !important;
            font-weight: 900;
        }

        .stButton button:hover,
        [data-testid="stFormSubmitButton"] button:hover,
        button[kind="primary"]:hover,
        button[kind="secondary"]:hover,
        button[kind="tertiary"]:hover {
            transform: translateY(-2px);
            filter: saturate(1.08);
            box-shadow: 0 10px 0 #dc7b28, 0 16px 28px rgba(255, 159, 67, 0.24) !important;
        }

        .stButton button:active,
        [data-testid="stFormSubmitButton"] button:active,
        button[kind="primary"]:active,
        button[kind="secondary"]:active,
        button[kind="tertiary"]:active {
            transform: translateY(4px);
            box-shadow: 0 4px 0 #dc7b28, 0 10px 18px rgba(255, 159, 67, 0.18) !important;
        }

        .stButton button:disabled,
        [data-testid="stFormSubmitButton"] button:disabled,
        button[kind="primary"]:disabled,
        button[kind="secondary"]:disabled,
        button[kind="tertiary"]:disabled {
            background: linear-gradient(180deg, #e8f2f5 0%, #cad9df 100%) !important;
            color: #5f6b86 !important;
            box-shadow: none;
        }

        .stButton button:disabled *,
        [data-testid="stFormSubmitButton"] button:disabled *,
        button[kind="primary"]:disabled *,
        button[kind="secondary"]:disabled *,
        button[kind="tertiary"]:disabled * {
            color: #5f6b86 !important;
        }

        [data-testid="stMetric"] {
            background: var(--kid-card);
            border: 1px solid var(--kid-border);
            border-radius: 20px;
            padding: 1rem 1.1rem;
            box-shadow: var(--kid-soft-shadow);
        }

        [data-testid="stMetricLabel"] p {
            color: var(--kid-muted);
            font-weight: 700;
        }

        [data-testid="stMetricValue"] {
            color: var(--kid-ink);
        }

        [data-testid="stExpander"],
        [data-testid="stForm"],
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 22px !important;
            border-color: rgba(72, 168, 245, 0.2) !important;
            box-shadow: var(--kid-soft-shadow);
            background: rgba(255, 255, 255, 0.78);
        }

        textarea, input, [data-baseweb="select"] > div {
            border-radius: 16px !important;
        }

        div[data-testid="stAlert"] {
            border-radius: 18px;
        }

        .kid-hero {
            position: relative;
            padding: 1.25rem 1.35rem;
            margin-bottom: 1rem;
            border-radius: 28px;
            background:
                linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(255, 248, 221, 0.9)),
                linear-gradient(90deg, rgba(255, 225, 106, 0.32), rgba(72, 168, 245, 0.22));
            border: 1px solid rgba(255, 159, 67, 0.2);
            box-shadow: var(--kid-shadow);
        }

        .kid-hero-title {
            margin: 0;
            font-size: clamp(2rem, 3vw, 3.1rem);
            line-height: 1.16;
            font-weight: 900;
            color: var(--kid-ink);
        }

        .kid-hero-copy {
            margin: 0.45rem 0 0;
            color: var(--kid-muted);
            font-size: 1.05rem;
        }

        .kid-card {
            padding: 1rem 1.1rem;
            border-radius: 22px;
            background: var(--kid-card);
            border: 1px solid var(--kid-border);
            box-shadow: var(--kid-soft-shadow);
            margin: 0.45rem 0 1rem;
        }

        .kid-section-title {
            margin: 1.25rem 0 0.5rem;
            font-size: 1.28rem;
            font-weight: 900;
            color: var(--kid-ink);
        }

        .kid-badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin: 0.5rem 0 0.25rem;
        }

        .strength-chip,
        .kid-tag {
            display: inline-flex;
            align-items: center;
            min-height: 34px;
            padding: 0.35rem 0.72rem;
            border-radius: 999px;
            font-size: 0.94rem;
            font-weight: 800;
            color: #303752;
            border: 1px solid rgba(255, 255, 255, 0.74);
            box-shadow: 0 6px 16px rgba(95, 111, 143, 0.12);
            margin: 0.18rem 0.26rem 0.18rem 0;
        }

        .chip-a { background: #ffe16a; }
        .chip-b { background: #9debc0; }
        .chip-c { background: #aee0ff; }
        .chip-d { background: #ffc1dc; }
        .chip-e { background: #d8cbff; }
        .chip-f { background: #ffd1a3; }

        .chat-bubble {
            width: fit-content;
            max-width: min(760px, 92%);
            padding: 0.85rem 1rem;
            border-radius: 22px;
            margin: 0.55rem 0;
            line-height: 1.75;
            box-shadow: var(--kid-soft-shadow);
            border: 1px solid rgba(255, 255, 255, 0.75);
            white-space: pre-wrap;
        }

        .chat-bubble-user {
            margin-left: auto;
            background: linear-gradient(135deg, #aee0ff 0%, #9debc0 100%);
        }

        .chat-bubble-ai {
            margin-right: auto;
            background: linear-gradient(135deg, #fff1b8 0%, #ffe0c2 55%, #eadfff 100%);
        }

        .chat-name {
            display: block;
            margin-bottom: 0.2rem;
            font-size: 0.86rem;
            font-weight: 900;
            color: rgba(47, 58, 95, 0.78);
        }

        .prompt-category {
            margin: 0.75rem 0 0.35rem;
            color: var(--kid-ink);
            font-weight: 900;
        }

        .thinking-card {
            display: inline-flex;
            align-items: center;
            gap: 0.8rem;
            padding: 0.9rem 1.1rem;
            margin: 0.75rem 0;
            border-radius: 22px;
            background: linear-gradient(135deg, #fff9d7 0%, #e7f5ff 100%);
            border: 1px solid rgba(72, 168, 245, 0.2);
            box-shadow: var(--kid-soft-shadow);
            color: var(--kid-ink);
            font-weight: 800;
        }

        .thinking-dots {
            display: inline-flex;
            gap: 0.22rem;
        }

        .thinking-dots span {
            width: 0.5rem;
            height: 0.5rem;
            border-radius: 50%;
            background: var(--kid-orange);
            animation: kid-bounce 900ms ease-in-out infinite;
        }

        .thinking-dots span:nth-child(2) {
            background: var(--kid-blue);
            animation-delay: 120ms;
        }

        .thinking-dots span:nth-child(3) {
            background: var(--kid-green);
            animation-delay: 240ms;
        }

        @keyframes kid-bounce {
            0%, 80%, 100% { transform: translateY(0); opacity: 0.62; }
            40% { transform: translateY(-5px); opacity: 1; }
        }

        .snake-board {
            overflow: hidden;
            border-radius: 22px;
            box-shadow: var(--kid-shadow);
            border: 5px solid rgba(255, 255, 255, 0.88);
        }

        @media (max-width: 640px) {
            [data-testid="stAppViewContainer"] .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .kid-hero {
                padding: 1rem;
                border-radius: 22px;
            }

            .chat-bubble {
                max-width: 100%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
