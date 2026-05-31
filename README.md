# 兒少優勢探索 AI MVP

這是一個 Streamlit + MySQL 的兒少優勢探索 MVP。孩子登入後可以和AI小幫手聊天、寫心情日記、完成任務、玩遊戲、累積 tokens，並把成長亮點保存到資料庫。

## 技術與部署判斷

- 入口檔：`app.py`
- Web 框架：Streamlit
- 主要資料庫：MySQL
- AI 服務：Google Gemini API；沒有 API key 時會自動使用 rule-based mock mode，不會讓 app crash
- 本機檔案資料：`data/*.json` 目前只作為靜態優勢定義與範例資料；聊天歷史已改為 MySQL `chat_sessions` table

最適合的部署方式是 Render 或 Railway，原因是本專案需要 MySQL。Streamlit Community Cloud 可以部署介面，但沒有內建 MySQL，需要額外接 Aiven、PlanetScale、Railway MySQL 或其他雲端 MySQL。若你已經有可公開連線的 MySQL，Streamlit Community Cloud 也可行。

## 本機安裝

組員第一次拉下專案後，可以直接執行：

```bash
scripts/setup_local.sh
```

這會建立 `.venv`、安裝 `requirements.txt`，並在沒有 `.env` 時從 `.env.example` 複製一份。

若想手動安裝，也可以使用：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 環境變數

先複製範例：

```bash
cp .env.example .env
```

必要設定：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=strength_avatar
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODELS=
TASK_REVIEW_PASSWORD=your_password_here
```

不要把真實 `.env`、`.env.local`、`.envc` 或 `.streamlit/secrets.toml` commit 到 GitHub。

## 初始化資料庫

確認 MySQL 已啟動後執行：

```bash
python database/init_db.py
```

這會建立 database、執行 `database/schema.sql`，並匯入 `database/seed_data.sql`。

## 啟動專案

最簡單方式：

```bash
scripts/run_local.sh
```

預設會啟動在 `http://127.0.0.1:8501`。

如果要換 port：

```bash
PORT=8502 scripts/run_local.sh
```

手動啟動方式：

```bash
streamlit run app.py
```

預設網址通常是 `http://localhost:8501`。

## 臨時外網分享

如果組員只是要把目前本機網站臨時分享給別人看，可以使用 Cloudflare quick tunnel。

方式一：一個指令同時啟動 Streamlit 與外網 tunnel：

```bash
scripts/start_public.sh
```

看到類似下面這行時，把網址分享出去即可：

```text
https://xxxxx.trycloudflare.com
```

方式二：如果 Streamlit 已經在另一個 Terminal 跑著，可以只開 tunnel：

```bash
scripts/share_tunnel.sh
```

注意：

- 這是臨時網址，不保證永久有效。
- 電腦睡眠、關機、網路中斷、Terminal 關掉後，外網網址就會失效。
- `cloudflared` 需要先安裝；macOS 可用 `brew install cloudflared`。
- 預設使用 `8501`，如需改 port 可用 `PORT=8502 scripts/start_public.sh`。

## Demo 帳號

| 帳號 | 密碼 |
| --- | --- |
| `studentB` | `1234` |
| `studentC` | `1234` |
| `studentD` | `1234` |

MVP 階段 `children.password_hash` 欄位暫存簡化密碼，欄位名稱保留未來改成真正 password hash 的路徑。

## Render 部署

1. 將專案推到 GitHub。
2. 在 Render 建立 MySQL 相容資料庫，或使用外部 MySQL 服務。
3. 建立 Web Service，連接 GitHub repo。
4. Runtime 選 Python。
5. Build Command：

```bash
pip install -r requirements.txt
```

6. Start Command：

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

7. 在 Render Environment Variables 設定：
   - `DB_HOST`
   - `DB_PORT`
   - `DB_USER`
   - `DB_PASSWORD`
   - `DB_NAME`
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL`
   - `GEMINI_FALLBACK_MODELS`
   - `TASK_REVIEW_PASSWORD`
8. 部署前或首次部署後，在能連到同一個 MySQL 的環境執行：

```bash
python database/init_db.py
```

## Railway 部署

1. 在 Railway 新增 Project，連接 GitHub repo。
2. 加入 MySQL service。
3. 在 Web service 設定環境變數，使用 Railway MySQL 提供的 host、port、user、password、database。
4. Start Command：

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

5. 透過 Railway shell 或本機連線到 Railway MySQL 後執行 `python database/init_db.py` 初始化。

## Streamlit Community Cloud 部署

1. 專案推到 GitHub。
2. 到 Streamlit Community Cloud 新增 app，選擇 repo、branch 與 main file：`app.py`。
3. 在 Secrets 加入資料庫與 Gemini 設定，例如：

```toml
DB_HOST = "your-cloud-mysql-host"
DB_PORT = "3306"
DB_USER = "your-user"
DB_PASSWORD = "your-password"
DB_NAME = "strength_avatar"
GEMINI_API_KEY = "your-key"
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_FALLBACK_MODELS = ""
TASK_REVIEW_PASSWORD = "your-review-password"
```

4. Streamlit Cloud 不提供內建 MySQL，請使用外部 MySQL 並確認允許 Streamlit Cloud 連線。
5. 在本機或資料庫管理工具先完成 `python database/init_db.py`。

## 部署風險

- 免費平台可能會休眠，第一次開啟會比較慢。
- MySQL 需要外部可持久化服務；不要依賴部署容器內檔案儲存使用者資料。
- `data/*.json` 是靜態設定資料，可以部署；`data/chat_sessions/` 是舊本機聊天檔，已被 `.gitignore` 排除。
- Gemini API key 必須放平台環境變數或 Streamlit secrets，不要寫在程式碼裡。
- 手機版遊戲已支援縮放與觸控，但不同手機瀏覽器仍需實機測試。
- 使用者變多時，建議升級到正式 MySQL 方案、加上密碼雜湊、帳號管理與資料備份。

## 手機與桌機測試

1. 本機啟動 `streamlit run app.py`。
2. 用 Chrome 開 `http://localhost:8501`。
3. 開啟 DevTools，切換 Device Toolbar。
4. 至少測試寬度：`390px` 手機、`768px` 平板、`1440px` 桌機。
5. 逐頁檢查：登入、首頁、成長儀表板、聊天、遊戲樂園、角色與服裝、心情日記、任務、商店。
6. 注意是否有橫向捲動、按鈕太小、聊天泡泡超出、圖表文字擠壓、遊戲畫面超出版面。
