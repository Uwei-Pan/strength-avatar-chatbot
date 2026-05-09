import streamlit as st

from database.db_connection import DatabaseConnectionError
from games.snake import new_game, render_cells, step, turn
from services.child_service import get_child
from services.game_service import finish_game, start_game
from services.strength_service import get_strength_context_for_game
from services.token_service import InsufficientTokensError


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

    st.title("優勢果實貪吃蛇")
    st.caption("開始遊戲需要 5 代幣，分數達 30 可獲得 10 代幣。")
    st.metric("目前代幣", child["tokens"])

    if "snake_state" not in st.session_state:
        st.session_state["snake_state"] = None
    if "snake_started" not in st.session_state:
        st.session_state["snake_started"] = False
    if "snake_saved" not in st.session_state:
        st.session_state["snake_saved"] = False

    if not st.session_state["snake_started"]:
        if st.button("開始遊戲", use_container_width=True):
            try:
                start_game(child_id)
            except InsufficientTokensError as exc:
                st.error(str(exc))
                return
            except DatabaseConnectionError as exc:
                st.error(str(exc))
                return
            st.session_state["snake_state"] = new_game()
            st.session_state["snake_started"] = True
            st.session_state["snake_saved"] = False
            st.rerun()
        return

    state = st.session_state["snake_state"]
    st.metric("分數", state["score"])
    _render_board(state)

    direction_cols = st.columns([1, 1, 1])
    with direction_cols[1]:
        if st.button("↑", use_container_width=True):
            _move("UP")
    left_right = st.columns([1, 1, 1])
    with left_right[0]:
        if st.button("←", use_container_width=True):
            _move("LEFT")
    with left_right[1]:
        if st.button("前進", use_container_width=True):
            _move(state["direction"])
    with left_right[2]:
        if st.button("→", use_container_width=True):
            _move("RIGHT")
    with direction_cols[1]:
        if st.button("↓", use_container_width=True):
            _move("DOWN")

    fruit = state["fruit"]
    st.info(f"目前果實：{fruit['fruit_name']}（{fruit['strength_name']}）")

    last_message = state.get("last_message")
    if isinstance(last_message, dict):
        try:
            context = get_strength_context_for_game(child_id, last_message["strength_name"])
            st.success(context["message"])
        except DatabaseConnectionError as exc:
            st.error(str(exc))

    if state["game_over"]:
        st.warning("遊戲結束")
        _finish_current_game(child_id, state)
    elif st.button("結束並儲存本局", use_container_width=True):
        state["game_over"] = True
        _finish_current_game(child_id, state)
        st.rerun()


def _move(direction: str) -> None:
    state = st.session_state["snake_state"]
    turn(state, direction)
    step(state)
    st.session_state["snake_state"] = state
    st.rerun()


def _render_board(state: dict) -> None:
    cells = render_cells(state)
    html_rows = []
    for row in cells:
        html_cells = "".join(f"<td>{cell}</td>" for cell in row)
        html_rows.append(f"<tr>{html_cells}</tr>")
    html = f"""
    <style>
    .snake-board table {{
        border-collapse: collapse;
        width: min(92vw, 420px);
        aspect-ratio: 1 / 1;
        table-layout: fixed;
        background: #f6fbf5;
    }}
    .snake-board td {{
        border: 1px solid #d6e6d2;
        text-align: center;
        vertical-align: middle;
        font-size: 22px;
        color: #245b35;
        width: 10%;
        height: 10%;
    }}
    </style>
    <div class="snake-board"><table>{"".join(html_rows)}</table></div>
    """
    st.html(html)
def _finish_current_game(child_id: str, state: dict) -> None:
    if st.session_state.get("snake_saved"):
        return
    try:
        result = finish_game(child_id, state["score"], state["fruits_eaten"])
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return

    st.session_state["snake_saved"] = True
    st.session_state["snake_started"] = False
    st.session_state["snake_state"] = None
    if result["tokens_earned"]:
        st.success(f"本局獲得 +{result['tokens_earned']} 代幣")
    else:
        st.info("本局已儲存，分數達 30 就能拿到獎勵。")
