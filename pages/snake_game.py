import random
from html import escape
from typing import Any

import streamlit as st

from database.db_connection import DatabaseConnectionError
from games.block_component import neon_block_puzzle_game
from games.block_puzzle import (
    new_game as new_block_game,
)
from games.slither_component import slither_snake_game
from services.ai_service import validate_reflection_answer
from services.avatar_assets import (
    get_game_buff_for_child,
    get_selected_outfit_profile,
    outfit_visual_html,
)
from services.child_service import get_child
from services.game_service import (
    BLOCK_TOKEN_THRESHOLD,
    MAX_GAME_TOKENS_PER_ROUND,
    SNAKE_TOKEN_THRESHOLD,
    award_game_token_once,
    finish_game,
    new_game_id,
    save_game_reflection,
    start_game,
)
from services.token_service import GAME_START_COST, InsufficientTokensError


REFLECTION_QUESTIONS = [
    "今天讓你最開心的一件事是什麼？",
    "今天有沒有遇到困難？你怎麼面對？",
    "今天你有幫助別人嗎？可以說說看嗎？",
    "今天你有完成什麼小挑戰嗎？",
    "今天你覺得自己哪裡做得不錯？",
    "剛剛玩遊戲時，你有沒有很努力的地方？",
    "今天有沒有人對你很好？發生了什麼事？",
    "你剛剛玩遊戲輸掉時，有什麼感覺？",
    "如果再玩一次，你想用什麼策略？",
    "今天你最想謝謝誰？為什麼？",
]

REFLECTION_PLACEHOLDER = (
    "寫下你的想法後，就可以再挑戰一次！例如：我想慢慢移動，不要太急，"
    "或我剛剛雖然輸了但有努力看方向。"
)

GAME_LABELS = {
    "snake": "貪食蛇",
    "block_puzzle": "方塊消除",
}

GAME_OVER_LABELS = {
    "hit_wall": "你撞到牆壁了！",
    "hit_self": "你撞到自己了！",
    "no_valid_moves": "目前沒有方塊可以放囉！",
}


