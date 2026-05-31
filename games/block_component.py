from collections.abc import Callable
from typing import Any

import streamlit as st


HTML = """
<div class="block-neon-shell">
  <div id="notice" class="block-notice">拖曳下方方塊到棋盤上，放開後就會放置。</div>
  <div id="buff" class="block-buff"></div>
  <div id="dragGhost" class="block-drag-ghost" aria-hidden="true"></div>
  <div class="block-neon-top">
    <button class="block-menu" type="button" aria-label="Menu">
      <span class="block-menu-icon"><i></i><i></i><i></i><i></i></span>
      <strong>8×8</strong>
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
  <div id="board" class="block-board" aria-label="方塊消除棋盤"></div>
  <div class="block-tray">
    <div id="pieces" class="block-pieces"></div>
    <button id="undo" class="block-undo" type="button" disabled>
      <span class="block-undo-icon">↶</span>
      <strong>返回上一步</strong>
    </button>
  </div>
</div>
"""

CSS = """
.block-neon-shell {
  --block-mini-size: 21px;
  width: min(100%, 500px);
  margin: 8px auto 14px;
  padding: 12px;
  border-radius: 16px;
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
  gap: 9px;
  align-items: center;
  margin: 8px 0 12px;
}

.block-menu,
.block-score-card,
.block-token-card,
.block-tool,
.block-tray,
.block-undo {
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: #33263d;
  box-shadow: 0 6px 0 rgba(12, 8, 20, 0.48), inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.block-menu {
  height: 40px;
  display: flex;
  gap: 6px;
  align-items: center;
  justify-content: center;
  color: #cf29f4;
  font-size: 15px;
  font-weight: 1000;
  cursor: default;
}

.block-menu-icon {
  display: grid;
  grid-template-columns: repeat(2, 9px);
  gap: 2px;
}

.block-menu-icon i {
  width: 9px;
  height: 9px;
  border-radius: 3px;
  background: #ca27ef;
  box-shadow: 0 0 10px rgba(221, 44, 255, 0.55);
}

.block-menu-icon i:nth-child(4) {
  background: transparent;
  border: 2px solid #ca27ef;
}

.block-score-card {
  height: 44px;
  display: grid;
  place-items: center;
}

.block-score-card span {
  color: #ad36c8;
  font-size: 10px;
  font-weight: 900;
}

.block-score-card strong {
  color: #d931ff;
  font-size: clamp(24px, 4vw, 34px);
  line-height: 0.9;
  text-shadow: 0 0 16px rgba(217, 49, 255, 0.42);
}

.block-token-card {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #ffc13a;
  font-size: 16px;
}

.block-coin {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  color: #ff9f2d;
  background: #ffe28a;
  box-shadow: inset 0 -4px 0 rgba(137, 78, 16, 0.24), 0 0 18px rgba(255, 195, 58, 0.32);
}

.block-notice {
  min-height: 18px;
  margin: 0 4px 8px;
  color: #d9a8e7;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.35;
}

.block-buff {
  min-height: 28px;
  margin: 0 4px 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 5px 9px;
  border-radius: 999px;
  color: #ffe28a;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 12px;
  font-weight: 900;
  white-space: nowrap;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.block-board {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 1.5px;
  padding: 5px;
  margin-top: 2px;
  border-radius: 12px;
  border: 2px solid #b72dec;
  background: #15071c;
  box-shadow:
    0 0 0 3px rgba(255, 69, 221, 0.62),
    inset 0 0 22px rgba(155, 42, 209, 0.26),
    0 0 28px rgba(200, 39, 239, 0.42);
}

.block-cell {
  position: relative;
  overflow: hidden;
  aspect-ratio: 1;
  border: 1px solid #582065;
  border-radius: 3px;
  background: rgba(23, 4, 29, 0.82);
  cursor: pointer;
  transition: filter 120ms ease, transform 120ms ease, box-shadow 120ms ease;
}

.block-cell:hover {
  filter: brightness(1.4);
  transform: translateY(-1px);
}

.block-cell.preview-valid {
  outline: 2px solid rgba(255, 226, 138, 0.84);
  background: rgba(255, 226, 138, 0.16);
}

.block-cell.preview-invalid {
  outline: 2px solid rgba(255, 97, 112, 0.9);
  background: rgba(255, 97, 112, 0.18);
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

.block-preview-cube {
  opacity: 0.52;
  filter: saturate(1.15);
  box-shadow: inset 0 -5px 0 rgba(0, 0, 0, 0.12), 0 0 18px rgba(255, 226, 138, 0.38);
}

.block-preview-cube.invalid {
  background: rgba(255, 97, 112, 0.7) !important;
  box-shadow: inset 0 -5px 0 rgba(0, 0, 0, 0.12), 0 0 16px rgba(255, 97, 112, 0.45);
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
  grid-template-columns: 1fr 104px;
  gap: 7px;
  padding: 7px;
  margin-top: 12px;
}

.block-pieces {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 7px;
}

.block-piece {
  min-height: 54px;
  border: 0;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  cursor: grab;
  touch-action: none;
  display: grid;
  place-items: center;
  padding: 5px;
  user-select: none;
  transition: transform 130ms ease, box-shadow 130ms ease, background 130ms ease;
}

.block-piece:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.08);
}

.block-piece.dragging {
  cursor: grabbing;
  transform: translateY(-4px) scale(1.03);
  box-shadow: 0 0 20px rgba(255, 226, 138, 0.34);
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

.block-undo {
  min-height: 54px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 4px;
  color: #ffe28a;
  cursor: pointer;
  font-weight: 1000;
  transition: transform 130ms ease, filter 130ms ease, box-shadow 130ms ease;
}

.block-undo:hover:not(:disabled) {
  transform: translateY(-2px);
  filter: brightness(1.08);
  box-shadow: 0 0 22px rgba(255, 226, 138, 0.28), 0 6px 0 rgba(12, 8, 20, 0.48);
}

.block-undo:disabled {
  opacity: 0.38;
  cursor: not-allowed;
}

.block-undo-icon {
  font-size: 20px;
  line-height: 1;
}

.block-piece-grid {
  display: grid;
  place-items: center;
  justify-content: center;
  align-content: center;
  gap: 4px;
}

.block-drag-ghost {
  position: fixed;
  left: 0;
  top: 0;
  z-index: 9999;
  pointer-events: none;
  opacity: 0;
  transform: translate(-999px, -999px) scale(1.08);
  padding: 12px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.12);
  box-shadow: 0 18px 34px rgba(0, 0, 0, 0.35), 0 0 22px rgba(255, 226, 138, 0.34);
  transition: opacity 90ms ease;
}

.block-drag-ghost.is-visible {
  opacity: 0.92;
}

.block-mini-cell {
  display: block;
  width: var(--block-mini-size, 21px);
  height: var(--block-mini-size, 21px);
}

@media (min-width: 900px) and (max-height: 820px) {
  .block-neon-shell {
    --block-mini-size: 19px;
    width: min(100%, 460px);
  }
  .block-piece { min-height: 50px; }
  .block-undo { min-height: 50px; }
}

@media (min-width: 900px) and (max-height: 740px) {
  .block-neon-shell {
    --block-mini-size: 17px;
    width: min(100%, 430px);
  }
  .block-score-card { height: 40px; }
  .block-menu,
  .block-token-card { height: 38px; }
}

@media (max-width: 700px) {
  .block-neon-shell { --block-mini-size: 19px; padding: 9px; border-radius: 14px; }
  .block-neon-top { grid-template-columns: 0.9fr 1.2fr 0.9fr; gap: 7px; margin: 7px 0 10px; }
  .block-tray { grid-template-columns: 1fr 88px; }
  .block-pieces { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; }
  .block-piece { min-height: 58px; padding: 5px; }
  .block-undo { min-height: 58px; }
  .block-tool { width: 120px; }
  .block-mini-cell { width: 20px; height: 20px; }
}

@media (max-width: 430px) {
  .block-neon-shell {
    --block-mini-size: 16px;
    width: 100%;
    padding: 8px;
    margin: 6px 0 10px;
  }
  .block-score-card { height: 36px; }
  .block-score-card strong { font-size: 24px; }
  .block-menu,
  .block-token-card { height: 36px; font-size: 14px; }
  .block-board {
    gap: 1.5px;
    padding: 4px;
    border-width: 2px;
    border-radius: 12px;
  }
  .block-cell { border-width: 1px; }
  .block-tray { grid-template-columns: 1fr 70px; padding: 6px; gap: 6px; margin-top: 9px; }
  .block-pieces { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .block-piece {
    min-height: 46px;
    padding: 4px;
  }
  .block-undo { min-height: 46px; font-size: 12px; }
  .block-mini-cell { width: 16px; height: 16px; }
  .block-notice,
  .block-buff { font-size: 10px; }
  .block-notice { margin-bottom: 6px; }
  .block-buff { min-height: 24px; margin-bottom: 8px; padding: 4px 7px; }
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
const smallShapes = [
  { name: "單格", cells: [[0, 0]] },
  { name: "兩格直線", cells: [[0, 0], [0, 1]] },
  { name: "兩格直線", cells: [[0, 0], [1, 0]] },
]
const mediumShapes = [
  { name: "三格直線", cells: [[0, 0], [0, 1], [0, 2]] },
  { name: "三格直線", cells: [[0, 0], [1, 0], [2, 0]] },
  { name: "L 型", cells: [[0, 0], [1, 0], [1, 1]] },
  { name: "L 型", cells: [[0, 1], [1, 1], [1, 0]] },
  { name: "2x2 方塊", cells: [[0, 0], [0, 1], [1, 0], [1, 1]] },
  { name: "T 型", cells: [[0, 0], [0, 1], [0, 2], [1, 1]] },
  { name: "短折線", cells: [[0, 0], [0, 1], [1, 1]] },
  { name: "短折線", cells: [[0, 1], [1, 1], [1, 0]] },
]
const largeShapes = [
  { name: "四格直線", cells: [[0, 0], [0, 1], [0, 2], [0, 3]] },
  { name: "四格直線", cells: [[0, 0], [1, 0], [2, 0], [3, 0]] },
  { name: "3x2 長方形", cells: [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2]] },
  { name: "2x3 長方形", cells: [[0, 0], [0, 1], [1, 0], [1, 1], [2, 0], [2, 1]] },
  { name: "大 L 型", cells: [[0, 0], [1, 0], [2, 0], [2, 1], [2, 2]] },
  { name: "大 L 型", cells: [[0, 2], [1, 2], [2, 0], [2, 1], [2, 2]] },
  { name: "大 T 型", cells: [[0, 0], [0, 1], [0, 2], [1, 1], [2, 1]] },
  { name: "Z 型", cells: [[0, 0], [0, 1], [1, 1], [1, 2]] },
  { name: "S 型", cells: [[0, 1], [0, 2], [1, 0], [1, 1]] },
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
  const scoreMultiplier = clamp(Number(data?.score_multiplier ?? 1), 1, 1.25)
  return {
    gameId,
    board: Array.from({ length: size }, () => Array.from({ length: size }, () => null)),
    // null = 已用完，等補充；非 null = 可用
    pieces: [newPiece(), newPiece(), newPiece()],
    selected: 0,
    score: Math.max(0, Math.round(Number(data?.bonus_start_score ?? 0))),
    scoreMultiplier,
    rescueChances: Math.max(0, Math.min(1, Math.round(Number(data?.rescue_chances ?? 0)))),
    buffLabel: data?.modifier_label ?? data?.buff_label ?? "",
    abilityEvents: [],
    highScore: Number(data?.high_score ?? 0),
    serverTokens: Number(data?.tokens_earned ?? 0),
    localTokens: 0,
    sentThresholds: new Set((data?.awarded_thresholds ?? []).map(Number)),
    placements: [],
    undoSnapshot: null,
    dragging: null,
    preview: null,
    gameOver: false,
    notice: "拖曳下方方塊到棋盤上，放開後就會放置。",
  }
}

function render(root, state, setTriggerValue) {
  root.querySelector("#score").textContent = String(state.score)
  root.querySelector("#tokens").textContent = String(state.serverTokens + state.localTokens)
  root.querySelector("#notice").textContent = state.notice
  const rescueText = state.rescueChances > 0 ? `｜換牌還有 ${state.rescueChances} 次` : ""
  root.querySelector("#buff").textContent = state.buffLabel ? `本局助力：${state.buffLabel}${rescueText}` : "本局沒有額外助力"
  const undoButton = root.querySelector("#undo")
  if (undoButton) {
    undoButton.disabled = !state.undoSnapshot || state.gameOver
    undoButton.onclick = () => undoLastMove(state, root, setTriggerValue)
  }

  const board = root.querySelector("#board")
  board.innerHTML = ""
  state.board.forEach((row, rowIndex) => {
    row.forEach((cell, colIndex) => {
      const button = document.createElement("button")
      button.className = "block-cell"
      button.type = "button"
      button.dataset.row = String(rowIndex)
      button.dataset.col = String(colIndex)
      button.setAttribute("aria-label", `放在 ${rowIndex + 1}, ${colIndex + 1}`)
      if (cell) button.appendChild(cube(cell))
      const previewInfo = previewForCell(state, rowIndex, colIndex)
      if (previewInfo) {
        button.classList.add(previewInfo.valid ? "preview-valid" : "preview-invalid")
        if (!cell) button.appendChild(previewCube(previewInfo.piece, previewInfo.valid))
      }
      button.onclick = () => place(state, rowIndex, colIndex, setTriggerValue, root)
      board.appendChild(button)
    })
  })
  board.onpointermove = (event) => updateDragPreview(root, state, event, setTriggerValue)
  board.onpointerleave = () => {
    if (!state.dragging) return
    state.preview = null
    render(root, state, setTriggerValue)
  }
  board.onpointerup = (event) => finishDrag(root, state, event, setTriggerValue)

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
      const isDragging = state.dragging?.pieceIndex === index
      button.className = `block-piece${isSelected ? " active" : ""}${isDragging ? " dragging" : ""}`
      button.setAttribute("aria-label", `拖曳 ${piece.name}`)
      button.onpointerdown = (event) => startDrag(root, state, index, event, setTriggerValue)
      button.appendChild(pieceGrid(piece))
    }
    pieces.appendChild(button)
  })
}

function place(state, row, col, setTriggerValue, root, pieceIndex = state.selected) {
  if (state.gameOver) return

  const piece = state.pieces[pieceIndex]
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

  state.undoSnapshot = makeUndoSnapshot(state)

  // 放置
  piece.cells.forEach(([r, c]) => {
    state.board[row + r][col + c] = { color: piece.color, shape: piece.shape }
  })
  const cleared = clearLines(state.board)
  const placedScore = piece.cells.length * 10
  const lineScore = cleared * 50
  const combo = Math.max(0, cleared - 1) * 25
  const baseScore = placedScore + lineScore + combo
  const earnedScore = addScore(state, baseScore)
  state.score += earnedScore
  state.highScore = Math.max(state.highScore, state.score)
  state.placements.push({
    piece_name: piece.name,
    cells: piece.cells.length,
    row,
    col,
    score_after: state.score,
    base_score: baseScore,
    score_earned: earnedScore,
    cleared_lines: cleared,
  })

  // 標記為已用
  state.pieces[pieceIndex] = null

  // 三個都用完才補充新的三個
  if (state.pieces.every(p => p === null)) {
    state.pieces = [newPiece(), newPiece(), newPiece()]
    state.selected = 0
    state.notice = cleared
      ? `消除 ${cleared} 條線，得到 ${earnedScore} 分！三個方塊用完，補充新的三個。`
      : `三個方塊都用完了，補充新的三個！`
  } else {
    // 自動選下一個可用的方塊
    const next = state.pieces.findIndex(p => p !== null)
    if (next !== -1) state.selected = next
    state.notice = cleared ? `消除 ${cleared} 條線，得到 ${earnedScore} 分！` : `放好了，+${earnedScore} 分。`
  }

  maybeAwardToken(state, setTriggerValue)

  // 用剩餘可用方塊判斷 game over
  const remaining = state.pieces.filter(p => p !== null)
  if (!hasMove(state.board, remaining)) {
    if (useRescue(state, root, setTriggerValue)) {
      render(root, state, setTriggerValue)
      return
    }
    state.gameOver = true
    state.notice = "目前沒有地方可以放囉！"
    setTriggerValue("game_over", {
      game_id: state.gameId,
      game_type: "block_puzzle",
      score: state.score,
      high_score: state.highScore,
      game_over_reason: "no_valid_moves",
      placements: state.placements,
      ability_events: state.abilityEvents,
    })
  }

  render(root, state, setTriggerValue)
}

function startDrag(root, state, pieceIndex, event, setTriggerValue) {
  if (state.gameOver || !state.pieces[pieceIndex]) return
  event.preventDefault()
  event.stopPropagation()
  state.selected = pieceIndex
  state.dragging = { pieceIndex }
  state.preview = null
  state.notice = `拖曳「${state.pieces[pieceIndex].name}」到棋盤上，看到亮亮預覽後放開。`
  event.currentTarget?.classList?.add("dragging")
  root.querySelector("#notice").textContent = state.notice
  renderDragGhost(root, state, event)
  const moveHandler = (moveEvent) => updateDragPreview(root, state, moveEvent, setTriggerValue)
  const upHandler = (upEvent) => {
    const view = root.ownerDocument.defaultView ?? window
    view.removeEventListener("pointermove", moveHandler)
    view.removeEventListener("pointerup", upHandler)
    finishDrag(root, state, upEvent, setTriggerValue)
  }
  const view = root.ownerDocument.defaultView ?? window
  view.addEventListener("pointermove", moveHandler)
  view.addEventListener("pointerup", upHandler)
}

function updateDragPreview(root, state, event, setTriggerValue) {
  if (!state.dragging) return
  event.preventDefault()
  renderDragGhost(root, state, event)
  const cell = cellFromPointer(root, event)
  if (!cell) {
    if (state.preview !== null) {
      state.preview = null
      render(root, state, setTriggerValue)
    }
    return
  }
  const row = Number(cell.dataset.row)
  const col = Number(cell.dataset.col)
  const piece = state.pieces[state.dragging.pieceIndex]
  if (!piece || !Number.isFinite(row) || !Number.isFinite(col)) return
  const valid = canPlace(state.board, piece, row, col)
  const nextPreview = { row, col, valid, pieceIndex: state.dragging.pieceIndex }
  if (!samePreview(state.preview, nextPreview)) {
    state.preview = nextPreview
    render(root, state, setTriggerValue)
  }
}

function finishDrag(root, state, event, setTriggerValue) {
  if (!state.dragging) return
  updateDragPreview(root, state, event, setTriggerValue)
  const preview = state.preview
  const pieceIndex = state.dragging.pieceIndex
  state.dragging = null
  state.preview = null
  hideDragGhost(root)
  if (preview?.valid) {
    place(state, preview.row, preview.col, setTriggerValue, root, pieceIndex)
    return
  }
  state.notice = preview ? "這個位置放不下喔，換個地方試試看。" : "拖到棋盤格子上，看到預覽後再放開。"
  render(root, state, setTriggerValue)
}

function useRescue(state, root, setTriggerValue) {
  if (state.rescueChances <= 0) return false
  state.rescueChances -= 1
  state.pieces = [newPiece(), newPiece(), newPiece()]
  state.selected = 0
  state.notice = "角色幫你換了一組方塊，再慢慢試一次。"
  state.abilityEvents.push({
    label: "角色換牌",
    message: "角色在卡住時幫你換了一組方塊。",
  })
  return hasMove(state.board, state.pieces)
}

function makeUndoSnapshot(state) {
  return {
    board: cloneBoard(state.board),
    pieces: clonePieces(state.pieces),
    selected: state.selected,
    score: state.score,
    highScore: state.highScore,
    localTokens: state.localTokens,
    serverTokens: state.serverTokens,
    sentThresholds: Array.from(state.sentThresholds),
    placements: state.placements.map((placement) => ({ ...placement })),
    rescueChances: state.rescueChances,
    abilityEvents: state.abilityEvents.map((event) => ({ ...event })),
    notice: state.notice,
  }
}

function undoLastMove(state, root, setTriggerValue) {
  const snapshot = state.undoSnapshot
  if (!snapshot) {
    state.notice = "目前沒有可以返回的步驟。"
    render(root, state, setTriggerValue)
    return
  }
  const snapshotThresholds = new Set(snapshot.sentThresholds)
  const revertedThresholds = Array.from(state.sentThresholds).filter((threshold) => !snapshotThresholds.has(threshold))
  state.board = cloneBoard(snapshot.board)
  state.pieces = clonePieces(snapshot.pieces)
  state.selected = snapshot.selected
  state.score = snapshot.score
  state.highScore = snapshot.highScore
  state.localTokens = snapshot.localTokens
  state.serverTokens = snapshot.serverTokens
  state.sentThresholds = new Set(snapshot.sentThresholds)
  state.placements = snapshot.placements.map((placement) => ({ ...placement }))
  state.rescueChances = snapshot.rescueChances
  state.abilityEvents = snapshot.abilityEvents.map((event) => ({ ...event }))
  state.dragging = null
  state.preview = null
  state.gameOver = false
  state.undoSnapshot = null
  state.notice = "已返回上一步，可以重新試一個位置。"
  setTriggerValue("undo_move", {
    game_id: state.gameId,
    game_type: "block_puzzle",
    score: state.score,
    high_score: state.highScore,
    placements: state.placements,
    tokens_earned: state.serverTokens + state.localTokens,
    awarded_thresholds: Array.from(state.sentThresholds),
    reverted_thresholds: revertedThresholds,
  })
  render(root, state, setTriggerValue)
}

function cloneBoard(board) {
  return board.map((row) => row.map((cell) => (cell ? { ...cell } : null)))
}

function clonePieces(pieces) {
  return pieces.map((piece) => piece ? { ...piece, cells: piece.cells.map(([row, col]) => [row, col]) } : null)
}

function previewForCell(state, row, col) {
  const preview = state.preview
  if (!preview) return null
  const piece = state.pieces[preview.pieceIndex]
  if (!piece) return null
  const hit = piece.cells.some(([r, c]) => preview.row + r === row && preview.col + c === col)
  return hit ? { ...preview, piece } : null
}

function samePreview(a, b) {
  if (!a || !b) return a === b
  return a.row === b.row && a.col === b.col && a.valid === b.valid && a.pieceIndex === b.pieceIndex
}

function cellFromPointer(root, event) {
  const board = root.querySelector("#board")
  if (!board) return null
  const boardRect = board.getBoundingClientRect()
  if (
    event.clientX < boardRect.left ||
    event.clientX > boardRect.right ||
    event.clientY < boardRect.top ||
    event.clientY > boardRect.bottom
  ) {
    return null
  }

  const cells = Array.from(board.querySelectorAll(".block-cell"))
  return cells.find((cell) => {
    const rect = cell.getBoundingClientRect()
    return (
      event.clientX >= rect.left &&
      event.clientX <= rect.right &&
      event.clientY >= rect.top &&
      event.clientY <= rect.bottom
    )
  }) ?? null
}

function renderDragGhost(root, state, event) {
  const ghost = root.querySelector("#dragGhost")
  const piece = state.pieces[state.dragging?.pieceIndex]
  if (!ghost || !piece) return
  if (!ghost.dataset.pieceId || ghost.dataset.pieceId !== piece.id) {
    ghost.innerHTML = ""
    ghost.appendChild(pieceGrid(piece))
    ghost.dataset.pieceId = piece.id
  }
  ghost.classList.add("is-visible")
  ghost.style.transform = `translate(${event.clientX + 14}px, ${event.clientY + 14}px) scale(1.08)`
}

function hideDragGhost(root) {
  const ghost = root.querySelector("#dragGhost")
  if (!ghost) return
  ghost.classList.remove("is-visible")
  ghost.style.transform = "translate(-999px, -999px) scale(1.08)"
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

function addScore(state, basePoints) {
  return Math.max(1, Math.round(Number(basePoints) * state.scoreMultiplier))
}

function newPiece() {
  const roll = Math.random()
  const pool = roll < 0.20 ? smallShapes : roll < 0.55 ? mediumShapes : largeShapes
  const shape = pool[Math.floor(Math.random() * pool.length)]
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

function previewCube(piece, valid) {
  const node = cube({ color: piece.color, shape: piece.shape })
  node.classList.add("block-preview-cube")
  if (!valid) node.classList.add("invalid")
  return node
}

function pieceGrid(piece) {
  const maxRow = Math.max(...piece.cells.map(([r]) => r))
  const maxCol = Math.max(...piece.cells.map(([, c]) => c))
  const grid = document.createElement("div")
  grid.className = "block-piece-grid"
  grid.style.gridTemplateColumns = `repeat(${maxCol + 1}, var(--block-mini-size, 21px))`
  grid.style.gridTemplateRows = `repeat(${maxRow + 1}, var(--block-mini-size, 21px))`
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

function clamp(value, min, max) {
  if (!Number.isFinite(value)) return min
  return Math.max(min, Math.min(max, value))
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
    on_undo_move_change: Callable[[], None] | None = None,
):
    if on_game_over_change is None:
        on_game_over_change = lambda: None
    if on_token_award_change is None:
        on_token_award_change = lambda: None
    if on_undo_move_change is None:
        on_undo_move_change = lambda: None
    modifiers = state.get("active_modifiers") or state.get("active_buff") or {}

    return _BLOCK_COMPONENT(
        key=key,
        data={
            "game_id": state["game_id"],
            "high_score": int(state.get("high_score", 0)),
            "tokens_earned": int(state.get("tokens_earned", 0)),
            "awarded_thresholds": state.get("awarded_thresholds", []),
            "score_multiplier": float(modifiers.get("score_multiplier") or 1.0),
            "bonus_start_score": int(modifiers.get("bonus_start_score") or 0),
            "rescue_chances": int(modifiers.get("rescue_chances") or 0),
            "modifier_label": modifiers.get("summary_label") if modifiers.get("applies") else "",
            "buff_label": modifiers.get("buff_label") if modifiers.get("applies") else "",
        },
        on_game_over_change=on_game_over_change,
        on_token_award_change=on_token_award_change,
        on_undo_move_change=on_undo_move_change,
    )
