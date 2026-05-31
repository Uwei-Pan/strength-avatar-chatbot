from collections.abc import Callable
from typing import Any

import streamlit as st


HTML = """
<div class="slither-shell">
  <div class="slither-canvas-wrap">
    <canvas id="slither-canvas" width="760" height="480" aria-label="貪食蛇遊戲畫布"></canvas>
    <div id="overlay" class="slither-overlay hidden"></div>
  </div>
  <div class="slither-topbar">
    <div>
      <span class="slither-label">分數</span>
      <strong id="score">0</strong>
    </div>
    <div>
      <span class="slither-label">長度</span>
      <strong id="length">3</strong>
    </div>
    <div>
      <span class="slither-label">本局代幣</span>
      <strong id="tokens">0</strong>
    </div>
  </div>
  <div id="buff" class="slither-buff"></div>
  <div class="slither-help">手機可用手指點按或拖曳操控；電腦可用方向鍵或滑鼠轉向。小光點基礎 +10，大顆優勢果實基礎 +40。</div>
</div>
"""

CSS = """
.slither-shell {
  position: relative;
  width: min(100%, 720px);
  margin: 0 auto;
  padding: 9px;
  border-radius: 16px;
  background:
    radial-gradient(circle at 18% 18%, rgba(255, 209, 102, 0.22), transparent 28%),
    radial-gradient(circle at 84% 20%, rgba(126, 240, 161, 0.16), transparent 30%),
    linear-gradient(135deg, #11183b 0%, #16265b 48%, #1b214c 100%);
  border: 1px solid rgba(255, 255, 255, 0.24);
  box-shadow: 0 22px 60px rgba(12, 18, 48, 0.35);
  color: #f7fbff;
  box-sizing: border-box;
}

.slither-topbar {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 7px;
  margin-top: 7px;
}

.slither-topbar > div {
  min-width: 0;
  padding: 6px 8px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(8px);
}

.slither-label {
  display: block;
  margin-bottom: 2px;
  color: rgba(247, 251, 255, 0.72);
  font-size: 10px;
  font-weight: 800;
}

.slither-topbar strong {
  font-size: 16px;
  line-height: 1.1;
}

#slither-canvas {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 14px;
  background: #090e27;
  outline: 3px solid rgba(255, 255, 255, 0.16);
  touch-action: none;
  user-select: none;
}

.slither-canvas-wrap {
  position: relative;
}

.slither-help {
  display: none;
  margin-top: 4px;
  color: rgba(247, 251, 255, 0.78);
  font-size: 12px;
  font-weight: 700;
  text-align: center;
}

.slither-buff {
  margin-top: 7px;
  min-height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3px 7px;
  border-radius: 999px;
  color: #fff7a8;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.14);
  font-size: 11px;
  font-weight: 900;
  white-space: nowrap;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.slither-overlay {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  border-radius: 18px;
  background: rgba(9, 14, 39, 0.72);
  color: #ffffff;
  text-align: center;
  font-weight: 900;
  backdrop-filter: blur(3px);
}

.slither-overlay.hidden {
  display: none;
}

@media (max-width: 560px) {
  .slither-shell { padding: 6px; border-radius: 14px; }
  .slither-topbar { gap: 4px; }
  .slither-topbar > div { padding: 4px 5px; border-radius: 10px; }
  .slither-topbar strong { font-size: 15px; }
  .slither-overlay { inset: 0; }
}

@media (max-width: 430px) {
  .slither-shell {
    width: 100%;
    padding: 5px;
  }
  #slither-canvas {
    aspect-ratio: 5 / 4;
    border-radius: 12px;
    outline-width: 2px;
  }
  .slither-label {
    font-size: 9px;
  }
  .slither-help {
    font-size: 10px;
    line-height: 1.45;
  }
  .slither-buff {
    border-radius: 12px;
    text-align: center;
  }
}
"""

