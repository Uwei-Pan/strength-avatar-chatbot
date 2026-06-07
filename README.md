# Strength Avatar Chatbot

Strength Avatar Chatbot is a Streamlit + MySQL MVP for child-centered strengths discovery. It combines AI chat, reflective journaling, task completion, games, token rewards, avatar outfits, and a growth dashboard to help children notice and record their character strengths over time.

The project is designed as a portfolio-friendly prototype: it demonstrates a full data-backed Streamlit application, AI-service fallback handling, gamified UX, and domain modeling around VIA-style character strengths.

## Tech Stack / 技術棧

| 層級 | 技術 | 用途 |
| --- | --- | --- |
| 前端 / UI | Streamlit | 建立多頁式 Web 介面，處理使用者互動 |
| 主要語言 | Python 3.11 | 專案主要開發語言 |
| 服務層 | `services/` Python modules | 將 AI、代幣、日記、遊戲、商店、儀表板邏輯和頁面 UI 分離 |
| 資料庫 | MySQL | 儲存使用者、聊天、日記、優勢、代幣、遊戲、服裝與任務資料 |
| 資料庫連線 | PyMySQL | 讓 Python service 連接 MySQL |
| AI 服務 | Google Gemini API | 產生兒少友善回覆、日記回饋、優勢判斷與遊戲反思驗證 |
| 預設 AI 模型 | `gemini-2.5-flash-lite` | 專案預設使用的 Gemini Flash 模型 |
| AI fallback | Rule-based / mock mode | 沒有有效 Gemini API key 時，仍能用本機規則維持 demo 流程 |
| 資料視覺化 | Pandas, Altair | 建立成長儀表板中的圖表與統計摘要 |
| 環境設定 | python-dotenv, Streamlit secrets | 讀取本機 `.env` 與部署平台 secrets |
| 臨時展示 | Cloudflare Quick Tunnel | 將本機 Streamlit app 暫時公開成 demo 網址 |

## 系統功能

| 功能模組 | 說明 |
| --- | --- |
| 登入系統 | 提供 seed data 中的 demo 學生帳號，並用 Streamlit session state 保存登入狀態 |
| 首頁儀表板 | 顯示孩子目前的角色、代幣與主要功能入口 |
| AI 聊天 | 孩子可以和 AI 小幫手對話；系統會判斷情緒、可能展現的優勢與代幣獎勵 |
| 心情日記 | 儲存日記內容，透過 Gemini 或 fallback 規則產生回饋，並記錄偵測到的品格優勢 |
| 任務小清單 | 孩子可以建立與完成任務；任務確認流程可透過環境變數設定輔導員密碼 |
| 成長儀表板 | 統整聊天、日記、遊戲與輔導紀錄，呈現優勢小卡、分布圖、趨勢與資料來源 |
| 遊戲樂園 | 包含貪食蛇與方塊消除，遊戲可獲得代幣，結束後也有反思問題 |
| 角色與服裝 | 孩子可以選擇角色和已解鎖服裝，部分服裝與優勢或遊戲效果連動 |
| 服裝商店 | 孩子可以使用代幣購買服裝 |
| 代幣系統 | 記錄聊天、日記、任務、遊戲、商店等行為造成的代幣增加與消耗 |
| MySQL 持久化 | 將資料存入 `children`、`chat_sessions`、`diary_entries`、`child_strengths`、`token_transactions`、`game_reflections` 等資料表 |

## Project Structure

```text
.
├── app.py                    # Streamlit entry point and page navigation
├── pages/                    # App pages: login, dashboard, chat, diary, tasks, games, avatar, shop
├── services/                 # Business logic, database-backed services, AI helpers
├── games/                    # Snake and block puzzle game logic/components
├── database/
│   ├── schema.sql            # MySQL schema
│   ├── seed_data.sql         # Demo users, strengths, outfits, sample evidence
│   └── init_db.py            # Database initialization script
├── data/                     # Static strengths/profile reference data
├── scripts/                  # Local setup, run, and temporary sharing scripts
├── requirements.txt
└── runtime.txt
```

