import random
from typing import Any


BOARD_SIZE = 10
FRUIT_STRENGTHS = ["仁慈", "勤奮", "好奇心", "勇敢", "感激", "團體合作"]


def new_game() -> dict[str, Any]:
    snake = [(5, 4), (5, 3), (5, 2)]
    return {
        "snake": snake,
        "direction": "RIGHT",
        "fruit": _spawn_fruit(snake),
        "score": 0,
        "game_over": False,
        "fruits_eaten": [],
        "last_message": None,
    }


def turn(state: dict[str, Any], direction: str) -> dict[str, Any]:
    opposites = {
        "UP": "DOWN",
        "DOWN": "UP",
        "LEFT": "RIGHT",
        "RIGHT": "LEFT",
    }
    if opposites.get(direction) != state.get("direction"):
        state["direction"] = direction
    return state


def step(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("game_over"):
        return state

    head_y, head_x = state["snake"][0]
    dy, dx = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1),
    }[state["direction"]]
    new_head = (head_y + dy, head_x + dx)

    if _hit_wall(new_head) or new_head in state["snake"]:
        state["game_over"] = True
        state["last_message"] = "遊戲結束，這一局可以先記錄下來。"
        return state

    state["snake"].insert(0, new_head)
    if new_head == state["fruit"]["position"]:
        state["score"] += 10
        eaten = {
            "strength_name": state["fruit"]["strength_name"],
            "fruit_name": state["fruit"]["fruit_name"],
            "score_after": state["score"],
        }
        state["fruits_eaten"].append(eaten)
        state["last_message"] = eaten
        state["fruit"] = _spawn_fruit(state["snake"])
    else:
        state["snake"].pop()
        state["last_message"] = None
    return state


def render_cells(state: dict[str, Any]) -> list[list[str]]:
    cells = [["" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for index, (row, col) in enumerate(state["snake"]):
        cells[row][col] = "●" if index == 0 else "•"
    fruit_row, fruit_col = state["fruit"]["position"]
    cells[fruit_row][fruit_col] = "◆"
    return cells


def _spawn_fruit(snake: list[tuple[int, int]]) -> dict[str, Any]:
    open_cells = [
        (row, col)
        for row in range(BOARD_SIZE)
        for col in range(BOARD_SIZE)
        if (row, col) not in snake
    ]
    position = random.choice(open_cells)
    strength_name = random.choice(FRUIT_STRENGTHS)
    return {
        "position": position,
        "strength_name": strength_name,
        "fruit_name": f"{strength_name}果實",
    }


def _hit_wall(position: tuple[int, int]) -> bool:
    row, col = position
    return row < 0 or col < 0 or row >= BOARD_SIZE or col >= BOARD_SIZE
