# Database Setup

本專案程式連到本機 MySQL，TablePlus 只是用來查看同一個 database 的 GUI。

## 1. 建立 MySQL database

先確認 MySQL 已啟動。初始化腳本會自動建立 `.env` 裡指定的 database：

```bash
python database/init_db.py
```

預設 database 名稱是 `ai_for_children`。

## 2. 設定 .env

複製 `.env.example` 成 `.env`，並依你的本機 MySQL 設定追加資料庫設定；若不設定，程式會使用本機預設值：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=ai_for_children
GEMINI_API_KEY=your_api_key_here
```

不要把真實 `.env` commit 到 GitHub。

## 3. 用 TablePlus 連線

在 TablePlus 建立 MySQL connection：

- Host: `localhost`
- Port: `3306`
- User: 你的 `DB_USER`
- Password: 你的 `DB_PASSWORD`
- Database: `ai_for_children`

程式和 TablePlus 都連到同一個 MySQL database。

## 4. 初始化資料表與 seed data

```bash
python database/init_db.py
```

這會執行：

1. `schema.sql`
2. `seed_data.sql`

## 5. 確認資料表

初始化後，可以在 TablePlus 看到：

- `children`
- `strengths`
- `child_strengths`
- `chat_logs`
- `chat_ai_usage_limits`
- `token_transactions`
- `game_sessions`
- `game_reflections`
- `outfits`
- `child_outfits`
- `todo_items`
- `diary_entries`
- `diary_analysis_cache`