def render() -> None:
    _init_state()
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
        f"""
        <div class="game-compact-hero">
            <div>
                <p class="game-compact-title">優勢遊戲樂園</p>
                <p class="game-compact-copy">
                    開始一局需要 {GAME_START_COST} 代幣；結束後可以退出，或回答小問題再挑戰。
                </p>
            </div>
            <span class="game-token-pill">目前 {int(child["tokens"])} 代幣</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    locked_game = _locked_game_type()
    if locked_game and st.session_state.get("current_game_type") != locked_game:
        st.session_state["current_game_type"] = locked_game
        st.session_state["game_switch_notice"] = "要先結束目前這局，才能切換到另一個遊戲。"
        st.rerun()

    notice = st.session_state.pop("game_switch_notice", None)
    if notice:
        st.warning(notice, icon=":material/lock:")

    exit_notice = st.session_state.pop("game_exit_notice", None)
    if exit_notice:
        st.success(exit_notice, icon=":material/check_circle:")

    current_game = st.radio(
        "選擇遊戲",
        options=["snake", "block_puzzle"],
        format_func=lambda value: GAME_LABELS[value],
        horizontal=True,
        key="current_game_type",
        disabled=locked_game is not None,
    )

    pending = st.session_state.get("pending_reflection_question")
    if pending and pending.get("game_type") == current_game:
        _render_reflection_gate(child, pending)
        return

    if current_game == "snake":
        _render_snake(child)
    else:
        _render_block_puzzle(child)

    _render_game_status(child, current_game)


def _init_state() -> None:
    st.session_state.setdefault("current_game_type", "snake")
    st.session_state.setdefault("snake_game", None)
    st.session_state.setdefault("block_puzzle_game", None)
    st.session_state.setdefault("pending_reflection_question", None)
    st.session_state.setdefault("game_exit_notice", None)


def _locked_game_type() -> str | None:
    pending = st.session_state.get("pending_reflection_question")
    if pending:
        return str(pending.get("game_type"))
    for game_type, key in [("snake", "snake_game"), ("block_puzzle", "block_puzzle_game")]:
        state = st.session_state.get(key) or {}
        if state.get("game_over") or (state.get("started") and not state.get("completed")):
            return game_type
    return None


def _render_snake(child: dict[str, Any]) -> None:
    child_id = str(child["child_id"])
    state = st.session_state.get("snake_game")
    if not state:
        state = _new_snake_state()
        st.session_state["snake_game"] = state

    st.markdown('<p class="kid-section-title">貪食蛇：星光果實賽道</p>', unsafe_allow_html=True)
    if state.get("game_over") or state.get("completed"):
        _render_game_over_panel(state, "snake")
        return

    if not state["started"]:
        st.markdown(
            """
            <div class="kid-card">
                這一版會連續滑行，使用方向鍵或 WASD 轉向。吃到星光點心 +10；
                大顆、會移動的優勢果實 +40，結束時會幫你整理吃到哪些優勢果實。
            </div>
            """,
            unsafe_allow_html=True,
        )
        _render_equipment_preview(child, "snake")
        if st.button("開始貪食蛇", icon=":material/play_arrow:", use_container_width=True):
            if _spend_start_cost(child_id):
                st.session_state["snake_game"] = _new_snake_state(
                    started=True,
                    tokens_spent=GAME_START_COST,
                    active_buff=get_game_buff_for_child(child, "snake"),
                )
                st.rerun()
        return

    _render_running_toolbar("snake", state)

    result = slither_snake_game(
        state,
        key=f"slither_{state['game_id']}",
        on_game_over_change=lambda: None,
        on_token_award_change=lambda: None,
    )
    _handle_snake_token_event(child_id, state, _component_value(result, "token_award"))
    _handle_snake_game_over(child_id, state, _component_value(result, "game_over"))


def _new_snake_state(
    *,
    started: bool = False,
    tokens_spent: int = 0,
    active_buff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "game_id": new_game_id(),
        "started": started,
        "score": 0,
        "length": 3,
        "tokens_earned": 0,
        "awarded_thresholds": [],
        "fruits_eaten": [],
        "all_fruits_eaten": [],
        "score_bank": 0,
        "revivals_used": 0,
        "completed": False,
        "final_summary": "",
        "game_over": False,
        "game_over_reason": "",
        "saved": False,
        "tokens_spent": int(tokens_spent),
        "active_buff": active_buff or {},
    }


def _handle_snake_token_event(child_id: str, state: dict[str, Any], payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    if payload.get("game_id") != state["game_id"]:
        return
    threshold = int(payload.get("threshold") or 0)
    _award_threshold_token(
        child_id,
        state,
        game_type="snake",
        threshold=threshold,
    )
    st.session_state["snake_game"] = state


def _handle_snake_game_over(child_id: str, state: dict[str, Any], payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    if payload.get("game_id") != state["game_id"] or state.get("saved"):
        return

    state["score"] = int(payload.get("score") or 0)
    state["length"] = int(payload.get("length") or 3)
    attempt_fruits = list(payload.get("fruits_eaten") or [])
    state["fruits_eaten"] = attempt_fruits
    state.setdefault("all_fruits_eaten", []).extend(attempt_fruits)
    state["strength_summary"] = str(payload.get("strength_summary") or "")
    state["game_over"] = True
    state["game_over_reason"] = str(payload.get("game_over_reason") or "hit_wall")
    state["completed"] = True
    state["started"] = False
    state["final_summary"] = _snake_strength_summary(state.get("all_fruits_eaten", []))
    _save_finished_game(child_id, state, "snake", state.get("all_fruits_eaten", []))
    st.session_state["snake_game"] = state
    st.rerun()


def _render_block_puzzle(child: dict[str, Any]) -> None:
    child_id = str(child["child_id"])
    state = st.session_state.get("block_puzzle_game")
    if not state:
        state = _new_block_state()
        st.session_state["block_puzzle_game"] = state

    st.markdown('<p class="kid-section-title">方塊消除：彩色積木挑戰</p>', unsafe_allow_html=True)
    if state.get("game_over") or state.get("completed"):
        _render_game_over_panel(state, "block_puzzle")
        return

    if not state.get("started"):
        st.markdown(
            """
            <div class="kid-card">
                選一個方塊，再點棋盤上的放置位置。填滿整列或整行就會消除加分；
                當三個方塊都放不下時，就要先回答小問題才能再來一局。
            </div>
            """,
            unsafe_allow_html=True,
        )
        _render_equipment_preview(child, "block_puzzle")
        if st.button("開始方塊消除", icon=":material/play_arrow:", use_container_width=True):
            if _spend_start_cost(child_id):
                st.session_state["block_puzzle_game"] = _new_block_state(
                    started=True,
                    tokens_spent=GAME_START_COST,
                    active_buff=get_game_buff_for_child(child, "block_puzzle"),
                )
                st.rerun()
        return

    _render_running_toolbar("block_puzzle", state)

    result = neon_block_puzzle_game(
        state,
        key=f"block_neon_{state['game_id']}",
        on_game_over_change=lambda: None,
        on_token_award_change=lambda: None,
    )
    _handle_block_token_event(child_id, state, _component_value(result, "token_award"))
    _handle_block_game_over(child_id, state, _component_value(result, "game_over"))


def _new_block_state(
    *,
    started: bool = False,
    tokens_spent: int = 0,
    active_buff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = new_block_game()
    state["started"] = started
    state["revivals_used"] = 0
    state["completed"] = False
    state["saved"] = False
    state["tokens_spent"] = int(tokens_spent)
    state["active_buff"] = active_buff or {}
    return state


def _handle_block_token_event(child_id: str, state: dict[str, Any], payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    if payload.get("game_id") != state["game_id"]:
        return
    threshold = int(payload.get("threshold") or 0)
    _award_threshold_token(
        child_id,
        state,
        game_type="block_puzzle",
        threshold=threshold,
    )
    state["score"] = max(int(state.get("score", 0)), int(payload.get("score") or 0))
    st.session_state["block_puzzle_game"] = state


def _handle_block_game_over(child_id: str, state: dict[str, Any], payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    if payload.get("game_id") != state["game_id"] or state.get("saved"):
        return
    state["score"] = int(payload.get("score") or 0)
    state["high_score"] = int(payload.get("high_score") or state.get("high_score", 0))
    state["placements"] = list(payload.get("placements") or [])
    state["game_over"] = True
    state["game_over_reason"] = str(payload.get("game_over_reason") or "no_valid_moves")
    state["completed"] = True
    state["started"] = False
    state["final_summary"] = f"本局分數 {state['score']}，成功放置 {len(state.get('placements', []))} 次方塊。"
    _save_finished_game(child_id, state, "block_puzzle", state.get("placements", []))
    st.session_state["block_puzzle_game"] = state
    st.rerun()


def _award_threshold_token(
    child_id: str,
    state: dict[str, Any],
    *,
    game_type: str,
    threshold: int,
) -> None:
    if threshold <= 0:
        return
    awarded_thresholds = [int(item) for item in state.get("awarded_thresholds", [])]
    if threshold in awarded_thresholds:
        return
    if len(awarded_thresholds) >= MAX_GAME_TOKENS_PER_ROUND:
        return
    try:
        result = award_game_token_once(
            child_id,
            game_type=game_type,
            game_id=state["game_id"],
            threshold=threshold,
        )
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return

    state.setdefault("awarded_thresholds", []).append(threshold)
    if result["awarded"]:
        state["tokens_earned"] = int(state.get("tokens_earned", 0)) + 1
        st.toast(f"分數達到 {threshold}，獲得 +1 代幣！", icon=":material/stars:")


def _save_finished_game(
    child_id: str,
    state: dict[str, Any],
    game_type: str,
    events: list[dict[str, Any]],
) -> None:
    if state.get("saved"):
        return
    try:
        finish_game(
            child_id,
            int(state.get("score", 0)),
            _events_with_buff(state, events),
            game_type=game_type,
            tokens_earned=int(state.get("tokens_earned", 0)),
            game_over_reason=str(state.get("game_over_reason", "")),
            game_id=state.get("game_id"),
            tokens_spent=int(state.get("tokens_spent", GAME_START_COST)),
        )
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return
    state["saved"] = True


def _queue_reflection(
    *,
    game_type: str,
    score: int,
    game_over_reason: str,
    game_id: str,
    summary: str = "",
    purpose: str = "replay",
) -> None:
    st.session_state["pending_reflection_question"] = {
        "student_id": st.session_state.get("child_id"),
        "game_id": game_id,
        "game_type": game_type,
        "question": random.choice(REFLECTION_QUESTIONS),
        "score_before_game_over": int(score),
        "game_over_reason": game_over_reason,
        "summary": summary,
        "purpose": purpose,
    }


def _render_reflection_gate(child: dict[str, Any], pending: dict[str, Any]) -> None:
    reason_label = GAME_OVER_LABELS.get(
        pending.get("game_over_reason"),
        "這一局結束了！",
    )
    game_label = GAME_LABELS.get(pending.get("game_type"), "遊戲")
    st.warning(reason_label, icon=":material/sentiment_dissatisfied:")
    st.markdown(
        f"""
        <div class="game-over-card">
            <strong>{escape(game_label)}再挑戰小問題</strong><br>
            本次分數：{int(pending.get("score_before_game_over", 0))}。先寫一句自己的想法，就可以開始新一局。<br>
            <strong>{escape(str(pending["question"]))}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("退出遊戲", icon=":material/logout:", key=f"exit_reflection_{pending['game_type']}", use_container_width=True):
        _exit_game(str(pending["game_type"]))
        st.rerun()

    with st.form(f"reflection_{pending['game_type']}_{pending['game_id']}", clear_on_submit=True):
        answer = st.text_area(
            "你的回答",
            placeholder=REFLECTION_PLACEHOLDER,
            height=120,
        )
        submitted = st.form_submit_button("送出回答，再玩一次", use_container_width=True)

    if not submitted:
        st.caption("回答不能空白；可以寫感覺、努力的地方，或下一次想用的策略。")
        return

    cleaned = answer.strip()
    if not cleaned:
        st.warning("先寫下一句想法，再開始新的挑戰。", icon=":material/edit_note:")
        return

    validation = validate_reflection_answer(child, str(pending["question"]), cleaned)
    if not validation["is_valid"]:
        st.warning(validation.get("gentle_prompt") or "請再寫得更具體一點。")
        return

    try:
        save_game_reflection(
            child_id=child["child_id"],
            game_type=str(pending["game_type"]),
            question=str(pending["question"]),
            answer=cleaned,
            score_before_game_over=int(pending["score_before_game_over"]),
            game_over_reason=str(pending["game_over_reason"]),
        )
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return

    if pending["game_type"] == "snake":
        st.session_state["snake_game"] = _new_snake_state(
            started=True,
            tokens_spent=0,
            active_buff=get_game_buff_for_child(child, "snake"),
        )
    else:
        st.session_state["block_puzzle_game"] = _new_block_state(
            started=True,
            tokens_spent=0,
            active_buff=get_game_buff_for_child(child, "block_puzzle"),
        )
    st.session_state["pending_reflection_question"] = None
    st.success("回答已保存，新的挑戰開始囉。")
    st.rerun()


