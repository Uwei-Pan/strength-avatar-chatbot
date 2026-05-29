import streamlit as st

from pages import character, chat, dashboard, diary, growth_dashboard, login, shop, snake_game, todo


PAGES = {
    "dashboard": dashboard.render,
    "growth_dashboard": growth_dashboard.render,
    "chat": chat.render,
    "snake_game": snake_game.render,
    "character": character.render,
    "diary": diary.render,
    "todo": todo.render,
    "shop": shop.render,
}

PAGE_LABELS = {
    "dashboard": "我的首頁",
    "growth_dashboard": "成長儀表板",
    "chat": "和小幫手聊聊",
    "snake_game": "遊戲樂園",
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
            for key in [
                "child_id",
                "page",
                "snake_state",
                "snake_started",
                "snake_saved",
                "snake_game",
                "block_puzzle_game",
                "current_game_type",
                "pending_reflection_question",
                "active_chat_session",
                "chat_confirm_close",
                "chat_notice",
            ]:
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

        [data-testid="stRadio"] label,
        [data-testid="stRadio"] label *,
        [data-testid="stRadio"] [role="radiogroup"] label,
        [data-testid="stRadio"] [role="radiogroup"] label * {
            color: #25306f !important;
            font-weight: 900 !important;
            opacity: 1 !important;
        }

        [data-testid="stRadio"] label:has(input:disabled),
        [data-testid="stRadio"] label:has(input:disabled) * {
            color: #25306f !important;
            opacity: 1 !important;
        }

        [data-testid="stAppViewContainer"] .main .block-container {
            padding-top: 2.2rem;
            padding-bottom: 4rem;
            max-width: min(1120px, calc(100vw - 2rem));
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
            min-width: 0;
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

        [data-testid="stTextArea"] textarea {
            padding: 0.75rem 0.9rem !important;
            line-height: 1.55 !important;
            color: #f8fafc !important;
            background: #252631 !important;
            border: 1px solid rgba(255, 255, 255, 0.18) !important;
        }

        [data-testid="stTextArea"] textarea::placeholder {
            color: #cbd5e1 !important;
            opacity: 1 !important;
        }

        .stApp:has(.todo-page-scope) [data-testid="stTextInput"] input,
        .stApp:has(.todo-page-scope) [data-testid="stTextArea"] textarea,
        .stApp:has(.todo-page-scope) [data-testid="stNumberInput"] input,
        .stApp:has(.todo-page-scope) [data-testid="stDateInput"] input,
        .stApp:has(.todo-page-scope) [data-baseweb="input"] input {
            min-height: 46px;
            padding: 0.68rem 0.85rem !important;
            border-radius: 16px !important;
            border: 1px solid rgba(72, 168, 245, 0.32) !important;
            background: #e7f5ff !important;
            color: #24345f !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72), 0 6px 16px rgba(72, 168, 245, 0.08) !important;
            caret-color: #0c63b8 !important;
        }

        .stApp:has(.todo-page-scope) [data-testid="stTextArea"] textarea {
            min-height: 92px;
            line-height: 1.55 !important;
            resize: vertical;
        }

        .stApp:has(.todo-page-scope) [data-testid="stTextInput"] input::placeholder,
        .stApp:has(.todo-page-scope) [data-testid="stTextArea"] textarea::placeholder {
            color: #6b7fa7 !important;
            opacity: 1 !important;
        }

        .stApp:has(.todo-page-scope) [data-testid="stTextInput"] input:focus,
        .stApp:has(.todo-page-scope) [data-testid="stTextArea"] textarea:focus,
        .stApp:has(.todo-page-scope) [data-testid="stNumberInput"] input:focus,
        .stApp:has(.todo-page-scope) [data-testid="stDateInput"] input:focus,
        .stApp:has(.todo-page-scope) [data-baseweb="input"] input:focus {
            border-color: rgba(12, 99, 184, 0.58) !important;
            box-shadow: 0 0 0 3px rgba(72, 168, 245, 0.16), 0 8px 18px rgba(72, 168, 245, 0.12) !important;
        }

        .stApp:has(.todo-page-scope) [data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.82);
            border-color: rgba(72, 168, 245, 0.2) !important;
        }

        [data-testid="stForm"] {
            padding: 1rem 1.05rem 0.95rem;
        }

        div[data-testid="stAlert"] {
            border-radius: 18px;
            border-width: 1px;
        }

        div[data-testid="stAlert"],
        div[data-testid="stAlert"] * {
            color: #334155 !important;
            opacity: 1 !important;
            font-weight: 800;
        }

        div[data-testid="stAlert"] p {
            line-height: 1.55;
        }

        [data-testid="stTabs"] [role="tablist"] {
            gap: 0.35rem;
            border-bottom: 1px solid rgba(255, 159, 67, 0.22);
        }

        [data-testid="stTabs"] [role="tab"] {
            padding: 0.42rem 0.85rem;
            border-radius: 14px 14px 0 0;
            color: #475569 !important;
            font-weight: 900;
            opacity: 1 !important;
        }

        [data-testid="stTabs"] [role="tab"] p,
        [data-testid="stTabs"] [role="tab"] span {
            color: inherit !important;
            font-weight: 900;
            opacity: 1 !important;
        }

        [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
            color: #c2410c !important;
            background: rgba(255, 241, 184, 0.76);
            box-shadow: inset 0 -3px 0 #ff6b35;
        }

        [data-testid="stTabs"] [role="tab"]:hover {
            color: #0f2f64 !important;
            background: rgba(255, 255, 255, 0.72);
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
            overflow-wrap: anywhere;
        }

        .kid-section-title {
            margin: 1rem 0 0.4rem;
            font-size: 1.28rem;
            font-weight: 900;
            color: var(--kid-ink);
        }

        .game-compact-hero {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.85rem 1rem;
            margin-bottom: 0.75rem;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(72, 168, 245, 0.18);
            box-shadow: var(--kid-soft-shadow);
        }

        .game-compact-title {
            margin: 0;
            font-size: 1.45rem;
            line-height: 1.2;
            font-weight: 900;
            color: var(--kid-ink);
        }

        .game-compact-copy {
            margin: 0.2rem 0 0;
            color: var(--kid-muted);
            font-size: 0.95rem;
        }

        .game-token-pill {
            flex: 0 0 auto;
            padding: 0.42rem 0.72rem;
            border-radius: 999px;
            background: #ffe16a;
            color: #303752;
            font-weight: 900;
            box-shadow: 0 6px 16px rgba(95, 111, 143, 0.12);
        }

        .game-over-card,
        .game-status-strip {
            padding: 0.95rem 1rem;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid var(--kid-border);
            box-shadow: var(--kid-soft-shadow);
            margin: 0.6rem 0 1rem;
        }

        .game-over-card {
            border-color: rgba(255, 159, 67, 0.28);
            background: linear-gradient(135deg, #fff7d6 0%, #e7f5ff 100%);
        }

        .game-status-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 0.7rem;
            align-items: center;
            color: var(--kid-muted);
            font-size: 0.94rem;
        }

        .game-status-strip span {
            display: inline-flex;
            align-items: center;
            min-height: 30px;
            padding: 0.25rem 0.55rem;
            border-radius: 999px;
            background: rgba(216, 240, 255, 0.56);
        }

        .stApp:has(.game-page-scope) [data-testid="stAppViewContainer"] .main .block-container {
            padding-top: 0.7rem;
            padding-bottom: 1.5rem;
            max-width: min(980px, calc(100vw - 1.2rem));
        }

        .stApp:has(.game-page-scope) .game-compact-hero {
            padding: 0.5rem 0.75rem;
            margin-bottom: 0.35rem;
            border-radius: 16px;
        }

        .stApp:has(.game-page-scope) .game-compact-title {
            font-size: 1.22rem;
        }

        .stApp:has(.game-page-scope) .game-compact-copy {
            margin-top: 0.05rem;
            font-size: 0.84rem;
            line-height: 1.35;
        }

        .stApp:has(.game-page-scope) .game-token-pill {
            padding: 0.3rem 0.58rem;
            font-size: 0.9rem;
        }

        .stApp:has(.game-page-scope) .kid-section-title {
            margin: 0.35rem 0 0.2rem;
            font-size: 1.05rem;
            line-height: 1.25;
        }

        .stApp:has(.game-page-scope) .kid-card {
            padding: 0.62rem 0.78rem;
            margin: 0.25rem 0 0.45rem;
            border-radius: 16px;
            line-height: 1.5;
        }

        .game-toolbar-buff {
            display: flex;
            align-items: center;
            min-height: 34px;
            padding: 0.3rem 0.7rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.84);
            border: 1px solid rgba(72, 168, 245, 0.18);
            box-shadow: 0 6px 16px rgba(95, 111, 143, 0.1);
            color: var(--kid-muted);
            font-size: 0.9rem;
            font-weight: 800;
            line-height: 1.2;
            white-space: nowrap;
            overflow-x: auto;
            overflow-y: hidden;
            -webkit-overflow-scrolling: touch;
        }

        .game-toolbar-buff strong {
            flex: 0 0 auto;
            margin-left: 0.25rem;
            color: var(--kid-ink);
        }

        .stApp:has(.game-page-scope) .game-status-strip {
            flex-wrap: nowrap;
            gap: 0.35rem;
            margin: 0.28rem 0 0.45rem;
            padding: 0.4rem 0.5rem;
            border-radius: 16px;
            overflow-x: auto;
            overflow-y: hidden;
            -webkit-overflow-scrolling: touch;
            font-size: 0.8rem;
        }

        .stApp:has(.game-page-scope) .game-status-strip span,
        .stApp:has(.game-page-scope) .gear-buff-pill {
            flex: 0 0 auto;
            min-height: 26px;
            padding: 0.18rem 0.45rem;
            white-space: nowrap;
            line-height: 1.2;
        }

        .stApp:has(.game-page-scope) [data-testid="stRadio"] {
            margin-bottom: -0.25rem;
        }

        .stApp:has(.game-page-scope) .stButton button {
            min-height: 40px;
            border-radius: 15px !important;
        }

        .avatar-profile-card,
        .character-card,
        .outfit-card,
        .shop-item-inline {
            border: 1px solid var(--kid-border);
            background: rgba(255, 255, 255, 0.86);
            box-shadow: var(--kid-soft-shadow);
        }

        .avatar-profile-card {
            display: grid;
            grid-template-columns: 112px minmax(0, 1fr);
            gap: 1rem;
            align-items: center;
            padding: 1rem;
            border-radius: 22px;
            margin: 0.8rem 0 1rem;
        }

        .avatar-figure {
            display: grid;
            place-items: center;
            min-height: 112px;
            border-radius: 20px;
            background: linear-gradient(135deg, #fff1b8 0%, #d8f0ff 100%);
        }

        .avatar-profile-card h3 {
            margin: 0.35rem 0;
            font-size: 1.25rem;
        }

        .avatar-profile-card p,
        .character-card p,
        .outfit-card p,
        .shop-item-inline p {
            margin: 0.25rem 0;
            color: var(--kid-muted);
            line-height: 1.55;
        }

        .character-card,
        .outfit-card {
            min-height: 220px;
            padding: 0.85rem;
            border-radius: 18px;
            margin-bottom: 0.55rem;
        }

        .character-emoji,
        .outfit-icon {
            display: grid;
            place-items: center;
            width: 58px;
            height: 58px;
            border-radius: 18px;
            margin-bottom: 0.45rem;
            background: linear-gradient(135deg, #fff7d6 0%, #e7f5ff 100%);
            font-size: 2rem;
        }

        .growth-hero {
            display: grid;
            grid-template-columns: 150px minmax(0, 1fr);
            gap: 1.1rem;
            align-items: center;
            padding: 1.2rem 1.35rem;
            margin-bottom: 1rem;
            border-radius: 28px;
            background:
                radial-gradient(circle at 12% 12%, rgba(255, 225, 106, 0.38), transparent 32%),
                radial-gradient(circle at 92% 18%, rgba(105, 199, 121, 0.18), transparent 30%),
                linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(231, 245, 255, 0.92));
            border: 1px solid rgba(72, 168, 245, 0.18);
            box-shadow: var(--kid-shadow);
        }

        .growth-hero-visual {
            position: relative;
            min-height: 132px;
            display: grid;
            place-items: center;
            border-radius: 24px;
            background: linear-gradient(135deg, rgba(255, 241, 184, 0.88), rgba(174, 224, 255, 0.76));
            overflow: hidden;
        }

        .growth-hero-visual .gear-visual {
            position: absolute;
            right: 14px;
            bottom: 10px;
            width: 54px;
            height: 54px;
        }

        .growth-summary-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin: 0.75rem 0 1rem;
        }

        .growth-summary-strip span,
        .gear-buff-pill {
            display: inline-flex;
            align-items: center;
            min-height: 34px;
            padding: 0.34rem 0.7rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(72, 168, 245, 0.18);
            box-shadow: 0 6px 16px rgba(95, 111, 143, 0.1);
            color: var(--kid-muted);
            font-weight: 800;
        }

        .growth-summary-strip strong,
        .gear-buff-pill strong {
            color: var(--kid-ink);
            margin-left: 0.2rem;
        }

        .growth-chart-card,
        .growth-story-card {
            border: 1px solid var(--kid-border);
            box-shadow: var(--kid-soft-shadow);
        }

        .growth-chart-card {
            padding: 0.8rem 0.85rem;
            margin: 0.45rem 0 1rem;
            border-radius: 28px;
            overflow-x: auto;
            overflow-y: hidden;
            -webkit-overflow-scrolling: touch;
            background:
                radial-gradient(circle at 12% 14%, rgba(255, 181, 84, 0.16), transparent 30%),
                radial-gradient(circle at 86% 18%, rgba(255, 224, 138, 0.1), transparent 28%),
                #11141d;
            border-color: rgba(255, 190, 118, 0.22);
        }

        .growth-story-card {
            padding: 0.85rem 1rem;
            margin: 0.55rem 0 0.25rem;
            border-radius: 22px;
            background:
                radial-gradient(circle at 8% 16%, rgba(255, 225, 106, 0.26), transparent 28%),
                linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(231, 245, 255, 0.86));
        }

        .growth-story-card strong {
            display: block;
            color: var(--kid-ink);
            font-size: 1.05rem;
            font-weight: 900;
        }

        .growth-story-card p {
            margin: 0.25rem 0 0;
            color: var(--kid-muted);
        }

        .character-visual,
        .gear-visual {
            position: relative;
            display: block;
            isolation: isolate;
            flex: 0 0 auto;
        }

        .character-visual {
            width: 90px;
            height: 98px;
            margin: 0 auto 0.55rem;
            animation: character-breathe 3.8s ease-in-out infinite;
        }

        .character-visual.is-large {
            width: 112px;
            height: 122px;
            margin-bottom: 0;
        }

        .character-visual.is-small {
            width: 58px;
            height: 64px;
            margin-bottom: 0;
        }

        .character-face-shape,
        .character-ear,
        .character-eye,
        .character-mark {
            position: absolute;
            display: block;
        }

        .character-face-shape {
            inset: 20% 10% 6%;
            border-radius: 48% 48% 42% 42%;
            background: var(--character-main, #f7a84a);
            box-shadow: inset 0 -12px 0 rgba(47, 58, 95, 0.08), 0 12px 24px rgba(95, 111, 143, 0.16);
            z-index: 2;
        }

        .character-ear {
            top: 7%;
            width: 30%;
            height: 34%;
            border-radius: 70% 70% 24% 24%;
            background: var(--character-main, #f7a84a);
            box-shadow: inset 0 -9px 0 rgba(47, 58, 95, 0.07);
            z-index: 1;
        }

        .character-ear-left {
            left: 12%;
            transform: rotate(-20deg);
        }

        .character-ear-right {
            right: 12%;
            transform: rotate(20deg);
        }

        .character-ear::after {
            content: "";
            position: absolute;
            inset: 28% 26% 20%;
            border-radius: inherit;
            background: rgba(255, 255, 255, 0.45);
        }

        .character-eye {
            top: 53%;
            width: 10%;
            height: 10%;
            border-radius: 50%;
            background: #263052;
            z-index: 3;
            box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.22);
        }

        .character-eye-left { left: 35%; }
        .character-eye-right { right: 35%; }

        .character-mark {
            left: 38%;
            right: 38%;
            bottom: 20%;
            height: 10%;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.7);
            z-index: 3;
        }

        .character-visual-fox { --character-main: #f29b3d; }
        .character-visual-rabbit { --character-main: #f7d7e6; }
        .character-visual-bear { --character-main: #b98754; }
        .character-visual-owl { --character-main: #8f82d8; }
        .character-visual-deer { --character-main: #d0a05f; }
        .character-visual-turtle { --character-main: #70ba79; }
        .character-visual-cat { --character-main: #f2b76b; }
        .character-visual-inventor { --character-main: #76c9d3; }

        .character-visual-turtle .character-face-shape {
            border-radius: 52% 52% 46% 46%;
            box-shadow: inset 0 0 0 12px rgba(255, 255, 255, 0.26), 0 12px 24px rgba(95, 111, 143, 0.16);
        }

        .character-visual-inventor .character-mark {
            left: 24%;
            right: 24%;
            top: 36%;
            bottom: auto;
            height: 7%;
            background: #2f3a5f;
        }

        .gear-visual {
            width: 66px;
            height: 66px;
            margin: 0 0 0.45rem;
            border-radius: 22px;
            background:
                radial-gradient(circle at 24% 18%, rgba(255, 255, 255, 0.82), transparent 20%),
                linear-gradient(135deg, var(--gear-bg-a, #fff1b8), var(--gear-bg-b, #aee0ff));
            box-shadow: 0 10px 22px rgba(95, 111, 143, 0.14);
            overflow: hidden;
            animation: gear-float 3.2s ease-in-out infinite;
        }

        .gear-visual.is-small {
            width: 58px;
            height: 58px;
        }

        .gear-visual.is-mini {
            width: 48px;
            height: 48px;
        }

        .gear-aura,
        .gear-core,
        .gear-detail,
        .gear-spark {
            position: absolute;
            display: block;
        }

        .gear-aura {
            inset: 10%;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.22);
            filter: blur(3px);
            animation: gear-glow 2.4s ease-in-out infinite;
        }

        .gear-core {
            left: 24%;
            right: 24%;
            top: 20%;
            bottom: 20%;
            border-radius: 16px;
            background: var(--gear-main, #ff9f43);
            box-shadow: inset 0 -7px 0 rgba(47, 58, 95, 0.12), 0 8px 16px rgba(95, 111, 143, 0.14);
            z-index: 2;
        }

        .gear-detail {
            z-index: 3;
            background: rgba(255, 255, 255, 0.78);
        }

        .gear-detail-one {
            left: 30%;
            right: 30%;
            top: 45%;
            height: 9%;
            border-radius: 999px;
        }

        .gear-detail-two {
            left: 42%;
            right: 42%;
            top: 28%;
            bottom: 28%;
            border-radius: 999px;
        }

        .gear-spark {
            width: 10%;
            height: 10%;
            border-radius: 50%;
            background: #fff7a8;
            box-shadow: 0 0 12px rgba(255, 247, 168, 0.9);
            z-index: 4;
        }

        .gear-spark-one { left: 16%; top: 20%; }
        .gear-spark-two { right: 16%; bottom: 18%; animation-delay: 400ms; }

        .gear-visual-scarf { --gear-main: #ff7aa6; --gear-bg-a: #fff1b8; --gear-bg-b: #ffd3e6; }
        .gear-visual-scarf .gear-core {
            left: 17%;
            right: 17%;
            top: 42%;
            bottom: 34%;
            border-radius: 999px;
        }
        .gear-visual-scarf .gear-detail-two {
            left: 58%;
            right: 23%;
            top: 47%;
            bottom: 14%;
            transform: rotate(-16deg);
            background: var(--gear-main);
        }

        .gear-visual-brush { --gear-main: #6ac7ff; --gear-bg-a: #e7f5ff; --gear-bg-b: #ffc1dc; }
        .gear-visual-brush .gear-core {
            left: 24%;
            right: 24%;
            top: 18%;
            bottom: 16%;
            border-radius: 999px;
            transform: rotate(34deg);
        }
        .gear-visual-brush .gear-detail-one {
            left: 19%;
            right: 49%;
            top: 61%;
            height: 18%;
            border-radius: 70% 20% 70% 20%;
            background: #ffe16a;
        }

        .gear-visual-hat { --gear-main: #6d5ad7; --gear-bg-a: #eadfff; --gear-bg-b: #aee0ff; }
        .gear-visual-hat .gear-core {
            left: 28%;
            right: 28%;
            top: 18%;
            bottom: 30%;
            border-radius: 12px 12px 6px 6px;
        }
        .gear-visual-hat .gear-detail-one {
            left: 16%;
            right: 16%;
            top: 58%;
            height: 13%;
            background: #ffe16a;
        }

        .gear-visual-lens,
        .gear-visual-glasses { --gear-main: #48a8f5; --gear-bg-a: #d8f0ff; --gear-bg-b: #fff1b8; }
        .gear-visual-lens .gear-core,
        .gear-visual-glasses .gear-core {
            left: 24%;
            right: 24%;
            top: 22%;
            bottom: 28%;
            border: 5px solid var(--gear-main);
            background: rgba(255, 255, 255, 0.5);
            border-radius: 50%;
        }
        .gear-visual-lens .gear-detail-two,
        .gear-visual-glasses .gear-detail-two {
            left: 60%;
            right: 20%;
            top: 62%;
            bottom: 21%;
            transform: rotate(42deg);
            background: var(--gear-main);
        }

        .gear-visual-map { --gear-main: #69c779; --gear-bg-a: #fff7d6; --gear-bg-b: #d5f8df; }
        .gear-visual-map .gear-core {
            left: 19%;
            right: 19%;
            top: 22%;
            bottom: 22%;
            border-radius: 10px;
            transform: rotate(-4deg);
        }

        .gear-visual-cape,
        .gear-visual-cloak { --gear-main: #ff8a4f; --gear-bg-a: #fff1b8; --gear-bg-b: #ffd1a3; }
        .gear-visual-cape .gear-core,
        .gear-visual-cloak .gear-core {
            left: 24%;
            right: 24%;
            top: 18%;
            bottom: 14%;
            clip-path: polygon(20% 0, 80% 0, 100% 100%, 0 100%);
            border-radius: 8px;
        }

        .gear-visual-boots { --gear-main: #8a694a; --gear-bg-a: #fff1b8; --gear-bg-b: #d5f8df; }
        .gear-visual-boots .gear-core {
            left: 18%;
            right: 18%;
            top: 46%;
            bottom: 22%;
            border-radius: 8px 8px 14px 14px;
        }
        .gear-visual-boots .gear-detail-two {
            left: 48%;
            right: 46%;
            top: 43%;
            bottom: 22%;
            background: rgba(255, 255, 255, 0.45);
        }

        .gear-visual-shield { --gear-main: #69c779; --gear-bg-a: #d8f0ff; --gear-bg-b: #d5f8df; }
        .gear-visual-shield .gear-core {
            left: 24%;
            right: 24%;
            top: 18%;
            bottom: 18%;
            clip-path: polygon(50% 0, 86% 16%, 78% 74%, 50% 100%, 22% 74%, 14% 16%);
            border-radius: 8px;
        }

        .gear-visual-star { --gear-main: #ffcc3d; --gear-bg-a: #fff7d6; --gear-bg-b: #eadfff; }
        .gear-visual-star .gear-core {
            left: 24%;
            right: 24%;
            top: 22%;
            bottom: 22%;
            clip-path: polygon(50% 0, 61% 34%, 98% 34%, 68% 55%, 79% 91%, 50% 70%, 21% 91%, 32% 55%, 2% 34%, 39% 34%);
        }

        .gear-visual-lantern { --gear-main: #ff9f43; --gear-bg-a: #fff1b8; --gear-bg-b: #ffd1a3; }
        .gear-visual-camera { --gear-main: #7fc8ff; --gear-bg-a: #e7f5ff; --gear-bg-b: #ffc1dc; }
        .gear-visual-flag { --gear-main: #ff6b6b; --gear-bg-a: #fff1b8; --gear-bg-b: #ffd1a3; }
        .gear-visual-flag .gear-core {
            left: 30%;
            right: 25%;
            top: 18%;
            bottom: 42%;
            border-radius: 8px 12px 12px 8px;
        }
        .gear-visual-flag .gear-detail-two {
            left: 28%;
            right: 65%;
            top: 18%;
            bottom: 16%;
            background: #2f3a5f;
        }

        .gear-visual-leaf { --gear-main: #69c779; --gear-bg-a: #d5f8df; --gear-bg-b: #fff1b8; }
        .gear-visual-leaf .gear-core {
            border-radius: 80% 8% 80% 8%;
            transform: rotate(45deg);
        }

        .gear-visual-scale,
        .gear-visual-bridge,
        .gear-visual-badge,
        .gear-visual-pin,
        .gear-visual-patch,
        .gear-visual-button { --gear-main: #a98bff; --gear-bg-a: #eadfff; --gear-bg-b: #d8f0ff; }

        .outfit-card,
        .shop-item-inline,
        .character-card {
            transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
        }

        .outfit-card:hover,
        .shop-item-inline:hover,
        .character-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 14px 28px rgba(95, 111, 143, 0.16);
        }

        .outfit-card.is-equipped,
        .shop-item-inline.is-equipped {
            border-color: rgba(255, 159, 67, 0.62);
            box-shadow: 0 0 0 3px rgba(255, 225, 106, 0.32), var(--kid-soft-shadow);
            background: linear-gradient(135deg, rgba(255, 247, 214, 0.92), rgba(231, 245, 255, 0.9));
        }

        .gear-buff-line {
            margin-top: 0.45rem !important;
            color: #0c63b8 !important;
            font-weight: 900;
        }

        .equipment-preview-card {
            display: grid;
            grid-template-columns: 72px minmax(0, 1fr);
            gap: 0.8rem;
            align-items: center;
            padding: 0.85rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid rgba(72, 168, 245, 0.18);
            box-shadow: var(--kid-soft-shadow);
            margin: 0.5rem 0 0.85rem;
        }

        @keyframes character-breathe {
            0%, 100% { transform: translateY(0) scale(1); }
            50% { transform: translateY(-3px) scale(1.015); }
        }

        @keyframes gear-float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-4px); }
        }

        @keyframes gear-glow {
            0%, 100% { opacity: 0.45; transform: scale(0.92); }
            50% { opacity: 0.75; transform: scale(1.08); }
        }

        .character-card strong,
        .outfit-card strong,
        .shop-item-inline strong {
            display: block;
            color: var(--kid-ink);
            font-size: 1.05rem;
            line-height: 1.35;
        }

        .character-card > span {
            display: block;
            margin-top: 0.15rem;
            color: #0c63b8;
            font-weight: 900;
            line-height: 1.35;
        }

        .shop-item-inline {
            display: grid;
            grid-template-columns: 70px minmax(0, 1fr);
            gap: 0.75rem;
            align-items: start;
            padding: 0.8rem;
            border-radius: 18px;
            box-shadow: none;
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

        .shop-status-available {
            background: #fff1b8;
            color: #9a3412 !important;
            border-color: rgba(255, 159, 67, 0.36);
        }

        .shop-status-owned {
            background: #dcfce7;
            color: #166534 !important;
            border-color: rgba(22, 101, 52, 0.2);
        }

        .chat-message-row {
            display: flex;
            width: 100%;
            margin: 0.38rem 0;
        }

        .chat-message-row.is-user {
            justify-content: flex-end;
        }

        .chat-message-row.is-ai {
            justify-content: flex-start;
        }

        .chat-bubble {
            width: max-content;
            max-width: min(68%, 720px);
            box-sizing: border-box;
            padding: 0.62rem 0.85rem;
            border-radius: 20px;
            margin: 0;
            line-height: 1.58;
            box-shadow: var(--kid-soft-shadow);
            border: 1px solid rgba(255, 255, 255, 0.75);
            white-space: normal;
            overflow-wrap: break-word;
            word-break: normal;
            color: #263052;
        }

        .chat-bubble-user {
            background: linear-gradient(135deg, #aee0ff 0%, #9debc0 100%);
        }

        .chat-bubble-ai {
            background: linear-gradient(135deg, #fff1b8 0%, #ffe0c2 55%, #eadfff 100%);
        }

        .chat-name {
            display: block;
            margin-bottom: 0.2rem;
            font-size: 0.86rem;
            font-weight: 900;
            color: rgba(47, 58, 95, 0.78);
        }

        .chat-text {
            display: block;
            white-space: pre-wrap;
        }

        .chat-confirm-card,
        .game-exit-notice {
            padding: 0.85rem 1rem;
            border-radius: 18px;
            border: 1px solid rgba(255, 159, 67, 0.26);
            box-shadow: var(--kid-soft-shadow);
            line-height: 1.6;
            font-weight: 900;
        }

        .chat-confirm-card {
            margin: 0.6rem 0 0.7rem;
            background: linear-gradient(135deg, rgba(255, 247, 214, 0.92), rgba(255, 225, 194, 0.78));
            color: #92400e;
        }

        .game-exit-notice {
            display: flex;
            align-items: center;
            gap: 0.65rem;
            margin: 0.65rem 0 0.85rem;
            background: linear-gradient(135deg, rgba(220, 252, 231, 0.92), rgba(209, 250, 229, 0.78));
            border-color: rgba(22, 101, 52, 0.18);
            color: #166534;
        }

        .game-exit-notice .notice-mark {
            width: 1.1rem;
            height: 1.1rem;
            border-radius: 999px;
            background: #22c55e;
            box-shadow: inset 0 0 0 4px rgba(255, 255, 255, 0.72);
            flex: 0 0 auto;
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

        .block-piece-row {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            margin: 0.75rem 0 1rem;
        }

        .block-piece-card {
            min-height: 118px;
            padding: 0.8rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.82);
            border: 2px solid rgba(72, 168, 245, 0.2);
            box-shadow: var(--kid-soft-shadow);
        }

        .block-piece-card.active {
            border-color: #ff9f43;
            background: linear-gradient(135deg, #fff7d6 0%, #e7f5ff 100%);
        }

        .block-piece-grid {
            display: inline-grid;
            gap: 4px;
            margin-top: 0.55rem;
        }

        .block-piece-grid-row {
            display: flex;
            gap: 4px;
            min-height: 22px;
        }

        .block-piece-grid span {
            width: 22px;
            height: 22px;
            border-radius: 7px;
            border: 1px solid rgba(47, 58, 95, 0.12);
            box-shadow: inset 0 -3px 0 rgba(47, 58, 95, 0.12);
        }

        .block-piece-grid span.ghost {
            border-color: transparent;
            box-shadow: none;
        }

        iframe,
        canvas,
        svg,
        img {
            max-width: 100%;
        }

        [data-testid="stDataFrame"] {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }

        @media (max-width: 900px) {
            [data-testid="stAppViewContainer"] .main .block-container {
                padding-top: 1.35rem;
                max-width: calc(100vw - 1.5rem);
            }

            .kid-hero-title {
                font-size: 1.85rem;
            }

            .growth-hero {
                grid-template-columns: 118px minmax(0, 1fr);
            }

            .game-compact-hero {
                align-items: flex-start;
            }

            .chat-bubble {
                max-width: min(78%, 640px);
            }
        }

        @media (max-width: 640px) {
            [data-testid="stAppViewContainer"] .main .block-container {
                padding-left: 0.85rem;
                padding-right: 0.85rem;
                max-width: 100vw;
            }

            [data-testid="stSidebar"] [role="radiogroup"] label,
            .stButton button,
            [data-testid="stFormSubmitButton"] button {
                min-height: 48px;
            }

            .stApp:has(.game-page-scope) .stButton button {
                min-height: 44px;
                font-size: 0.88rem;
            }

            .kid-hero {
                padding: 1rem;
                border-radius: 22px;
            }

            .kid-hero-title,
            h1 {
                font-size: 1.7rem;
                line-height: 1.2;
            }

            .kid-hero-copy {
                font-size: 0.98rem;
            }

            .game-compact-hero,
            .growth-hero,
            .avatar-profile-card,
            .equipment-preview-card,
            .shop-item-inline {
                grid-template-columns: 1fr;
                display: grid;
            }

            .game-compact-hero {
                gap: 0.65rem;
                padding: 0.85rem;
            }

            .game-compact-title {
                font-size: 1.25rem;
            }

            .game-token-pill {
                width: fit-content;
            }

            .growth-hero-visual {
                min-height: 108px;
            }

            .avatar-profile-card {
                gap: 0.75rem;
            }

            .character-card,
            .outfit-card {
                min-height: auto;
            }

            .strength-chip,
            .kid-tag {
                min-height: 32px;
                font-size: 0.88rem;
                padding: 0.3rem 0.58rem;
            }

            .chat-bubble {
                max-width: 94%;
                padding: 0.58rem 0.78rem;
            }

            .chat-message-row {
                margin: 0.3rem 0;
            }

            .thinking-card {
                width: 100%;
                box-sizing: border-box;
            }

            .block-piece-row {
                grid-template-columns: 1fr;
            }

            [data-testid="stTabs"] [role="tablist"] {
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
            }
        }

        @media (max-width: 430px) {
            [data-testid="stAppViewContainer"] .main .block-container {
                padding-left: 0.65rem;
                padding-right: 0.65rem;
            }

            .kid-hero,
            .kid-card,
            [data-testid="stMetric"],
            .game-over-card,
            .game-status-strip,
            .growth-story-card,
            .growth-chart-card {
                border-radius: 16px;
            }

            .growth-chart-card {
                padding: 0.55rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
