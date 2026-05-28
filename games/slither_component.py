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
  <div class="slither-help">使用方向鍵或 WASD 轉向。小光點基礎 +10，會移動的大顆優勢果實基礎 +40。</div>
</div>
"""

CSS = """
.slither-shell {
  position: relative;
  width: min(100%, 840px);
  margin: 0 auto;
  padding: 14px;
  border-radius: 24px;
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
  gap: 10px;
  margin-top: 12px;
}

.slither-topbar > div {
  min-width: 0;
  padding: 10px 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(8px);
}

.slither-label {
  display: block;
  margin-bottom: 2px;
  color: rgba(247, 251, 255, 0.72);
  font-size: 12px;
  font-weight: 800;
}

.slither-topbar strong {
  font-size: 24px;
  line-height: 1.1;
}

#slither-canvas {
  display: block;
  width: 100%;
  aspect-ratio: 19 / 12;
  border-radius: 20px;
  background: #090e27;
  outline: 4px solid rgba(255, 255, 255, 0.16);
}

.slither-canvas-wrap {
  position: relative;
}

.slither-help {
  margin-top: 10px;
  color: rgba(247, 251, 255, 0.78);
  font-size: 13px;
  font-weight: 700;
  text-align: center;
}

.slither-buff {
  margin-top: 10px;
  min-height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px 10px;
  border-radius: 999px;
  color: #fff7a8;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.14);
  font-size: 13px;
  font-weight: 900;
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
  .slither-shell { padding: 10px; border-radius: 18px; }
  .slither-topbar { gap: 6px; }
  .slither-topbar > div { padding: 8px; border-radius: 12px; }
  .slither-topbar strong { font-size: 18px; }
  .slither-overlay { inset: 0; }
}
"""

JS = """
const instances = new WeakMap()

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

  const resizeCanvas = () => {
    const rect = canvas.getBoundingClientRect()
    const ratio = window.devicePixelRatio || 1
    canvas.width = Math.floor(rect.width * ratio)
    canvas.height = Math.floor(rect.width * 12 / 19 * ratio)
    instance.scale = ratio
    instance.width = canvas.width / ratio
    instance.height = canvas.height / ratio
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
  }
  resizeCanvas()

  const keyHandler = (event) => {
    const key = event.key.toLowerCase()
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
      instance.targetAngle = map[key]
    }
  }

  const pointerHandler = (event) => {
    const rect = canvas.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top
    instance.targetAngle = Math.atan2(y - instance.head.y, x - instance.head.x)
  }

  window.addEventListener("keydown", keyHandler)
  window.addEventListener("resize", resizeCanvas)
  canvas.addEventListener("pointermove", pointerHandler)

  const tick = () => {
    if (!instances.has(parentElement)) return
    if (!instance.gameOver) {
      update(instance, setTriggerValue)
    }
    draw(ctx, instance, scoreNode, lengthNode, tokenNode, buffNode, overlay)
    instance.frame = window.requestAnimationFrame(tick)
  }
  if (!instance.frame) {
    instance.frame = window.requestAnimationFrame(tick)
  }

  return () => {
    window.removeEventListener("keydown", keyHandler)
    window.removeEventListener("resize", resizeCanvas)
    canvas.removeEventListener("pointermove", pointerHandler)
    if (instance.frame) window.cancelAnimationFrame(instance.frame)
    instance.frame = null
  }
}

function createGame(gameId, data) {
  const width = 760
  const height = 480
  const head = { x: 180, y: 240 }
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
    speed: 2.25 * speedMultiplier,
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
    score: Math.max(0, Math.round(Number(data?.bonus_start_score ?? 0))),
    serverTokens: Number(data?.tokens_earned ?? 0),
    localTokens: 0,
    sentThresholds: new Set((data?.awarded_thresholds ?? []).map(Number)),
    fruits: [],
    strengthFruit: null,
    frame: null,
    gameOver: false,
    reason: "",
  }
  for (let index = 0; index < 46; index += 1) {
    state.points.push({ x: head.x - index * 4, y: head.y })
  }
  for (let index = 0; index < 28; index += 1) spawnFood(state)
  state.strengthFruit = spawnStrengthFruit(state)
  return state
}

function update(state, setTriggerValue) {
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
    const label = state.reason === "hit_self" ? "你撞到自己了！" : "你撞到牆壁了！"
    overlay.innerHTML = `<div><div style="font-size:30px;margin-bottom:8px;">Game Over</div><div>${label}</div></div>`
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
  state.foods.push({
    x: 30 + Math.random() * Math.max(1, state.width - 60),
    y: 30 + Math.random() * Math.max(1, state.height - 60),
    radius: 5,
    type: "normal",
    color: palette[Math.floor(Math.random() * palette.length)],
  })
}

function spawnStrengthFruit(state) {
  const strengths = ["仁慈", "勤奮", "好奇心", "勇敢", "感激", "團體合作", "自我規範"]
  const palette = ["#ffcf4a", "#ff7ab8", "#a98bff", "#7ef0a1"]
  const angle = Math.random() * Math.PI * 2
  return {
    x: 80 + Math.random() * Math.max(1, state.width - 160),
    y: 80 + Math.random() * Math.max(1, state.height - 160),
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
):
    if on_game_over_change is None:
        on_game_over_change = lambda: None
    if on_token_award_change is None:
        on_token_award_change = lambda: None
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
        },
        on_game_over_change=on_game_over_change,
        on_token_award_change=on_token_award_change,
    )