JS = """
const instances = new WeakMap()
const BASE_SNAKE_SPEED = 1.35
const SNAKE_COUNTDOWN_MS = 5000

export default function (component) {
  const { data, parentElement, setTriggerValue } = component
  const canvas = parentElement.querySelector("#slither-canvas")
  const scoreNode = parentElement.querySelector("#score")
  const lengthNode = parentElement.querySelector("#length")
  const tokenNode = parentElement.querySelector("#tokens")
  const buffNode = parentElement.querySelector("#buff")
  const overlay = parentElement.querySelector("#overlay")
  if (!canvas || !scoreNode || !lengthNode || !tokenNode || !buffNode || !overlay) return

  const ctx = canvas.getContext("2d")
  const gameId = data?.game_id ?? "demo"
  let instance = instances.get(parentElement)
  if (!instance || instance.gameId !== gameId) {
    instance = createGame(gameId, data)
    instances.set(parentElement, instance)
  } else {
    const incomingTokens = Number(data?.tokens_earned ?? instance.serverTokens ?? 0)
    if (incomingTokens > instance.serverTokens) {
      instance.localTokens = 0
    }
    instance.serverTokens = incomingTokens
  }
  instance.paused = Boolean(data?.paused)

  const resizeCanvas = () => {
    const rect = canvas.getBoundingClientRect()
    const ratio = window.devicePixelRatio || 1
    const displayWidth = Math.max(280, rect.width)
    const displayHeight = Math.max(220, rect.height || rect.width * 9 / 16)
    const shouldWaitForTouch = isTouchPlayfield(displayWidth)
    canvas.width = Math.floor(displayWidth * ratio)
    canvas.height = Math.floor(displayHeight * ratio)
    instance.scale = ratio
    instance.width = displayWidth
    instance.height = displayHeight
    if (instance.needsResizeReset) {
      resetPlayfield(instance)
      instance.waitingForTouch = false
      instance.needsResizeReset = false
    } else {
      keepInsidePlayfield(instance)
      if (!shouldWaitForTouch) instance.waitingForTouch = false
    }
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
  }
  resizeCanvas()

  const keyHandler = (event) => {
    const key = event.key.toLowerCase()
    if (key === " " || key === "spacebar") {
      event.preventDefault()
      instance.paused = !instance.paused
      setTriggerValue("pause_toggle", {
        game_id: instance.gameId,
        game_type: "snake",
        paused: instance.paused,
      })
      return
    }
    const map = {
      arrowup: -Math.PI / 2,
      w: -Math.PI / 2,
      arrowdown: Math.PI / 2,
      s: Math.PI / 2,
      arrowleft: Math.PI,
      a: Math.PI,
      arrowright: 0,
      d: 0,
    }
    if (key in map) {
      event.preventDefault()
      instance.waitingForTouch = false
      instance.targetAngle = map[key]
    }
  }

  const pointerHandler = (event) => {
    event.preventDefault()
    const rect = canvas.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top
    instance.waitingForTouch = false
    instance.targetAngle = Math.atan2(y - instance.head.y, x - instance.head.x)
  }

  const pointerDownHandler = (event) => {
    pointerHandler(event)
    canvas.setPointerCapture?.(event.pointerId)
  }

  const pointerUpHandler = (event) => {
    canvas.releasePointerCapture?.(event.pointerId)
  }

  if (instance.cleanup) instance.cleanup()
  window.addEventListener("keydown", keyHandler)
  window.addEventListener("resize", resizeCanvas)
  canvas.addEventListener("pointerdown", pointerDownHandler)
  canvas.addEventListener("pointermove", pointerHandler)
  canvas.addEventListener("pointerup", pointerUpHandler)
  canvas.addEventListener("pointercancel", pointerUpHandler)
  instance.cleanup = () => {
    window.removeEventListener("keydown", keyHandler)
    window.removeEventListener("resize", resizeCanvas)
    canvas.removeEventListener("pointerdown", pointerDownHandler)
    canvas.removeEventListener("pointermove", pointerHandler)
    canvas.removeEventListener("pointerup", pointerUpHandler)
    canvas.removeEventListener("pointercancel", pointerUpHandler)
  }

  const tick = () => {
    if (!instances.has(parentElement)) return
    if (!instance.gameOver && !instance.waitingForTouch && !instance.paused && countdownRemainingMs(instance) <= 0) {
      update(instance, setTriggerValue)
    }
    draw(ctx, instance, scoreNode, lengthNode, tokenNode, buffNode, overlay)
    instance.frame = window.requestAnimationFrame(tick)
  }
  if (!instance.frame) {
    instance.frame = window.requestAnimationFrame(tick)
  }

  return () => {
    instance.cleanup?.()
    instance.cleanup = null
    if (instance.frame) window.cancelAnimationFrame(instance.frame)
    instance.frame = null
  }
}

function createGame(gameId, data) {
  const width = 760
  const height = 480
  const head = { x: width / 2, y: height / 2 }
  const scoreMultiplier = clamp(Number(data?.score_multiplier ?? 1), 1, 1.25)
  const speedMultiplier = clamp(Number(data?.speed_multiplier ?? 1), 0.78, 1.08)
  const shieldCharges = Math.max(0, Math.min(1, Math.round(Number(data?.shield_charges ?? 0))))
  const state = {
    gameId,
    width,
    height,
    head,
    angle: 0,
    targetAngle: 0,
    speed: BASE_SNAKE_SPEED * speedMultiplier,
    scoreMultiplier,
    speedMultiplier,
    turnRate: clamp(Number(data?.turn_rate ?? 0.09), 0.065, 0.09),
    shieldCharges,
    strengthFruitBonus: Math.max(0, Math.min(15, Math.round(Number(data?.strength_fruit_bonus ?? 0)))),
    buffLabel: data?.modifier_label ?? data?.buff_label ?? "",
    abilityEvents: [],
    radius: 11,
    maxPoints: 58,
    points: [],
    foods: [],
    obstacles: [],
    difficultyLevel: 0,
    score: Math.max(0, Math.round(Number(data?.bonus_start_score ?? 0))),
    serverTokens: Number(data?.tokens_earned ?? 0),
    localTokens: 0,
    sentThresholds: new Set((data?.awarded_thresholds ?? []).map(Number)),
    fruits: [],
    strengthFruit: null,
    frame: null,
    gameOver: false,
    reason: "",
    needsResizeReset: true,
    waitingForTouch: false,
    paused: Boolean(data?.paused),
    countdownStartedAtMs: Number(data?.countdown_started_at_ms ?? Date.now()),
    countdownMs: SNAKE_COUNTDOWN_MS,
    cleanup: null,
  }
  for (let index = 0; index < 46; index += 1) {
    state.points.push({ x: head.x - index * 4, y: head.y })
  }
  for (let index = 0; index < 28; index += 1) spawnFood(state)
  state.strengthFruit = spawnStrengthFruit(state)
  return state
}

function resetPlayfield(state) {
  state.head = { x: state.width / 2, y: state.height / 2 }
  state.angle = 0
  state.targetAngle = 0
  state.points = []
  for (let index = 0; index < 46; index += 1) {
    state.points.push({ x: state.head.x - index * 4, y: state.head.y })
  }
  state.foods = []
  for (let index = 0; index < 28; index += 1) spawnFood(state)
  state.obstacles = []
  updateObstaclesByLength(state)
  state.strengthFruit = spawnStrengthFruit(state)
}

function keepInsidePlayfield(state) {
  const margin = state.radius + 8
  state.head.x = Math.max(margin, Math.min(state.width - margin, state.head.x))
  state.head.y = Math.max(margin, Math.min(state.height - margin, state.head.y))
  state.points = state.points.map((point) => ({
    x: Math.max(margin, Math.min(state.width - margin, point.x)),
    y: Math.max(margin, Math.min(state.height - margin, point.y)),
  }))
  for (const food of state.foods) {
    food.x = Math.max(24, Math.min(state.width - 24, food.x))
    food.y = Math.max(24, Math.min(state.height - 24, food.y))
  }
  if (state.strengthFruit) {
    const fruitMargin = state.strengthFruit.radius + 12
    state.strengthFruit.x = Math.max(fruitMargin, Math.min(state.width - fruitMargin, state.strengthFruit.x))
    state.strengthFruit.y = Math.max(fruitMargin, Math.min(state.height - fruitMargin, state.strengthFruit.y))
  }
  for (const obstacle of state.obstacles ?? []) {
    const obstacleMargin = obstacle.radius + 8
    obstacle.x = Math.max(obstacleMargin, Math.min(state.width - obstacleMargin, obstacle.x))
    obstacle.y = Math.max(obstacleMargin, Math.min(state.height - obstacleMargin, obstacle.y))
  }
}

function update(state, setTriggerValue) {
  updateObstaclesByLength(state)
  state.angle = turnToward(state.angle, state.targetAngle, state.turnRate)
  state.head.x += Math.cos(state.angle) * state.speed
  state.head.y += Math.sin(state.angle) * state.speed
  state.points.unshift({ x: state.head.x, y: state.head.y })
  while (state.points.length > state.maxPoints) state.points.pop()

  const margin = state.radius + 4
  if (
    state.head.x < margin ||
    state.head.y < margin ||
    state.head.x > state.width - margin ||
    state.head.y > state.height - margin
  ) {
    if (useShield(state, "hit_wall")) return
    finish(state, "hit_wall", setTriggerValue)
    return
  }

  for (let index = 28; index < state.points.length; index += 1) {
    if (distance(state.head, state.points[index]) < state.radius * 1.45) {
      if (useShield(state, "hit_self")) return
      finish(state, "hit_self", setTriggerValue)
      return
    }
  }

  for (const obstacle of state.obstacles ?? []) {
    if (distance(state.head, obstacle) < state.radius + obstacle.radius * 0.82) {
      if (useShield(state, "hit_obstacle")) return
      finish(state, "hit_obstacle", setTriggerValue)
      return
    }
  }

  moveStrengthFruit(state)
  if (state.strengthFruit && distance(state.head, state.strengthFruit) < state.radius + state.strengthFruit.radius) {
    const fruit = state.strengthFruit
    const earned = addScore(state, fruit.points)
    state.score += earned
    state.maxPoints += 18
    state.fruits.push({
      strength_name: fruit.strength,
      fruit_name: `${fruit.strength}果實`,
      score_after: state.score,
      points: earned,
      base_points: fruit.points,
      is_strength_fruit: true,
    })
    state.strengthFruit = spawnStrengthFruit(state)
    maybeAwardToken(state, setTriggerValue)
  }

  for (let index = state.foods.length - 1; index >= 0; index -= 1) {
    const food = state.foods[index]
    if (distance(state.head, food) < state.radius + food.radius) {
      state.foods.splice(index, 1)
      state.score += addScore(state, 10)
      state.maxPoints += 7
      spawnFood(state)
      maybeAwardToken(state, setTriggerValue)
    }
  }
}

function draw(ctx, state, scoreNode, lengthNode, tokenNode, buffNode, overlay) {
  ctx.clearRect(0, 0, state.width, state.height)
  const gradient = ctx.createLinearGradient(0, 0, state.width, state.height)
  gradient.addColorStop(0, "#080c24")
  gradient.addColorStop(0.55, "#132765")
  gradient.addColorStop(1, "#1e1844")
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, state.width, state.height)

  ctx.save()
  ctx.globalAlpha = 0.28
  ctx.strokeStyle = "#ffffff"
  ctx.lineWidth = 1
  for (let x = 24; x < state.width; x += 40) {
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, state.height)
    ctx.stroke()
  }
  for (let y = 24; y < state.height; y += 40) {
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(state.width, y)
    ctx.stroke()
  }
  ctx.restore()

  drawObstacles(ctx, state)

  for (const food of state.foods) {
    const glow = ctx.createRadialGradient(food.x, food.y, 1, food.x, food.y, food.radius * 3.2)
    glow.addColorStop(0, food.color)
    glow.addColorStop(1, "rgba(255,255,255,0)")
    ctx.fillStyle = glow
    ctx.beginPath()
    ctx.arc(food.x, food.y, food.radius * 3.2, 0, Math.PI * 2)
    ctx.fill()
    ctx.fillStyle = food.color
    ctx.beginPath()
    ctx.arc(food.x, food.y, food.radius, 0, Math.PI * 2)
    ctx.fill()
  }

  if (state.strengthFruit) {
    drawStrengthFruit(ctx, state.strengthFruit, state)
  }

  for (let index = state.points.length - 1; index >= 0; index -= 1) {
    const point = state.points[index]
    const t = index / Math.max(1, state.points.length - 1)
    const radius = Math.max(5, state.radius * (1 - t * 0.42))
    ctx.fillStyle = index === 0 ? "#fff07a" : `hsl(${170 + index * 2}, 88%, ${62 - t * 18}%)`
    ctx.shadowColor = index === 0 ? "#fff07a" : "#62f3cc"
    ctx.shadowBlur = index === 0 ? 18 : 9
    ctx.beginPath()
    ctx.arc(point.x, point.y, radius, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.shadowBlur = 0

  scoreNode.textContent = String(state.score)
  lengthNode.textContent = String(Math.max(3, Math.round(state.maxPoints / 18)))
  tokenNode.textContent = String(state.serverTokens + state.localTokens)
  const shieldText = state.shieldCharges > 0 ? `｜守護還有 ${state.shieldCharges} 次` : ""
  buffNode.textContent = state.buffLabel ? `本局助力：${state.buffLabel}${shieldText}` : "本局沒有額外助力"

  if (state.gameOver) {
    const reasonLabels = {
      hit_self: "你撞到自己了！",
      hit_obstacle: "你碰到星岩障礙了！",
      hit_wall: "你撞到牆壁了！",
    }
    const label = reasonLabels[state.reason] ?? "這一局結束了！"
    overlay.innerHTML = `<div><div style="font-size:30px;margin-bottom:8px;">Game Over</div><div>${label}</div></div>`
    overlay.classList.remove("hidden")
  } else if (state.paused) {
    overlay.innerHTML = `<div><div style="font-size:24px;margin-bottom:8px;">遊戲已暫停</div><div>按「繼續遊戲」或空白鍵回到這一局。</div></div>`
    overlay.classList.remove("hidden")
  } else if (countdownRemainingMs(state) > 0) {
    const seconds = countdownRemainingSeconds(state)
    overlay.innerHTML = `<div><div style="font-size:26px;margin-bottom:8px;">準備開始</div><div style="font-size:56px;line-height:1;margin-bottom:10px;">${seconds}</div><div>準備好方向鍵 / 滑鼠或手指操作</div></div>`
    overlay.classList.remove("hidden")
  } else if (state.waitingForTouch) {
    overlay.innerHTML = `<div><div style="font-size:24px;margin-bottom:8px;">點一下畫面開始</div><div>用手指拖曳方向，蛇會朝手指移動。</div></div>`
    overlay.classList.remove("hidden")
  } else {
    overlay.classList.add("hidden")
  }
}

function maybeAwardToken(state, setTriggerValue) {
  const threshold = Math.floor(state.score / 100) * 100
  if (threshold <= 0 || threshold > 500 || state.sentThresholds.has(threshold)) return
  state.sentThresholds.add(threshold)
  state.localTokens += 1
  setTriggerValue("token_award", {
    game_id: state.gameId,
    game_type: "snake",
    threshold,
    score: state.score,
  })
}

function addScore(state, basePoints) {
  return Math.max(1, Math.round(Number(basePoints) * state.scoreMultiplier))
}

function finish(state, reason, setTriggerValue) {
  state.gameOver = true
  state.reason = reason
  const strengthSummary = state.fruits
    .filter((fruit) => fruit.is_strength_fruit)
    .map((fruit) => `${fruit.fruit_name} +${fruit.points}`)
    .join("、")
  setTriggerValue("game_over", {
    game_id: state.gameId,
    game_type: "snake",
    score: state.score,
    length: Math.max(3, Math.round(state.maxPoints / 18)),
    game_over_reason: reason,
    fruits_eaten: state.fruits,
    strength_summary: strengthSummary,
    ability_events: state.abilityEvents,
  })
}

function spawnFood(state) {
  const palette = ["#64d2ff", "#4ecdc4", "#fff07a", "#a5ffd6"]
  const point = findSafePoint(state, 8)
  state.foods.push({
    x: point.x,
    y: point.y,
    radius: 5,
    type: "normal",
    color: palette[Math.floor(Math.random() * palette.length)],
  })
}

function spawnStrengthFruit(state) {
  const strengths = ["仁慈", "勤奮", "好奇心", "勇敢", "感激", "團體合作", "自我規範"]
  const palette = ["#ffcf4a", "#ff7ab8", "#a98bff", "#7ef0a1"]
  const angle = Math.random() * Math.PI * 2
  const point = findSafePoint(state, 22)
  return {
    x: point.x,
    y: point.y,
    vx: Math.cos(angle) * 1.35,
    vy: Math.sin(angle) * 1.35,
    radius: 16,
    strength: strengths[Math.floor(Math.random() * strengths.length)],
    points: 40 + Math.max(0, Number(state.strengthFruitBonus ?? 0)),
    color: palette[Math.floor(Math.random() * palette.length)],
    pulse: Math.random() * Math.PI * 2,
  }
}

function useShield(state, reason) {
  if (state.shieldCharges <= 0) return false
  state.shieldCharges -= 1
  state.abilityEvents.push({
    reason,
    label: "角色守護",
    message: reason === "hit_self" ? "角色守護了你一次，幫你避開撞到自己。" : "角色守護了你一次，幫你回到安全的位置。",
  })
  state.head = { x: state.width / 2, y: state.height / 2 }
  state.angle = 0
  state.targetAngle = 0
  state.points = []
  for (let index = 0; index < 46; index += 1) {
    state.points.push({ x: state.head.x - index * 4, y: state.head.y })
  }
  return true
}

function snakeLength(state) {
  return Math.max(3, Math.round(state.maxPoints / 18))
}

function getSnakeDifficulty(length) {
  const level = Math.max(0, Math.min(5, Math.floor((Number(length) - 5) / 4)))
  return {
    level,
    obstacleCount: Math.max(0, Math.min(5, level)),
    obstacleRadius: 13 + Math.min(4, level),
  }
}

function updateObstaclesByLength(state) {
  const difficulty = getSnakeDifficulty(snakeLength(state))
  state.difficultyLevel = difficulty.level
  if (!Array.isArray(state.obstacles)) state.obstacles = []
  while (state.obstacles.length < difficulty.obstacleCount) {
    const point = findSafePoint(state, difficulty.obstacleRadius + 4)
    state.obstacles.push({
      x: point.x,
      y: point.y,
      radius: difficulty.obstacleRadius,
      pulse: Math.random() * Math.PI * 2,
    })
  }
  if (state.obstacles.length > difficulty.obstacleCount) {
    state.obstacles = state.obstacles.slice(0, difficulty.obstacleCount)
  }
}

function drawObstacles(ctx, state) {
  for (const obstacle of state.obstacles ?? []) {
    obstacle.pulse = (obstacle.pulse ?? 0) + 0.025
    const glowRadius = obstacle.radius * (2.4 + Math.sin(obstacle.pulse) * 0.18)
    const glow = ctx.createRadialGradient(obstacle.x, obstacle.y, 1, obstacle.x, obstacle.y, glowRadius)
    glow.addColorStop(0, "rgba(255, 95, 109, 0.56)")
    glow.addColorStop(1, "rgba(255, 95, 109, 0)")
    ctx.fillStyle = glow
    ctx.beginPath()
    ctx.arc(obstacle.x, obstacle.y, glowRadius, 0, Math.PI * 2)
    ctx.fill()
    ctx.fillStyle = "#ff5f6d"
    ctx.strokeStyle = "rgba(255, 255, 255, 0.55)"
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.arc(obstacle.x, obstacle.y, obstacle.radius, 0, Math.PI * 2)
    ctx.fill()
    ctx.stroke()
  }
}

function findSafePoint(state, radius) {
  const margin = Math.max(28, radius + state.radius + 8)
  for (let attempt = 0; attempt < 80; attempt += 1) {
    const point = {
      x: margin + Math.random() * Math.max(1, state.width - margin * 2),
      y: margin + Math.random() * Math.max(1, state.height - margin * 2),
    }
    if (isPointSafe(state, point, radius)) return point
  }
  return {
    x: Math.max(margin, Math.min(state.width - margin, state.width * 0.72)),
    y: Math.max(margin, Math.min(state.height - margin, state.height * 0.32)),
  }
}

function isPointSafe(state, point, radius) {
  if (distance(point, state.head) < radius + state.radius + 80) return false
  for (const bodyPoint of state.points ?? []) {
    if (distance(point, bodyPoint) < radius + state.radius + 16) return false
  }
  for (const obstacle of state.obstacles ?? []) {
    if (distance(point, obstacle) < radius + obstacle.radius + 24) return false
  }
  for (const food of state.foods ?? []) {
    if (distance(point, food) < radius + food.radius + 18) return false
  }
  if (state.strengthFruit && distance(point, state.strengthFruit) < radius + state.strengthFruit.radius + 24) {
    return false
  }
  return true
}

function countdownRemainingMs(state) {
  const elapsed = Date.now() - Number(state.countdownStartedAtMs ?? Date.now())
  return Math.max(0, Number(state.countdownMs ?? 0) - elapsed)
}

function countdownRemainingSeconds(state) {
  return Math.max(1, Math.ceil(countdownRemainingMs(state) / 1000))
}

function moveStrengthFruit(state) {
  const fruit = state.strengthFruit
  if (!fruit) return
  fruit.x += fruit.vx
  fruit.y += fruit.vy
  fruit.pulse += 0.04
  const margin = fruit.radius + 12
  if (fruit.x < margin || fruit.x > state.width - margin) fruit.vx *= -1
  if (fruit.y < margin || fruit.y > state.height - margin) fruit.vy *= -1
  fruit.x = Math.max(margin, Math.min(state.width - margin, fruit.x))
  fruit.y = Math.max(margin, Math.min(state.height - margin, fruit.y))
}

function drawStrengthFruit(ctx, fruit, state) {
  const pulseRadius = fruit.radius + Math.sin(fruit.pulse) * 2
  const glow = ctx.createRadialGradient(fruit.x, fruit.y, 2, fruit.x, fruit.y, pulseRadius * 4.2)
  glow.addColorStop(0, fruit.color)
  glow.addColorStop(0.42, "rgba(255, 236, 122, 0.42)")
  glow.addColorStop(1, "rgba(255,255,255,0)")
  ctx.fillStyle = glow
  ctx.beginPath()
  ctx.arc(fruit.x, fruit.y, pulseRadius * 4.2, 0, Math.PI * 2)
  ctx.fill()

  ctx.save()
  ctx.translate(fruit.x, fruit.y)
  ctx.rotate(Math.sin(fruit.pulse) * 0.08)
  ctx.fillStyle = fruit.color
  ctx.shadowColor = fruit.color
  ctx.shadowBlur = 22
  ctx.beginPath()
  ctx.arc(0, 2, pulseRadius, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = "#fff7a8"
  ctx.beginPath()
  ctx.arc(-5, -4, 4, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = "#5df2c2"
  ctx.beginPath()
  ctx.ellipse(8, -15, 8, 4, -0.7, 0, Math.PI * 2)
  ctx.fill()
  ctx.shadowBlur = 0
  ctx.fillStyle = "#21052c"
  ctx.font = "900 10px sans-serif"
  ctx.textAlign = "center"
  ctx.fillText(`+${addScore(state, fruit.points)}`, 0, 6)
  ctx.restore()
}

function turnToward(current, target, amount) {
  let difference = ((target - current + Math.PI) % (Math.PI * 2)) - Math.PI
  if (difference < -Math.PI) difference += Math.PI * 2
  return current + Math.max(-amount, Math.min(amount, difference))
}

function distance(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y)
}

function clamp(value, min, max) {
  if (!Number.isFinite(value)) return min
  return Math.max(min, Math.min(max, value))
}

function isTouchPlayfield(width) {
  return width <= 560 || window.matchMedia?.("(pointer: coarse)")?.matches === true
}
"""


