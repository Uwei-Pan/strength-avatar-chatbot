from collections.abc import Callable
from typing import Any

import streamlit as st


HTML = """
<div class="block-neon-shell">
  <div class="block-neon-top">
    <button class="block-menu" type="button" aria-label="Menu">
      <span class="block-menu-icon"><i></i><i></i><i></i><i></i></span>
      <strong>MENU</strong>
    </button>
    <div class="block-score-card">
      <span>皇冠分數</span>
      <strong id="score">0</strong>
    </div>
    <div class="block-token-card">
      <span class="block-coin">★</span>
      <strong id="tokens">0</strong>
    </div>
  </div>
  <div id="notice" class="block-notice">選擇下方方塊，再點棋盤放置。</div>
  <div id="board" class="block-board" aria-label="方塊消除棋盤"></div>
  <div class="block-tool-row">
    <div class="block-tool"><span>↔</span><strong>2</strong></div>
    <div class="block-tool"><span>⟳</span><strong>2</strong></div>
  </div>
  <div class="block-tray">
    <div id="pieces" class="block-pieces"></div>
    <div class="block-hold"></div>
  </div>
</div>
"""

CSS = """
.block-neon-shell {
  width: min(100%, 760px);
  margin: 0 auto 20px;
  padding: 20px;
  border-radius: 24px;
  color: #f7eaff;
  background:
    radial-gradient(circle at 18% 20%, rgba(180, 41, 255, 0.16), transparent 32%),
    radial-gradient(circle at 82% 70%, rgba(34, 238, 220, 0.12), transparent 34%),
    linear-gradient(180deg, #220027 0%, #170018 100%);
  box-shadow: 0 26px 70px rgba(31, 0, 40, 0.45);
  box-sizing: border-box;
}

.block-neon-top {
  display: grid;
  grid-template-columns: 1fr 1.5fr 1fr;
  gap: 14px;
  align-items: center;
  margin-bottom: 18px;
}

.block-menu,
.block-score-card,
.block-token-card,
.block-tool,
.block-tray,
.block-hold {
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: #33263d;
  box-shadow: 0 6px 0 rgba(12, 8, 20, 0.48), inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.block-menu {
  height: 76px;
  display: flex;
  gap: 14px;
  align-items: center;
  justify-content: center;
  color: #cf29f4;
  font-size: 24px;
  font-weight: 1000;
  cursor: default;
}

.block-menu-icon {
  display: grid;
  grid-template-columns: repeat(2, 18px);
  gap: 4px;
}

.block-menu-icon i {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  background: #ca27ef;
  box-shadow: 0 0 10px rgba(221, 44, 255, 0.55);
}

.block-menu-icon i:nth-child(4) {
  background: transparent;
  border: 3px solid #ca27ef;
}

.block-score-card {
  height: 88px;
  display: grid;
  place-items: center;
}

.block-score-card span {
  color: #ad36c8;
  font-size: 16px;
  font-weight: 900;
}

.block-score-card strong {
  color: #d931ff;
  font-size: clamp(42px, 8vw, 66px);
  line-height: 0.9;
  text-shadow: 0 0 16px rgba(217, 49, 255, 0.42);
}

.block-token-card {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #ffc13a;
  font-size: 26px;
}

.block-coin {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  color: #ff9f2d;
  background: #ffe28a;
  box-shadow: inset 0 -4px 0 rgba(137, 78, 16, 0.24), 0 0 18px rgba(255, 195, 58, 0.32);
}

.block-notice {
  min-height: 24px;
  margin: 0 4px 10px;
  color: #d9a8e7;
  font-size: 14px;
  font-weight: 800;
}

.block-board {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 3px;
  padding: 10px;
  border-radius: 20px;
  border: 4px solid #b72dec;
  background: #15071c;
  box-shadow:
    0 0 0 3px rgba(255, 69, 221, 0.62),
    inset 0 0 22px rgba(155, 42, 209, 0.26),
    0 0 28px rgba(200, 39, 239, 0.42);
}

.block-cell {
  aspect-ratio: 1;
  border: 2px solid #582065;
  border-radius: 4px;
  background: rgba(23, 4, 29, 0.82);
  cursor: pointer;
  transition: filter 120ms ease, transform 120ms ease, box-shadow 120ms ease;
}

.block-cell:hover {
  filter: brightness(1.4);
  transform: translateY(-1px);
}

.block-cube {
  display: block;
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 3px;
  box-shadow: inset 0 -5px 0 rgba(0, 0, 0, 0.2), inset 0 0 0 2px rgba(255, 255, 255, 0.18);
}

.block-cube::after {
  content: "";
  position: absolute;
  inset: 23%;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.25);
}

.block-shape-triangle::after {
  inset: 24% 20% 18%;
  clip-path: polygon(50% 0, 100% 100%, 0 100%);
}

.block-shape-leaf::after {
  inset: 18%;
  border-radius: 80% 8% 80% 8%;
  transform: rotate(45deg);
}

.block-tool-row {
  display: flex;
  justify-content: space-between;
  margin: 20px 6px 18px;
}

.block-tool {
  width: 150px;
  height: 74px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #d931ff;
  font-size: 34px;
}

.block-tray {
  display: grid;
  grid-template-columns: 1fr 190px;
  gap: 20px;
  padding: 18px;
}

.block-pieces {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}

.block-piece {
  min-height: 108px;
  border: 0;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  cursor: pointer;
  display: grid;
  place-items: center;
  padding: 12px;
}

.block-piece.used {
  opacity: 0.18;
  cursor: default;
  pointer-events: none;
}

.block-piece.active {
  outline: 3px solid #d931ff;
  box-shadow: 0 0 18px rgba(217, 49, 255, 0.42);
}

.block-piece-grid {
  display: grid;
  place-items: center;
  justify-content: center;
  align-content: center;
  gap: 4px;
}

.block-mini-cell {
  display: block;
  width: 28px;
  height: 28px;
}

@media (max-width: 700px) {
  .block-neon-shell { padding: 12px; border-radius: 18px; }
  .block-neon-top { grid-template-columns: 1fr; }
  .block-tray { grid-template-columns: 1fr; }
  .block-hold { display: none; }
  .block-tool { width: 120px; }
}
"""

