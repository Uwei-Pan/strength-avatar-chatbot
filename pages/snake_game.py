import time

import streamlit as st
import streamlit.components.v1 as components

from database.db_connection import DatabaseConnectionError
from games.snake import SPEED_INTERVALS, new_game, render_cells, step, toggle_pause, turn
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

    # ── session-state defaults ────────────────────────────────────────────────
    st.session_state.setdefault("snake_state", None)
    st.session_state.setdefault("snake_started", False)
    st.session_state.setdefault("snake_saved", False)
    st.session_state.setdefault("snake_speed", "普通")

    # ── start screen ──────────────────────────────────────────────────────────
    if not st.session_state["snake_started"]:
        st.markdown(
            """
            <div class="kid-hero">
                <p class="kid-hero-title">優勢果實遊戲</p>
                <p class="kid-hero-copy">吃到果實時，看看它和你的哪一種優勢力量有關。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("開始遊戲需要 5 代幣，分數達 30 可獲得 10 代幣。")
        st.metric("目前代幣", child["tokens"])
        speed = st.radio(
            "速度",
            list(SPEED_INTERVALS.keys()),
            index=list(SPEED_INTERVALS.keys()).index(st.session_state["snake_speed"]),
            horizontal=True,
        )
        st.session_state["snake_speed"] = speed
        if st.button("開始遊戲", use_container_width=True):
            _start_new_game(child_id)
        return

    # ── active game ───────────────────────────────────────────────────────────
    state    = st.session_state["snake_state"]
    paused   = state.get("paused", False)
    gameover = state.get("game_over", False)
    disabled = gameover or paused

    # Keyboard listener (arrow keys → direction buttons)
    _inject_keyboard_listener()

    # ── two-column layout: board | controls ───────────────────────────────────
    board_col, ctrl_col = st.columns([5, 3])

    with board_col:
        _render_board(state)

    with ctrl_col:
        # Score
        st.metric("分數", state["score"])

        # ── D-pad (cross shape) + pause in centre ─────────────────────────────
        # Row 1 — ↑
        _, m, _ = st.columns(3)
        with m:
            if st.button("↑", use_container_width=True, key="btn_up", disabled=disabled):
                _queue_direction("UP")

        # Row 2 — ← ⏸/▶ →
        cl, cm, cr = st.columns(3)
        with cl:
            if st.button("←", use_container_width=True, key="btn_left", disabled=disabled):
                _queue_direction("LEFT")
        with cm:
            pause_icon = "▶" if paused else "⏸"
            if st.button(pause_icon, use_container_width=True, key="btn_pause", disabled=gameover):
                toggle_pause(state)
                st.session_state["snake_state"] = state
                st.rerun()
        with cr:
            if st.button("→", use_container_width=True, key="btn_right", disabled=disabled):
                _queue_direction("RIGHT")

        # Row 3 — ↓
        _, m, _ = st.columns(3)
        with m:
            if st.button("↓", use_container_width=True, key="btn_down", disabled=disabled):
                _queue_direction("DOWN")

        st.markdown("<div style='margin:8px 0;border-top:1px solid #e0e0e0'></div>",
                    unsafe_allow_html=True)

        # ── restart | save ────────────────────────────────────────────────────
        rc1, rc2 = st.columns(2)
        with rc1:
            if st.button("🔄 重來", use_container_width=True):
                if not st.session_state.get("snake_saved"):
                    try:
                        finish_game(child_id, state["score"], state["fruits_eaten"])
                    except DatabaseConnectionError:
                        pass
                _start_new_game(child_id)
        with rc2:
            if not gameover:
                if st.button("💾 儲存", use_container_width=True):
                    state["game_over"] = True
                    _finish_current_game(child_id, state)
                    st.rerun()

    # ── fruit legend + strength message ───────────────────────────────────────
    _render_fruits_info(state["fruits"])

    last_message = state.get("last_message")
    if isinstance(last_message, dict):
        try:
            context = get_strength_context_for_game(child_id, last_message["strength_name"])
            st.success(context["message"])
        except DatabaseConnectionError as exc:
            st.error(str(exc))

    # ── game-over auto-save / auto-advance ────────────────────────────────────
    if gameover:
        _finish_current_game(child_id, state)
    elif not paused:
        interval = SPEED_INTERVALS[st.session_state["snake_speed"]]
        time.sleep(interval)
        step(state)
        st.session_state["snake_state"] = state
        st.rerun()


# ── helpers ───────────────────────────────────────────────────────────────────

def _start_new_game(child_id: str) -> None:
    try:
        start_game(child_id)
    except InsufficientTokensError as exc:
        st.error(str(exc))
        return
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return
    st.session_state["snake_state"]   = new_game()
    st.session_state["snake_started"] = True
    st.session_state["snake_saved"]   = False
    st.rerun()


def _queue_direction(direction: str) -> None:
    state = st.session_state["snake_state"]
    turn(state, direction)
    step(state)
    st.session_state["snake_state"] = state
    st.rerun()


def _inject_keyboard_listener() -> None:
    """Arrow keys → click the matching visible d-pad button."""
    components.html(
        """
        <script>
        (function () {
            var p = window.parent;
            if (p._snakeKbHandler) {
                p.document.removeEventListener('keydown', p._snakeKbHandler);
            }
            var KEY_MAP = {
                ArrowUp:    '\u2191',
                ArrowDown:  '\u2193',
                ArrowLeft:  '\u2190',
                ArrowRight: '\u2192',
            };
            p._snakeKbHandler = function (e) {
                var label = KEY_MAP[e.key];
                if (!label) return;
                e.preventDefault();
                var btns = p.document.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].innerText.trim() === label && !btns[i].disabled) {
                        btns[i].click();
                        return;
                    }
                }
            };
            p.document.addEventListener('keydown', p._snakeKbHandler);
        })();
        </script>
        """,
        height=1,
    )


def _render_fruits_info(fruits: list[dict]) -> None:
    from games.snake import STRENGTH_EMOJIS
    chips = "".join(
        f'<span class="fruit-chip">'
        f'{STRENGTH_EMOJIS.get(f["strength_name"], "◆")} {f["fruit_name"]}'
        f'</span>'
        for f in fruits
    )
    st.html(f"""
        <style>
        .fruit-chips-wrap {{
            display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0;
        }}
        .fruit-chip {{
            background: #e8f5e9; border: 1px solid #a5d6a7;
            border-radius: 20px; padding: 4px 12px;
            font-size: 13px; color: #2e7d4f; font-weight: 600;
        }}
        </style>
        <div class="fruit-chips-wrap">{chips}</div>
    """)


def _render_board(state: dict) -> None:
    cells    = render_cells(state)
    paused   = state.get("paused", False)
    gameover = state.get("game_over", False)

    html_rows: list[str] = []
    for row in cells:
        tds = ""
        for cell in row:
            t        = cell["type"]
            content  = cell.get("content", "")
            connects = cell.get("connects", set())
            if t in ("head", "body", "tail"):
                cc = " ".join(f"conn-{s}" for s in connects)
                tds += f'<td class="sc s-{t} {cc}"><span>{content or "&nbsp;"}</span></td>'
            elif t == "fruit":
                tds += f'<td class="sc s-fruit"><span>{content}</span></td>'
            else:
                tds += "<td><span>&nbsp;</span></td>"
        html_rows.append(f"<tr>{tds}</tr>")

    overlay = ""
    if paused:
        overlay = '<div class="board-overlay">⏸ 暫停中</div>'
    elif gameover:
        overlay = '<div class="board-overlay game-over-text">遊戲結束<br>按 🔄 重來</div>'

    st.html(f"""
    <style>
    .snake-wrap {{
        position: relative;
        width: 100%;
        aspect-ratio: 1 / 1;
        max-width: 480px;
    }}
    .snake-board {{ width: 100%; height: 100%; }}
    .snake-board table {{
        border-collapse: collapse;
        width: 100%; height: 100%;
        table-layout: fixed;
        background: #f0f7ee;
    }}
    .snake-board td {{
        border: 1px solid #c8dfc4;
        text-align: center; vertical-align: middle;
        font-size: clamp(12px, 2vw, 20px);
        width: 10%; height: 10%; padding: 0; overflow: hidden;
    }}
    .snake-board span {{
        display: inline-flex; align-items: center;
        justify-content: center; width: 100%; height: 100%; line-height: 1;
    }}
    .sc {{ background:#388e3c; border:2px solid #388e3c !important; color:#fff; font-weight:700; }}
    .s-head {{ background:#1b5e20; border-color:#1b5e20 !important; font-size:clamp(10px,1.8vw,16px); }}
    .s-tail {{ background:#66bb6a; border-color:#66bb6a !important; }}
    .s-head.conn-up    {{ border-top-color:#1b5e20    !important; }}
    .s-head.conn-down  {{ border-bottom-color:#1b5e20 !important; }}
    .s-head.conn-left  {{ border-left-color:#1b5e20   !important; }}
    .s-head.conn-right {{ border-right-color:#1b5e20  !important; }}
    .s-body.conn-up    {{ border-top-color:#388e3c    !important; }}
    .s-body.conn-down  {{ border-bottom-color:#388e3c !important; }}
    .s-body.conn-left  {{ border-left-color:#388e3c   !important; }}
    .s-body.conn-right {{ border-right-color:#388e3c  !important; }}
    .s-tail.conn-up    {{ border-top-color:#66bb6a    !important; }}
    .s-tail.conn-down  {{ border-bottom-color:#66bb6a !important; }}
    .s-tail.conn-left  {{ border-left-color:#66bb6a   !important; }}
    .s-tail.conn-right {{ border-right-color:#66bb6a  !important; }}
    .s-fruit {{ background:#fffde7; border:1px solid #f9a825 !important; font-size:clamp(12px,2vw,20px); }}
    .board-overlay {{
        position:absolute; inset:0; display:flex; flex-direction:column;
        align-items:center; justify-content:center;
        background:rgba(240,247,238,0.82); font-size:clamp(16px,2vw,22px);
        font-weight:700; color:#245b35; pointer-events:none;
        border-radius:4px; text-align:center; gap:6px;
    }}
    .game-over-text {{ color:#b71c1c; background:rgba(255,235,235,0.85); }}
    </style>
    <div class="snake-wrap">
        <div class="snake-board"><table>{"".join(html_rows)}</table></div>
        {overlay}
    </div>
    """)


def _finish_current_game(child_id: str, state: dict) -> None:
    if st.session_state.get("snake_saved"):
        return
    try:
        result = finish_game(child_id, state["score"], state["fruits_eaten"])
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return
    st.session_state["snake_saved"]   = True
    st.session_state["snake_started"] = False
    st.session_state["snake_state"]   = None
    if result["tokens_earned"]:
        st.success(f"本局獲得 +{result['tokens_earned']} 代幣")
    else:
        st.info("本局已儲存，分數達 30 就能拿到獎勵。")