## Backend Logic / 後端邏輯位置

本專案目前是 Streamlit MVP，還沒有拆成獨立的 FastAPI / REST API 後端。現階段的「後端邏輯」主要寫在 `services/`，而 `pages/` 負責從 Streamlit 畫面呼叫這些 service。整體資料流可以理解成：

```text
Streamlit pages -> Python services -> MySQL / Gemini API
```

快速註解：`pages/` 負責使用者看到和點擊的畫面；`services/` 負責商業邏輯、AI 呼叫、代幣變動和資料庫操作。

### 1. Database Connection and Schema / 資料庫連線與資料表

資料庫連線邏輯從 `database/db_connection.py` 開始。這個檔案會從環境變數讀取 MySQL 設定，建立資料庫連線，並提供 `fetch_one`、`fetch_all`、`execute` 這些共用 helper。大部分 service 都透過這些 helper 操作資料庫，而不是各自重複建立連線。

`database/schema.sql` 定義所有資料表，例如 children、strengths、chat logs、chat sessions、diary entries、token transactions、game sessions、game reflections、outfits、tasks 和 diary analysis cache。`database/init_db.py` 則負責初始化資料庫：建立 database、套用 schema，並匯入 `database/seed_data.sql` 的 demo 資料。

快速註解：資料庫連線、資料表設計和初始資料都在 `database/`。如果想知道系統存了哪些資料，先看 `database/schema.sql`。

### 2. AI and Gemini Logic / AI 與 Gemini 邏輯

Gemini 相關邏輯寫在 `services/ai_service.py`。這個檔案會讀取 `GEMINI_API_KEY`、選擇 Gemini model、建立 prompt、呼叫 Gemini、解析 JSON 回傳，並把 AI 結果整理成前端可以使用的固定格式。

它主要處理三種 AI 場景：聊天訊息分析、日記回饋分析、遊戲反思驗證。如果沒有設定有效的 Gemini API key，這個 service 會自動改用 rule-based / mock fallback，讓本機 demo 不會因為 AI key 缺失而壞掉。

快速註解：Gemini API key、prompt、AI JSON 解析和 fallback 都集中在 `services/ai_service.py`。

### 3. Chat Backend Logic / 聊天後端邏輯

聊天畫面由 `pages/chat.py` 呈現，但後端邏輯分散在多個 service。`services/ai_service.py` 負責分析孩子的訊息，`services/chat_reward_service.py` 判斷這次對話是否能獲得代幣，`services/token_service.py` 更新代幣，`services/chat_session_service.py` 儲存完整聊天 session，`services/strength_service.py` 儲存聊天紀錄和偵測到的優勢。

聊天流程是：使用者送出訊息後，`pages/chat.py` 呼叫 AI 分析；接著 reward logic 計算代幣事件；代幣變動寫入 MySQL；最後完整聊天紀錄會存到 `chat_sessions` 和 `chat_logs`。

快速註解：聊天不是單純顯示訊息，它同時串起 AI 分析、獎勵計算、代幣更新、聊天儲存與優勢證據儲存。

### 4. Diary Backend Logic / 日記後端邏輯

日記後端邏輯主要在 `services/diary_service.py`。它會接收日記文字，先檢查是否已經有快取的 AI 分析結果；如果沒有，就呼叫 `services/ai_service.py` 分析日記，接著計算日記代幣、儲存日記內容，並保存偵測到的優勢。

最後的日記結果會存進 `diary_entries`，重複的 AI 分析則可以快取到 `diary_analysis_cache`。這樣同一篇日記不需要一直重複呼叫 Gemini。

快速註解：`services/diary_service.py` 控制完整日記流程：分析、快取、給代幣、存日記、存優勢。

### 5. Token, Task, Shop, and Outfit Logic / 代幣、任務、商店與服裝邏輯

代幣變動由 `services/token_service.py` 處理。它會更新孩子的 token balance，並把每一次增加或扣除寫進 `token_transactions`，讓獎勵和消費都有紀錄可查。

