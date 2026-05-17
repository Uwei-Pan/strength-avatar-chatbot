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
    "今天有沒有一件讓你覺得有點難過或生氣的事？",
    "今天你有幫助別人嗎？可以說說看嗎？",
    "今天你有完成什麼小挑戰嗎？",
    "今天你覺得自己哪裡做得不錯？",
    "如果今天可以重來一次，你想怎麼做？",
    "今天有沒有人對你很好？發生了什麼事？",
    "你剛剛玩遊戲輸掉時，有什麼感覺？",
    "你想用哪一個優勢幫助自己再試一次？",
    "今天你最想謝謝誰？為什麼？",
]

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
        """
        <div class="kid-hero">
            <p class="kid-hero-title">優勢遊戲樂園</p>
            <p class="kid-hero-copy">玩遊戲、練反思，累積自己的優勢代幣。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        f"開始一局需要 {GAME_START_COST} 代幣。"
        f"貪食蛇每 {SNAKE_TOKEN_THRESHOLD} 分 +1 代幣，"
        f"方塊消除每 {BLOCK_TOKEN_THRESHOLD} 分 +1 代幣，單局最多 +{MAX_GAME_TOKENS_PER_ROUND}。"
    )

    locked_game = _locked_game_type()
    if locked_game and st.session_state.get("current_game_type") != locked_game:
        st.session_state["current_game_type"] = locked_game
        st.session_state["game_switch_notice"] = "要先結束目前這局，才能切換到另一個遊戲。"
        st.rerun()

    notice = st.session_state.pop("game_switch_notice", None)
    if notice:
        st.warning(notice, icon=":material/lock:")

    current_game = st.radio(
        "選擇遊戲",
        options=["snake", "block_puzzle"],
        format_func=lambda value: GAME_LABELS[value],
        horizontal=True,
        key="current_game_type",
        disabled=locked_game is not None,
    )

    metric_cols = st.columns(3)
    metric_cols[0].metric("目前代幣", child["tokens"])
    metric_cols[1].metric("貪食蛇本局", _metric_score("snake_game"))
    metric_cols[2].metric("方塊本局", _metric_score("block_puzzle_game"))

    pending = st.session_state.get("pending_reflection_question")
    if pending and pending.get("game_type") == current_game:
        _render_reflection_gate(child, pending)
        return

    if current_game == "snake":
        _render_snake(child_id)
    else:
        _render_block_puzzle(child_id)


def _init_state() -> None:
    st.session_state.setdefault("current_game_type", "snake")
    st.session_state.setdefault("snake_game", None)
    st.session_state.setdefault("block_puzzle_game", None)
    st.session_state.setdefault("pending_reflection_question", None)


def _locked_game_type() -> str | None:
    pending = st.session_state.get("pending_reflection_question")
    if pending:
        return str(pending.get("game_type"))
    for game_type, key in [("snake", "snake_game"), ("block_puzzle", "block_puzzle_game")]:
        state = st.session_state.get(key) or {}
        if state.get("started") and not state.get("completed"):
            return game_type
    return None


def _render_snake(child_id: str) -> None:
    state = st.session_state.get("snake_game")
    if not state:
        state = _new_snake_state()
        st.session_state["snake_game"] = state

    st.markdown('<p class="kid-section-title">貪食蛇：星光果實賽道</p>', unsafe_allow_html=True)
    if state.get("completed"):
        _render_final_summary(state, "snake")
        if st.button("開始新一局貪食蛇", icon=":material/restart_alt:", use_container_width=True):
            st.session_state["snake_game"] = _new_snake_state()
            st.rerun()
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
        if st.button("開始貪食蛇", icon=":material/play_arrow:", use_container_width=True):
            if _spend_start_cost(child_id):
                st.session_state["snake_game"] = _new_snake_state(started=True)
                st.rerun()
        return

    result = slither_snake_game(
        state,
        key=f"slither_{state['game_id']}",
        on_game_over_change=lambda: None,
        on_token_award_change=lambda: None,
    )
    _handle_snake_token_event(child_id, state, _component_value(result, "token_award"))
    _handle_snake_game_over(child_id, state, _component_value(result, "game_over"))


def _new_snake_state(*, started: bool = False) -> dict[str, Any]:
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
    state["score_bank"] = int(state.get("score_bank", 0)) + state["score"]
    if int(state.get("revivals_used", 0)) < 1:
        _queue_reflection(
            game_type="snake",
            score=state["score"],
            game_over_reason=state["game_over_reason"],
            game_id=state["game_id"],
            purpose="revive",
        )
    else:
        state["score"] = int(state.get("score_bank", state["score"]))
        state["completed"] = True
        state["started"] = False
        state["final_summary"] = _snake_strength_summary(state.get("all_fruits_eaten", []))
        _save_finished_game(child_id, state, "snake", state.get("all_fruits_eaten", []))
    st.session_state["snake_game"] = state
    st.rerun()


def _render_block_puzzle(child_id: str) -> None:
    state = st.session_state.get("block_puzzle_game")
    if not state:
        state = new_block_game()
        state["started"] = False
        state["revivals_used"] = 0
        state["completed"] = False
        st.session_state["block_puzzle_game"] = state

    st.markdown('<p class="kid-section-title">方塊消除：彩色積木挑戰</p>', unsafe_allow_html=True)
    if state.get("completed"):
        _render_final_summary(state, "block_puzzle")
        if st.button("開始新一局方塊消除", icon=":material/restart_alt:", use_container_width=True):
            state = new_block_game()
            state["started"] = False
            st.session_state["block_puzzle_game"] = state
            st.rerun()
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
        if st.button("開始方塊消除", icon=":material/play_arrow:", use_container_width=True):
            if _spend_start_cost(child_id):
                state = new_block_game()
                state["started"] = True
                state["revivals_used"] = 0
                state["completed"] = False
                st.session_state["block_puzzle_game"] = state
                st.rerun()
        return

    top_cols = st.columns(4)
    top_cols[0].metric("分數", state["score"])
    top_cols[1].metric("最高分", state.get("high_score", 0))
    top_cols[2].metric("本局代幣", state.get("tokens_earned", 0))
    top_cols[3].metric("玩法", "8 x 8")

    result = neon_block_puzzle_game(
        state,
        key=f"block_neon_{state['game_id']}",
        on_game_over_change=lambda: None,
        on_token_award_change=lambda: None,
    )
    _handle_block_token_event(child_id, state, _component_value(result, "token_award"))
    _handle_block_game_over(child_id, state, _component_value(result, "game_over"))


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
    if int(state.get("revivals_used", 0)) < 1:
        _queue_reflection(
            game_type="block_puzzle",
            score=int(state["score"]),
            game_over_reason=state.get("game_over_reason") or "no_valid_moves",
            game_id=state["game_id"],
            purpose="revive",
        )
    else:
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
            events,
            game_type=game_type,
            tokens_earned=int(state.get("tokens_earned", 0)),
            game_over_reason=str(state.get("game_over_reason", "")),
            game_id=state.get("game_id"),
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
    purpose: str = "revive",
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
        <div class="kid-card">
            想復活一次，繼續挑戰「{escape(game_label)}」嗎？先回答一個小問題：<br>
            <strong>{escape(str(pending["question"]))}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form(f"reflection_{pending['game_type']}_{pending['game_id']}", clear_on_submit=True):
        answer = st.text_area(
            "你的回答",
            placeholder="至少 20 個字。可以說說你的感覺、剛剛怎麼輸的，或下一次想怎麼做。",
            height=120,
        )
        submitted = st.form_submit_button("送出回答，使用一次復活", use_container_width=True)

    if not submitted:
        st.caption("每局只能復活一次；回答至少 20 個字，而且要有具體想法。")
        return

    cleaned = answer.strip()
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
        old_state = st.session_state.get("snake_game") or {}
        revived = _new_snake_state(started=True)
        revived["revivals_used"] = int(old_state.get("revivals_used", 0)) + 1
        revived["tokens_earned"] = int(old_state.get("tokens_earned", 0))
        revived["awarded_thresholds"] = list(old_state.get("awarded_thresholds", []))
        revived["all_fruits_eaten"] = list(old_state.get("all_fruits_eaten", []))
        revived["score_bank"] = int(old_state.get("score_bank", 0))
        st.session_state["snake_game"] = revived
    else:
        old_state = st.session_state.get("block_puzzle_game") or {}
        revived = new_block_game()
        revived["started"] = True
        revived["revivals_used"] = int(old_state.get("revivals_used", 0)) + 1
        revived["tokens_earned"] = int(old_state.get("tokens_earned", 0))
        revived["awarded_thresholds"] = list(old_state.get("awarded_thresholds", []))
        revived["high_score"] = int(old_state.get("high_score", 0))
        st.session_state["block_puzzle_game"] = revived
    st.session_state["pending_reflection_question"] = None
    st.success("回答已保存，這是本局唯一一次復活機會。")
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


def _render_final_summary(state: dict[str, Any], game_type: str) -> None:
    title = "本局完整結束" if game_type == "snake" else "方塊挑戰結束"
    summary = state.get("final_summary") or "這一局已經結束，可以換遊戲或重新開始。"
    st.markdown(
        f"""
        <div class="kid-card">
            <strong>{escape(title)}</strong><br>
            分數：{int(state.get("score", 0))}｜本局代幣：+{int(state.get("tokens_earned", 0))}<br>
            {escape(str(summary))}
        </div>
        """,
        unsafe_allow_html=True,
    )


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
