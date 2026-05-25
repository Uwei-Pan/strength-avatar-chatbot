import random
from typing import Any


BOARD_SIZE = 10
FRUIT_COUNT = 3
FRUIT_STRENGTHS = ["仁慈", "勤奮", "好奇心", "勇敢", "感激", "團體合作"]

# Each strength maps to a distinct emoji shown on the board
STRENGTH_EMOJIS: dict[str, str] = {
    "仁慈":   "💛",   # golden heart
    "勤奮":   "⭐",   # shining star
    "好奇心": "🔭",   # telescope
    "勇敢":   "🔥",   # fire
    "感激":   "🌸",   # blossom
    "團體合作": "🤝", # handshake
}

# Arrow shown inside the snake's head cell
_HEAD_ARROW: dict[str, str] = {
    "UP": "▲", "DOWN": "▼", "LEFT": "◀", "RIGHT": "▶",
}

# Auto-advance interval in seconds per speed level
SPEED_INTERVALS = {
    "慢": 0.6,
    "普通": 0.35,
    "快": 0.18,
}


def new_game() -> dict[str, Any]:
    snake = [(5, 4), (5, 3), (5, 2)]
    fruits = _spawn_fruits(snake, [])
    return {
        "snake": snake,
        "direction": "RIGHT",
        "pending_direction": "RIGHT",  # buffered input, applied on next step
        "fruits": fruits,
        "score": 0,
        "game_over": False,
        "paused": False,
        "fruits_eaten": [],
        "last_message": None,
        "steps": 0,
    }


def turn(state: dict[str, Any], direction: str) -> dict[str, Any]:
    """Buffer a direction change; it is applied on the next step() call."""
    opposites = {
        "UP": "DOWN",
        "DOWN": "UP",
        "LEFT": "RIGHT",
        "RIGHT": "LEFT",
    }
    # Ignore reversal; compare against current moving direction, not pending
    if opposites.get(direction) != state.get("direction"):
        state["pending_direction"] = direction
    return state


def step(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("game_over") or state.get("paused"):
        return state

    # Commit buffered direction
    state["direction"] = state.get("pending_direction", state["direction"])

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
    state["steps"] = state.get("steps", 0) + 1

    hit_index = next(
        (i for i, f in enumerate(state["fruits"]) if f["position"] == new_head),
        None,
    )
    if hit_index is not None:
        state["score"] += 10
        eaten_fruit = state["fruits"][hit_index]
        eaten = {
            "strength_name": eaten_fruit["strength_name"],
            "fruit_name": eaten_fruit["fruit_name"],
            "score_after": state["score"],
        }
        state["fruits_eaten"].append(eaten)
        state["last_message"] = eaten
        remaining = [f for i, f in enumerate(state["fruits"]) if i != hit_index]
        state["fruits"][hit_index] = _spawn_one_fruit(state["snake"], remaining)
    else:
        state["snake"].pop()
        state["last_message"] = None

    return state


def toggle_pause(state: dict[str, Any]) -> dict[str, Any]:
    if not state.get("game_over"):
        state["paused"] = not state.get("paused", False)
    return state


def render_cells(state: dict[str, Any]) -> list[list[dict[str, Any]]]:
    """Return a 2-D grid of cell descriptors consumed by the board renderer.

    Each cell is a dict with at minimum a ``type`` key:
      - ``"empty"``  – blank cell
      - ``"head"``   – snake head (includes ``content`` arrow + ``connects`` set)
      - ``"body"``   – snake body segment (includes ``connects`` set)
      - ``"tail"``   – last snake segment  (includes ``connects`` set)
      - ``"fruit"``  – fruit (includes ``content`` emoji + ``strength_name``)

    ``connects`` is a set of sides (``"up"``, ``"down"``, ``"left"``, ``"right"``)
    that border an adjacent snake segment, used to merge cells visually.
    """
    snake = state["snake"]

    # Build empty grid
    cells: list[list[dict[str, Any]]] = [
        [{"type": "empty", "content": ""} for _ in range(BOARD_SIZE)]
        for _ in range(BOARD_SIZE)
    ]

    # Snake segments
    for i, (row, col) in enumerate(snake):
        prev = snake[i - 1] if i > 0 else None           # closer to head
        nxt  = snake[i + 1] if i < len(snake) - 1 else None  # closer to tail

        connects: set[str] = set()
        for neighbour in (prev, nxt):
            if neighbour is None:
                continue
            nr, nc = neighbour
            if   nr == row - 1: connects.add("up")
            elif nr == row + 1: connects.add("down")
            elif nc == col - 1: connects.add("left")
            elif nc == col + 1: connects.add("right")

        if i == 0:
            cell_type = "head"
            content   = _HEAD_ARROW.get(state["direction"], "▶")
        elif i == len(snake) - 1:
            cell_type = "tail"
            content   = ""
        else:
            cell_type = "body"
            content   = ""

        cells[row][col] = {
            "type":     cell_type,
            "content":  content,
            "connects": connects,
        }

    # Fruits
    for fruit in state["fruits"]:
        fr, fc = fruit["position"]
        cells[fr][fc] = {
            "type":          "fruit",
            "content":       STRENGTH_EMOJIS.get(fruit["strength_name"], "◆"),
            "strength_name": fruit["strength_name"],
        }

    return cells


# ── internal helpers ──────────────────────────────────────────────────────────

def _spawn_fruits(
    snake: list[tuple[int, int]],
    existing: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    fruits: list[dict[str, Any]] = []
    for _ in range(FRUIT_COUNT):
        fruit = _spawn_one_fruit(snake, fruits)
        fruits.append(fruit)
    return fruits


def _spawn_one_fruit(
    snake: list[tuple[int, int]],
    existing_fruits: list[dict[str, Any]],
) -> dict[str, Any]:
    taken = set(snake) | {f["position"] for f in existing_fruits}
    open_cells = [
        (row, col)
        for row in range(BOARD_SIZE)
        for col in range(BOARD_SIZE)
        if (row, col) not in taken
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