任務邏輯在 `services/todo_service.py`，輔導員審核流程則由 `pages/todo.py` 觸發。商店購買由 `services/shop_service.py` 處理，包含檢查是否已擁有服裝、確認代幣是否足夠、解鎖服裝、扣除代幣和記錄交易。角色與服裝資料則由 `services/avatar_assets.py` 和 `services/child_service.py` 支援。

快速註解：代幣變動應該透過 `services/token_service.py` 或會記錄交易的 service function，不應該在 UI 直接手動改 token 數字。

### 6. Game and Reflection Logic / 遊戲與反思邏輯

遊戲畫面主要由 `pages/snake_game.py` 和 `games/` 裡的元件控制，但遊戲紀錄與持久化邏輯在 `services/game_service.py`。這個 service 會建立遊戲 session、記錄遊戲結果、處理遊戲代幣獎勵、防止重複發獎，並儲存遊戲反思答案。

遊戲反思驗證會使用 `services/ai_service.validate_reflection_answer()`。如果 Gemini 可用，就用 Gemini 輔助判斷；如果 Gemini 沒有設定，仍然有本機規則可以做基本驗證。

快速註解：遊戲畫面在 `pages/` 和 `games/`；遊戲紀錄、代幣獎勵和反思儲存走 `services/game_service.py`。

### 7. Growth Dashboard Logic / 成長儀表板邏輯

成長儀表板的資料整理邏輯寫在 `services/growth_dashboard_service.py`。它會讀取日記、遊戲反思、聊天紀錄、已完成任務和已儲存的優勢證據，然後整理成摘要、圖表、趨勢和優勢證據卡。

`pages/growth_dashboard.py` 主要負責畫面呈現，比較重的資料整理和統計邏輯放在 service layer，讓頁面程式碼比較專注在 UI。

快速註解：如果想知道儀表板如何決定要顯示哪些優勢，主要看 `services/growth_dashboard_service.py`。

## Installation

### 1. Prerequisites

Make sure the following tools are available before running the project:

- Python 3.11+
- MySQL 8.0+ or a MySQL-compatible database
- Optional: Google Gemini API key for real AI responses
- Optional: `cloudflared` for temporary public demos

Gemini is optional for local exploration. Without a valid API key, the app still runs with rule-based / mock fallback responses. MySQL is required because user data and app state are persisted in the database.

### 2. Clone the Repository

```bash
git clone <your-repo-url>
cd strength-avatar-chatbot
```

### 3. Install Python Dependencies

The easiest setup path is the included script:

```bash
scripts/setup_local.sh
```

This script creates `.venv`, installs packages from `requirements.txt`, and copies `.env.example` to `.env` if `.env` does not exist.

