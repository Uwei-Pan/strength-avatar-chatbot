# 兒少優勢探索 AI MVP

這是一個 Streamlit MVP。孩子登入後可以和智慧小幫手分享日常、獲得 tokens、留下成長亮點紀錄，並用 tokens 玩簡化版貪吃蛇優勢果實遊戲。

## 1. 安裝套件

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. 建立 .env

```bash
cp .env.example .env
```

依本機 MySQL 修改：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=strength_avatar
GEMINI_API_KEY=your_gemini_api_key_here
```

不要把真實 `.env` commit 到 GitHub。

## 3. Gemini API key

把 Google AI Studio / Gemini API key 放在 `.env`：

```env
GEMINI_API_KEY=你的_api_key
```

如果沒有設定 `GEMINI_API_KEY`，聊天會自動進入 mock mode，用 rule-based fallback 回覆與整理亮點，app 不會 crash。

可選擇指定模型：

```env
GEMINI_MODEL=gemini-2.0-flash
```

## 4. MySQL 與 TablePlus

程式連線對象是 MySQL。TablePlus 只是查看同一個 MySQL database 的 GUI。

TablePlus 連線設定：

- Host: `localhost`
- Port: `3306`
- User: `.env` 的 `DB_USER`
- Password: `.env` 的 `DB_PASSWORD`
- Database: `.env` 的 `DB_NAME`，預設 `strength_avatar`

## 5. 初始化資料庫

確認 MySQL 已啟動後：

```bash
python database/init_db.py
```

這會建立 database、執行 `database/schema.sql`，並匯入 `database/seed_data.sql`。

## 6. 啟動專案

```bash
streamlit run app.py
```

## 7. Demo 帳號

| 帳號 | 密碼 |
| --- | --- |
| `studentB` | `1234` |
| `studentC` | `1234` |
| `studentD` | `1234` |

MVP 階段 `children.password_hash` 欄位暫存簡化密碼，欄位名稱保留未來改成真正 password hash 的路徑。

## 8. 功能範圍

目前已建立：

- 登入
- Dashboard
- AI chat + token reward
- Gemini API service + mock mode
- Rule-based strength fallback
- 成長亮點紀錄儲存
- Token transaction
- 簡化版貪吃蛇遊戲
- 遊戲 token cost / score reward / game session
- Character / Outfit 基本頁
- Diary：可寫日記、接智慧小幫手回覆、儲存 diary entry、發 token、儲存成長亮點紀錄
- Todo：可新增任務、完成任務、發 token、記錄 token transaction
- Shop：可瀏覽服裝、用 token 購買並解鎖服裝

## 9. Mock mode 規則

沒有 `GEMINI_API_KEY` 或 Gemini 呼叫失敗時，`services/ai_service.py` 會使用 rule-based fallback：

- 包含「幫、照顧、分享、安慰」：仁慈
- 包含「完成、努力、練習、堅持」：勤奮
- 包含「嘗試、新、發現、為什麼」：好奇心
- 包含「害怕但、勇敢、挑戰」：勇敢
- 包含「謝謝、感謝」：感激
- 包含「一起、合作、隊友、幫忙完成」：團體合作

低訊息內容如「今天很累」「不知道」「還好」不會硬新增優勢標籤。
