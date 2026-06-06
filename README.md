# Strength Avatar Chatbot

Strength Avatar Chatbot is a Streamlit + MySQL MVP for child-centered strengths discovery. It combines AI chat, reflective journaling, task completion, games, token rewards, avatar outfits, and a growth dashboard to help children notice and record their character strengths over time.

The project is designed as a portfolio-friendly prototype: it demonstrates a full data-backed Streamlit application, AI-service fallback handling, gamified UX, and domain modeling around VIA-style character strengths.

## Features

- Child login with seeded demo accounts
- AI companion chat for encouragement, emotion reflection, and strengths detection
- Mood diary with AI-assisted feedback and cached analysis results
- Task checklist with counselor review password support
- Growth dashboard showing strength evidence, distribution, trends, and source breakdowns
- Game zone with snake and block puzzle games
- Token economy for chat, diary, games, tasks, and shop purchases
- Avatar and outfit system connected to unlocked strengths and in-game effects
- MySQL persistence for users, chat sessions, diary entries, games, rewards, outfits, and strength evidence
- Gemini API integration with local rule-based fallback when no valid API key is configured

## Tech Stack

| Area | Technology |
| --- | --- |
| App framework | Streamlit |
| Language | Python 3.11 |
| Database | MySQL |
| AI service | Google Gemini API, default model `gemini-2.5-flash-lite` |
| Data access | PyMySQL |
| Charts | Pandas, Altair |
| Environment config | python-dotenv, Streamlit secrets |

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

## Prerequisites

- Python 3.11+
- MySQL 8.0+ or a MySQL-compatible database
- Optional: Google Gemini API key
- Optional for public local sharing: `cloudflared`

Gemini is optional for local exploration. Without a valid API key, the app still runs with rule-based mock responses. MySQL is required because user data and app state are persisted in the database.

## Quick Start

1. Clone the repository.

```bash
git clone <your-repo-url>
cd strength-avatar-chatbot
```

2. Install dependencies.

```bash
scripts/setup_local.sh
```

Manual setup also works:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Create local environment settings.

```bash
cp .env.example .env
```

You can start with the default local MySQL settings, then add or adjust values as needed:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=ai_for_children
GEMINI_API_KEY=your_api_key_here
TASK_REVIEW_PASSWORD=change_me
```

4. Start MySQL and initialize the database.

```bash
python database/init_db.py
```

This creates the configured database, applies `database/schema.sql`, and loads `database/seed_data.sql`.

5. Run the app.

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