You can also set up the environment manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Fill in `.env` according to your local MySQL settings. A typical local setup looks like this:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=ai_for_children
GEMINI_API_KEY=your_api_key_here
TASK_REVIEW_PASSWORD=change_me
```

Important notes:

- `GEMINI_API_KEY` is optional. If it is missing or still set to a placeholder value, the app uses fallback logic.
- `TASK_REVIEW_PASSWORD` is used by the counselor review flow.
- Do not commit real `.env`, `.env.local`, `.envc`, or `.streamlit/secrets.toml` files.

### 5. Initialize the MySQL Database

Start MySQL first, then run:

```bash
python database/init_db.py
```

This creates the configured database, applies `database/schema.sql`, and loads `database/seed_data.sql`.

### 6. Run the Streamlit App

```bash
scripts/run_local.sh
```

Open:

```text
http://127.0.0.1:8501
```

You can also run Streamlit directly:

```bash
streamlit run app.py
```

## Demo Accounts

The seed data includes demo children from `studentB` through `studentP`. A few easy starting accounts are:

| Username | Password |
| --- | --- |
| `studentB` | `1234` |
| `studentC` | `1234` |
| `studentD` | `1234` |

The current MVP stores simplified demo passwords in the `children.password_hash` column. For production use, replace this with a real password hashing and account-management flow.

## Environment Variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `DB_HOST` | No | `localhost` | MySQL host |
| `DB_PORT` | No | `3306` | MySQL port |
| `DB_USER` | No | `root` | MySQL user |
| `DB_PASSWORD` | No | empty | MySQL password |
| `DB_NAME` | No | `ai_for_children` | Database name created by `database/init_db.py` |
| `GEMINI_API_KEY` | No | empty | Enables Gemini-backed AI responses when valid |
| `GEMINI_MODEL` | No | `gemini-2.5-flash-lite` | Gemini Flash model override |
| `TASK_REVIEW_PASSWORD` | Recommended | empty | Password for counselor task review |
| `COUNSELOR_TASK_REVIEW_PASSWORD` | No | empty | Alternative key for task review password |
| `CHAT_AI_DAILY_TOKEN_LIMIT` | No | app default | Optional daily AI chat token limit |

Do not commit real `.env`, `.env.local`, `.envc`, or `.streamlit/secrets.toml` files.

## Database Notes

The schema persists the main product model:

- `children`
- `strengths`
- `child_strengths`
- `chat_logs`
- `chat_sessions`
- `chat_ai_usage_limits`
- `token_transactions`
- `game_sessions`
- `game_reflections`
- `outfits`
- `child_outfits`
- `todo_items`
- `diary_entries`
- `diary_analysis_cache`

For more database-specific setup notes, see `database/README.md`.

## Local Public Sharing

For a temporary public demo from your local machine, install `cloudflared` and run:

```bash
scripts/start_public.sh
```

If Streamlit is already running in another terminal:

```bash
scripts/share_tunnel.sh
```

The generated `trycloudflare.com` URL is temporary. It stops working when the tunnel process, terminal, computer, or network connection stops.

## Deployment

This app needs a persistent MySQL-compatible database. Good deployment options include Render, Railway, or Streamlit Community Cloud paired with an external MySQL service.

### Render or Railway

Use the following commands:

```bash
pip install -r requirements.txt
```

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

Set environment variables for database credentials, Gemini, and task review password. Then initialize the database from an environment that can connect to the deployed MySQL instance:

```bash
python database/init_db.py
```

### Streamlit Community Cloud

Set `app.py` as the main file and configure secrets similar to:

```toml
DB_HOST = "your-cloud-mysql-host"
DB_PORT = "3306"
DB_USER = "your-user"
DB_PASSWORD = "your-password"
DB_NAME = "ai_for_children"
GEMINI_API_KEY = "your-key"
TASK_REVIEW_PASSWORD = "your-review-password"
```

Streamlit Community Cloud does not provide built-in MySQL, so use an external database provider and initialize the schema before running the demo.

## Testing Checklist

After running the app, manually verify:

- Login with `studentB` / `1234`
- Dashboard and growth dashboard load from seeded data
- Chat works with Gemini or mock fallback
- Diary entry saves and displays AI or fallback feedback
- Task creation and counselor review flow work
- Snake and block puzzle can start, award tokens, and save results
- Avatar, outfit, and shop pages reflect token and unlock state
- Layout remains usable at mobile, tablet, and desktop widths

Suggested viewport checks:

- Mobile: `390px`
- Tablet: `768px`
- Desktop: `1440px`

## Security and Production Considerations

This is an MVP prototype, not a production child-safety system. Before production use, prioritize:

- Real password hashing and account lifecycle management
- Role-based access for children, counselors, and administrators
- Privacy review for child-related records
- Database backups and migration strategy
- Stronger audit logs for counselor actions and AI-generated outputs
- Human-in-the-loop review for sensitive AI interactions
- Rate limiting and monitoring for Gemini usage

## What This Project Demonstrates

- Building a multi-page Streamlit application with a custom kid-friendly interface
- Designing a MySQL schema for persistent behavioral, reflective, and gamified records
- Integrating LLM features while keeping graceful fallback behavior
- Translating domain concepts like character strengths into product flows
- Connecting chat, diary, games, and rewards into one coherent growth-tracking experience