_SLITHER_COMPONENT = st.components.v2.component(
    "slither_snake_game",
    html=HTML,
    css=CSS,
    js=JS,
)


def slither_snake_game(
    state: dict[str, Any],
    *,
    key: str,
    on_game_over_change: Callable[[], None] | None = None,
    on_token_award_change: Callable[[], None] | None = None,
    on_pause_toggle_change: Callable[[], None] | None = None,
):
    if on_game_over_change is None:
        on_game_over_change = lambda: None
    if on_token_award_change is None:
        on_token_award_change = lambda: None
    if on_pause_toggle_change is None:
        on_pause_toggle_change = lambda: None
    modifiers = state.get("active_modifiers") or state.get("active_buff") or {}

    return _SLITHER_COMPONENT(
        key=key,
        data={
            "game_id": state["game_id"],
            "tokens_earned": int(state.get("tokens_earned", 0)),
            "awarded_thresholds": state.get("awarded_thresholds", []),
            "score_multiplier": float(modifiers.get("score_multiplier") or 1.0),
            "speed_multiplier": float(modifiers.get("speed_multiplier") or 1.0),
            "bonus_start_score": int(modifiers.get("bonus_start_score") or 0),
            "shield_charges": int(modifiers.get("shield_charges") or 0),
            "turn_rate": float(modifiers.get("turn_rate") or 0.09),
            "strength_fruit_bonus": int(modifiers.get("strength_fruit_bonus") or 0),
            "modifier_label": modifiers.get("summary_label") if modifiers.get("applies") else "",
            "buff_label": modifiers.get("buff_label") if modifiers.get("applies") else "",
            "paused": bool(state.get("paused")),
            "countdown_started_at_ms": int(state.get("countdown_started_at_ms") or 0),
        },
        on_game_over_change=on_game_over_change,
        on_token_award_change=on_token_award_change,
        on_pause_toggle_change=on_pause_toggle_change,
    )
