import copy
import random
from typing import Any

from services.game_service import new_game_id


BOARD_SIZE = 8

COLORS = [
    "#64d2ff",
    "#7ef0a1",
    "#ffd166",
    "#ff8fab",
    "#c7a4ff",
    "#ff9f43",
    "#4ecdc4",
]

SHAPES = [
    {"name": "單格", "cells": [(0, 0)]},
    {"name": "兩格直線", "cells": [(0, 0), (0, 1)]},
    {"name": "兩格直線", "cells": [(0, 0), (1, 0)]},
    {"name": "三格直線", "cells": [(0, 0), (0, 1), (0, 2)]},
    {"name": "三格直線", "cells": [(0, 0), (1, 0), (2, 0)]},
    {"name": "L 型", "cells": [(0, 0), (1, 0), (1, 1)]},
    {"name": "L 型", "cells": [(0, 1), (1, 1), (1, 0)]},
    {"name": "2x2 方塊", "cells": [(0, 0), (0, 1), (1, 0), (1, 1)]},
    {"name": "T 型", "cells": [(0, 0), (0, 1), (0, 2), (1, 1)]},
    {"name": "短折線", "cells": [(0, 0), (0, 1), (1, 1)]},
    {"name": "短折線", "cells": [(0, 1), (1, 1), (1, 0)]},
]


def new_game() -> dict[str, Any]:
    return {
        "game_id": new_game_id(),
        "board": [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)],
        # None = 已用完等補充；dict = 可用方塊
        "pieces": [_new_piece(), _new_piece(), _new_piece()],
        "selected_piece": 0,
        "score": 0,
        "high_score": 0,
        "tokens_earned": 0,
        "awarded_thresholds": [],
        "game_over": False,
        "game_over_reason": "",
        "notice": "",
        "last_cleared": [],
        "placements": [],
    }


def select_piece(state: dict[str, Any], piece_index: int) -> dict[str, Any]:
    if 0 <= piece_index < len(state["pieces"]):
        if state["pieces"][piece_index] is not None:
            state["selected_piece"] = piece_index
    return state


def place_selected_piece(state: dict[str, Any], row: int, col: int) -> dict[str, Any]:
    if state.get("game_over"):
        return state

    piece_index = int(state.get("selected_piece", 0))
    piece = state["pieces"][piece_index]

    if piece is None:
        state["notice"] = "這個方塊已經用掉了，請選另一個。"
        return state

    if not can_place(state["board"], piece, row, col):
        state["notice"] = "這個位置放不下喔，換個地方試試看。"
        return state

    board = copy.deepcopy(state["board"])
    for cell_row, cell_col in piece["cells"]:
        board[row + cell_row][col + cell_col] = piece["color"]

    placed_cells = len(piece["cells"])
    clear_result = _clear_full_lines(board)
    cleared_lines = clear_result["cleared_lines"]
    line_bonus = 50 * cleared_lines
    combo_bonus = 25 * max(0, cleared_lines - 1)
    earned = placed_cells * 10 + line_bonus + combo_bonus

    state["board"] = clear_result["board"]
    state["score"] += earned
    state["high_score"] = max(int(state.get("high_score", 0)), int(state["score"]))
    state["last_cleared"] = clear_result["cleared_positions"]
    state["placements"].append(
        {
            "piece_name": piece["name"],
            "cells": placed_cells,
            "row": row,
            "col": col,
            "score_after": state["score"],
            "cleared_lines": cleared_lines,
        }
    )

    # 標記為已用
    state["pieces"][piece_index] = None

    # 三個都用完才補充新的三個
    if all(p is None for p in state["pieces"]):
        state["pieces"] = [_new_piece(), _new_piece(), _new_piece()]
        state["selected_piece"] = 0
        state["notice"] = (
            f"消除 {cleared_lines} 條線！三個方塊用完，補充新的三個。"
            if cleared_lines
            else "三個方塊都用完了，補充新的三個！"
        )
    else:
        # 自動選下一個可用的方塊
        next_index = next(
            (i for i, p in enumerate(state["pieces"]) if p is not None), 0
        )
        state["selected_piece"] = next_index
        state["notice"] = _score_notice(placed_cells, cleared_lines, combo_bonus)

    # 用剩餘可用方塊判斷 game over
    remaining = [p for p in state["pieces"] if p is not None]
    if not has_any_valid_move(state["board"], remaining):
        state["game_over"] = True
        state["game_over_reason"] = "no_valid_moves"
        state["notice"] = "目前沒有地方可以放囉！先回答一個小問題，再挑戰一次。"

    return state


def can_place(board: list[list[str | None]], piece: dict[str, Any], row: int, col: int) -> bool:
    for cell_row, cell_col in piece["cells"]:
        target_row = row + cell_row
        target_col = col + cell_col
        if target_row < 0 or target_col < 0:
            return False
        if target_row >= BOARD_SIZE or target_col >= BOARD_SIZE:
            return False
        if board[target_row][target_col] is not None:
            return False
    return True


def has_any_valid_move(board: list[list[str | None]], pieces: list[dict[str, Any]]) -> bool:
    for piece in pieces:
        if piece is None:
            continue
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if can_place(board, piece, row, col):
                    return True
    return False


def next_token_thresholds(score: int, awarded_thresholds: list[int], threshold: int = 150) -> list[int]:
    awarded = set(int(item) for item in awarded_thresholds)
    earned_count = int(score) // threshold
    return [
        step * threshold
        for step in range(1, earned_count + 1)
        if step * threshold not in awarded
    ]


def _new_piece() -> dict[str, Any]:
    shape = random.choice(SHAPES)
    return {
        "id": new_game_id(),
        "name": shape["name"],
        "cells": list(shape["cells"]),
        "color": random.choice(COLORS),
    }


def _clear_full_lines(board: list[list[str | None]]) -> dict[str, Any]:
    full_rows = [
        row_index
        for row_index, row in enumerate(board)
        if all(cell is not None for cell in row)
    ]
    full_cols = [
        col_index
        for col_index in range(BOARD_SIZE)
        if all(board[row_index][col_index] is not None for row_index in range(BOARD_SIZE))
    ]
    cleared_positions = []
    for row_index in full_rows:
        for col_index in range(BOARD_SIZE):
            cleared_positions.append((row_index, col_index))
            board[row_index][col_index] = None
    for col_index in full_cols:
        for row_index in range(BOARD_SIZE):
            cleared_positions.append((row_index, col_index))
            board[row_index][col_index] = None
    return {
        "board": board,
        "cleared_lines": len(full_rows) + len(full_cols),
        "cleared_positions": cleared_positions,
    }


def _score_notice(placed_cells: int, cleared_lines: int, combo_bonus: int) -> str:
    if cleared_lines == 0:
        return f"放好了！這塊有 {placed_cells} 格，獲得 {placed_cells * 10} 分。"
    if combo_bonus:
        return f"太棒了，同時消除 {cleared_lines} 條線，還有連消加分！"
    return f"消除 {cleared_lines} 條線，獲得額外分數！"