def _spend_start_cost(child_id: str) -> bool:
    try:
        start_game(child_id)
    except InsufficientTokensError as exc:
        st.error(str(exc))
        return False
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return False
    return True


def _component_value(result: Any, field_name: str) -> Any:
    if result is None:
        return None
    if isinstance(result, dict):
        return result.get(field_name)
    return getattr(result, field_name, None)


def _metric_score(key: str) -> str:
    state = st.session_state.get(key) or {}
    score = int(state.get("score", 0))
    tokens = int(state.get("tokens_earned", 0))
    return f"{score} 分 / +{tokens}"


def _render_equipment_preview(child: dict[str, Any], game_type: str) -> None:
    outfit = get_selected_outfit_profile(child)
    buff = get_game_buff_for_child(child, game_type)
    applies_tag = "會在本局生效" if buff.get("applies") else "本局只作為外觀"
    st.markdown(
        f"""
        <div class="equipment-preview-card">
            {outfit_visual_html(outfit, "is-small")}
            <div>
                <strong>目前裝備：{escape(str(outfit.get("display_name") or "尚未選擇"))}</strong>
                <p>{escape(str(outfit.get("short_description") or "可以到角色頁選一件裝備。"))}</p>
                <p class="gear-buff-line">
                    {escape(str(buff.get("buff_label") or "本遊戲沒有加成"))}｜{escape(applies_tag)}
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _buff_status_label(buff: Any) -> str:
    if not isinstance(buff, dict) or not buff:
        return "尚未開始"
    if not buff.get("applies"):
        return "本遊戲沒有加成"
    return f"{buff.get('buff_label') or '裝備加成'}（已套用）"


def _events_with_buff(state: dict[str, Any], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buff = state.get("active_buff")
    if not isinstance(buff, dict) or not buff.get("applies"):
        return list(events)
    return [
        {
            "event_type": "outfit_buff",
            "outfit_id": buff.get("outfit_id", ""),
            "outfit_name": buff.get("outfit_name", ""),
            "buff_type": buff.get("buff_type", ""),
            "buff_value": buff.get("buff_value", 0),
            "buff_label": buff.get("buff_label", ""),
            "target_game": buff.get("target_game", ""),
        },
        *list(events),
    ]


def _render_running_toolbar(game_type: str, state: dict[str, Any]) -> None:
    cols = st.columns([3, 2, 1], vertical_alignment="center")
    with cols[0]:
        st.caption("遊戲進行中；不想繼續時可以直接退出，會回到遊戲入口。")
    with cols[1]:
        st.markdown(
            f'<span class="gear-buff-pill">本局加成：<strong>{escape(_buff_status_label(state.get("active_buff")))}</strong></span>',
            unsafe_allow_html=True,
        )
    with cols[2]:
        if st.button(
            "退出遊戲",
            icon=":material/logout:",
            key=f"exit_running_{game_type}",
            use_container_width=True,
        ):
            _exit_game(game_type)
            st.rerun()


def _render_game_over_panel(state: dict[str, Any], game_type: str) -> None:
    game_label = GAME_LABELS.get(game_type, "遊戲")
    reason = str(state.get("game_over_reason") or _default_game_over_reason(game_type))
    reason_label = GAME_OVER_LABELS.get(reason, "這一局結束了！")
    summary = state.get("final_summary") or "這一局已經結束，可以選擇退出，或先回答一個小問題再挑戰。"
    buff_label = _buff_status_label(state.get("active_buff"))
    st.markdown(
        f"""
        <div class="game-over-card">
            <strong>{escape(game_label)}結束</strong><br>
            原因：{escape(reason_label)}<br>
            本次分數：{int(state.get("score", 0))}｜本次獲得代幣：+{int(state.get("tokens_earned", 0))}<br>
            本局加成：{escape(buff_label)}<br>
            {escape(str(summary))}
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_exit, col_replay = st.columns(2)
    with col_exit:
        if st.button(
            "退出遊戲",
            icon=":material/logout:",
            key=f"exit_over_{game_type}_{state.get('game_id', '')}",
            use_container_width=True,
        ):
            _exit_game(game_type)
            st.rerun()
    with col_replay:
        if st.button(
            "再玩一次",
            icon=":material/restart_alt:",
            key=f"replay_{game_type}_{state.get('game_id', '')}",
            use_container_width=True,
        ):
            _queue_reflection(
                game_type=game_type,
                score=int(state.get("score", 0)),
                game_over_reason=reason,
                game_id=str(state.get("game_id") or new_game_id()),
                summary=str(summary),
                purpose="replay",
            )
            st.rerun()


def _render_game_status(child: dict[str, Any], current_game: str) -> None:
    state_key = "snake_game" if current_game == "snake" else "block_puzzle_game"
    state = st.session_state.get(state_key) or {}
    threshold = SNAKE_TOKEN_THRESHOLD if current_game == "snake" else BLOCK_TOKEN_THRESHOLD
    st.markdown(
        f"""
        <div class="game-status-strip">
            <span>目前代幣：<strong>{int(child.get("tokens", 0))}</strong></span>
            <span>{escape(GAME_LABELS.get(current_game, "遊戲"))}本局：<strong>{escape(_metric_score(state_key))}</strong></span>
            <span>裝備加成：<strong>{escape(_buff_status_label(state.get("active_buff")))}</strong></span>
            <span>每 {threshold} 分 +1 代幣，單局最多 +{MAX_GAME_TOKENS_PER_ROUND}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _exit_game(game_type: str) -> None:
    _reset_game_state(game_type)
    st.session_state["game_exit_notice"] = "已退出遊戲，回到遊戲入口。"


def _reset_game_state(game_type: str) -> None:
    if game_type == "snake":
        old_state = st.session_state.get("snake_game") or {}
        game_id = old_state.get("game_id")
        if game_id:
            st.session_state.pop(f"slither_{game_id}", None)
        st.session_state["snake_game"] = _new_snake_state()
    else:
        old_state = st.session_state.get("block_puzzle_game") or {}
        game_id = old_state.get("game_id")
        if game_id:
            st.session_state.pop(f"block_neon_{game_id}", None)
        st.session_state["block_puzzle_game"] = _new_block_state()

    pending = st.session_state.get("pending_reflection_question")
    if pending and pending.get("game_type") == game_type:
        st.session_state["pending_reflection_question"] = None


def _default_game_over_reason(game_type: str) -> str:
    return "no_valid_moves" if game_type == "block_puzzle" else "hit_wall"


def _snake_strength_summary(fruits_eaten: list[dict[str, Any]]) -> str:
    strength_fruits = [
        fruit
        for fruit in fruits_eaten
        if fruit.get("is_strength_fruit") or str(fruit.get("fruit_name", "")).endswith("果實")
    ]
    if not strength_fruits:
        return "這一局還沒有吃到優勢果實，下次可以追追看那顆會移動的大果實。"
    parts = []
    for fruit in strength_fruits:
        fruit_name = str(fruit.get("fruit_name") or "優勢果實")
        strength_name = str(fruit.get("strength_name") or fruit_name.replace("果實", ""))
        points = int(fruit.get("points") or 0)
        score_after = int(fruit.get("score_after") or 0)
        suggestion = _strength_practice_tip(strength_name)
        parts.append(f"{fruit_name} +{points} 分（吃到後總分 {score_after}）。下次可以這樣做到「{strength_name}」：{suggestion}")
    return "、".join(parts)


def _strength_practice_tip(strength_name: str) -> str:
    tips = {
        "仁慈": "主動問一句「你需要幫忙嗎？」或分享一個小資源。",
        "勤奮": "把大任務拆成一個 5 分鐘能完成的小步驟，先做第一步。",
        "好奇心": "遇到不懂的地方先問一個為什麼，再試著找一個答案。",
        "勇敢": "害怕時先深呼吸，選一件安全但有一點挑戰的小事去試。",
        "感激": "把想謝謝的人和原因說出來，或寫成一句小卡片。",
        "團體合作": "先聽隊友的想法，再說出自己可以負責的一件事。",
        "自我規範": "想衝動前停三秒，提醒自己先選一個比較好的做法。",
    }
    return tips.get(strength_name, "想一件今天可以練習的小行動，慢慢做一次就很好。")