JS = """
const instances = new WeakMap()
const size = 8
const colors = [
  { color: "#2bdc48", shape: "square" },
  { color: "#e63e3f", shape: "square" },
  { color: "#d9cf24", shape: "triangle" },
  { color: "#24c9c5", shape: "leaf" },
  { color: "#35a9e3", shape: "square" },
  { color: "#aadb2c", shape: "line" },
]
const shapes = [
  { name: "單格", cells: [[0, 0]] },
  { name: "兩格直線", cells: [[0, 0], [0, 1]] },
  { name: "兩格直線", cells: [[0, 0], [1, 0]] },
  { name: "三格直線", cells: [[0, 0], [0, 1], [0, 2]] },
  { name: "三格直線", cells: [[0, 0], [1, 0], [2, 0]] },
  { name: "L 型", cells: [[0, 0], [1, 0], [1, 1]] },
  { name: "L 型", cells: [[0, 1], [1, 1], [1, 0]] },
  { name: "2x2 方塊", cells: [[0, 0], [0, 1], [1, 0], [1, 1]] },
  { name: "T 型", cells: [[0, 0], [0, 1], [0, 2], [1, 1]] },
  { name: "短折線", cells: [[0, 0], [0, 1], [1, 1]] },
]

export default function (component) {
  const { data, parentElement, setTriggerValue } = component
  const gameId = data?.game_id ?? "block-demo"
  let state = instances.get(parentElement)
  if (!state || state.gameId !== gameId) {
    state = createState(gameId, data)
    instances.set(parentElement, state)
  } else {
    const incomingTokens = Number(data?.tokens_earned ?? state.serverTokens ?? 0)
    if (incomingTokens > state.serverTokens) {
      state.localTokens = 0
    }
    state.serverTokens = incomingTokens
  }
  render(parentElement, state, setTriggerValue)
}

function createState(gameId, data) {
  return {
    gameId,
    board: Array.from({ length: size }, () => Array.from({ length: size }, () => null)),
    // null = 已用完，等補充；非 null = 可用
    pieces: [newPiece(), newPiece(), newPiece()],
    selected: 0,
    score: 0,
    highScore: Number(data?.high_score ?? 0),
    serverTokens: Number(data?.tokens_earned ?? 0),
    localTokens: 0,
    sentThresholds: new Set((data?.awarded_thresholds ?? []).map(Number)),
    placements: [],
    gameOver: false,
    notice: "選擇下方方塊，再點棋盤放置。",
  }
}

function render(root, state, setTriggerValue) {
  root.querySelector("#score").textContent = String(state.score)
  root.querySelector("#tokens").textContent = String(state.serverTokens + state.localTokens)
  root.querySelector("#notice").textContent = state.notice

  const board = root.querySelector("#board")
  board.innerHTML = ""
  state.board.forEach((row, rowIndex) => {
    row.forEach((cell, colIndex) => {
      const button = document.createElement("button")
      button.className = "block-cell"
      button.type = "button"
      button.setAttribute("aria-label", `放在 ${rowIndex + 1}, ${colIndex + 1}`)
      if (cell) button.appendChild(cube(cell))
      button.onclick = () => place(state, rowIndex, colIndex, setTriggerValue, root)
      board.appendChild(button)
    })
  })

  const pieces = root.querySelector("#pieces")
  pieces.innerHTML = ""
  state.pieces.forEach((piece, index) => {
    const button = document.createElement("button")
    button.type = "button"

    if (piece === null) {
      // 已用完：灰掉、不可點
      button.className = "block-piece used"
      button.setAttribute("aria-label", "已使用")
    } else {
      const isSelected = index === state.selected
      button.className = `block-piece${isSelected ? " active" : ""}`
      button.setAttribute("aria-label", `選擇 ${piece.name}`)
      button.onclick = () => {
        state.selected = index
        state.notice = `已選擇：${piece.name}`
        render(root, state, setTriggerValue)
      }
      button.appendChild(pieceGrid(piece))
    }
    pieces.appendChild(button)
  })
}

function place(state, row, col, setTriggerValue, root) {
  if (state.gameOver) return

  const piece = state.pieces[state.selected]
  // 選到的格子已用完
  if (piece === null) {
    state.notice = "這個方塊已經用掉了，請選另一個。"
    render(root, state, setTriggerValue)
    return
  }
  if (!canPlace(state.board, piece, row, col)) {
    state.notice = "這個位置放不下喔，換個地方試試看。"
    render(root, state, setTriggerValue)
    return
  }

  // 放置
  piece.cells.forEach(([r, c]) => {
    state.board[row + r][col + c] = { color: piece.color, shape: piece.shape }
  })
  const cleared = clearLines(state.board)
  const placedScore = piece.cells.length * 10
  const lineScore = cleared * 50
  const combo = Math.max(0, cleared - 1) * 25
  state.score += placedScore + lineScore + combo
  state.highScore = Math.max(state.highScore, state.score)
  state.placements.push({
    piece_name: piece.name,
    cells: piece.cells.length,
    row,
    col,
    score_after: state.score,
    cleared_lines: cleared,
  })

  // 標記為已用
  state.pieces[state.selected] = null

  // 三個都用完才補充新的三個
  if (state.pieces.every(p => p === null)) {
    state.pieces = [newPiece(), newPiece(), newPiece()]
    state.selected = 0
    state.notice = cleared
      ? `消除 ${cleared} 條線！三個方塊用完，補充新的三個。`
      : `三個方塊都用完了，補充新的三個！`
  } else {
    // 自動選下一個可用的方塊
    const next = state.pieces.findIndex(p => p !== null)
    if (next !== -1) state.selected = next
    state.notice = cleared ? `消除 ${cleared} 條線！` : `放好了，+${placedScore} 分。`
  }

  maybeAwardToken(state, setTriggerValue)

  // 用剩餘可用方塊判斷 game over
  const remaining = state.pieces.filter(p => p !== null)
  if (!hasMove(state.board, remaining)) {
    state.gameOver = true
    state.notice = "目前沒有地方可以放囉！"
    setTriggerValue("game_over", {
      game_id: state.gameId,
      game_type: "block_puzzle",
      score: state.score,
      high_score: state.highScore,
      game_over_reason: "no_valid_moves",
      placements: state.placements,
    })
  }

  render(root, state, setTriggerValue)
}

function maybeAwardToken(state, setTriggerValue) {
  const threshold = Math.floor(state.score / 150) * 150
  if (threshold <= 0 || threshold > 750 || state.sentThresholds.has(threshold)) return
  state.sentThresholds.add(threshold)
  state.localTokens += 1
  setTriggerValue("token_award", {
    game_id: state.gameId,
    game_type: "block_puzzle",
    threshold,
    score: state.score,
  })
}

function newPiece() {
  const shape = shapes[Math.floor(Math.random() * shapes.length)]
  const look = colors[Math.floor(Math.random() * colors.length)]
  return {
    id: Math.random().toString(16).slice(2),
    name: shape.name,
    cells: shape.cells,
    color: look.color,
    shape: look.shape,
  }
}

function canPlace(board, piece, row, col) {
  return piece.cells.every(([r, c]) => {
    const targetRow = row + r
    const targetCol = col + c
    return targetRow >= 0 && targetCol >= 0 && targetRow < size && targetCol < size && !board[targetRow][targetCol]
  })
}

function hasMove(board, pieces) {
  return pieces.some((piece) => {
    if (!piece) return false
    for (let row = 0; row < size; row += 1) {
      for (let col = 0; col < size; col += 1) {
        if (canPlace(board, piece, row, col)) return true
      }
    }
    return false
  })
}

function clearLines(board) {
  const rows = []
  const cols = []
  for (let row = 0; row < size; row += 1) {
    if (board[row].every(Boolean)) rows.push(row)
  }
  for (let col = 0; col < size; col += 1) {
    let full = true
    for (let row = 0; row < size; row += 1) {
      if (!board[row][col]) full = false
    }
    if (full) cols.push(col)
  }
  rows.forEach((row) => {
    for (let col = 0; col < size; col += 1) board[row][col] = null
  })
  cols.forEach((col) => {
    for (let row = 0; row < size; row += 1) board[row][col] = null
  })
  return rows.length + cols.length
}

function cube(cell) {
  const node = document.createElement("span")
  node.className = `block-cube block-shape-${cell.shape}`
  node.style.background = cell.color
  node.style.boxShadow = `inset 0 -5px 0 rgba(0,0,0,.22), 0 0 14px ${cell.color}66`
  return node
}

function pieceGrid(piece) {
  const maxRow = Math.max(...piece.cells.map(([r]) => r))
  const maxCol = Math.max(...piece.cells.map(([, c]) => c))
  const grid = document.createElement("div")
  grid.className = "block-piece-grid"
  grid.style.gridTemplateColumns = `repeat(${maxCol + 1}, 28px)`
  grid.style.gridTemplateRows = `repeat(${maxRow + 1}, 28px)`
  for (let row = 0; row <= maxRow; row += 1) {
    for (let col = 0; col <= maxCol; col += 1) {
      const cell = document.createElement("span")
      cell.className = "block-mini-cell"
      if (piece.cells.some(([r, c]) => r === row && c === col)) {
        cell.appendChild(cube({ color: piece.color, shape: piece.shape }))
      }
      grid.appendChild(cell)
    }
  }
  return grid
}
"""


_BLOCK_COMPONENT = st.components.v2.component(
    "neon_block_puzzle_game",
    html=HTML,
    css=CSS,
    js=JS,
)


def neon_block_puzzle_game(
    state: dict[str, Any],
    *,
    key: str,
    on_game_over_change: Callable[[], None] | None = None,
    on_token_award_change: Callable[[], None] | None = None,
):
    if on_game_over_change is None:
        on_game_over_change = lambda: None
    if on_token_award_change is None:
        on_token_award_change = lambda: None

    return _BLOCK_COMPONENT(
        key=key,
        data={
            "game_id": state["game_id"],
            "high_score": int(state.get("high_score", 0)),
            "tokens_earned": int(state.get("tokens_earned", 0)),
            "awarded_thresholds": state.get("awarded_thresholds", []),
        },
        on_game_over_change=on_game_over_change,
        on_token_award_change=on_token_award_change,
    )