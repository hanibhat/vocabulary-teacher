# AGENTS.md — Vocabulary Teacher

This file is a guide for AI coding agents. It describes the project's architecture, conventions, and common workflows so agents can produce correct and idiomatic code with minimal context switching.

---

## 1. Project Overview

Vocabulary Teacher is a vocabulary practice app with a **FastAPI backend**, a **static Alpine.js frontend**, and a **Telegram bot** for adding words to a Google Spreadsheet.

### High-Level Flow

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Browser     │────▶│  FastAPI Server   │────▶│  Google Sheets  │
│  (Alpine.js) │     │  (uvicorn)        │     │  API            │
└─────────────┘     └──────────────────┘     └─────────────────┘
                           │
                           ▼
                    ┌──────────────────┐
                    │  OpenRouter LLM  │
                    │  (translations)  │
                    └──────────────────┘

┌─────────────┐     ┌──────────────────┐
│  Telegram    │────▶│  Bot Webhook     │
│  User        │     │  (POST /webhook) │
└─────────────┘     └──────────────────┘
```

---

## 2. Tech Stack

| Layer          | Technology                                                     |
| -------------- | -------------------------------------------------------------- |
| Runtime        | Python 3.13+                                                   |
| Web framework  | FastAPI                                                        |
| Server         | Uvicorn                                                        |
| Scheduler      | APScheduler (async)                                            |
| DB / Storage   | Google Sheets API (read/write)                                 |
| LLM            | OpenRouter API (translation & example generation)              |
| Bot            | python-telegram-bot                                            |
| Frontend       | Vanilla JS (Alpine.js), Tailwind CSS (CDN), static HTML        |
| Testing        | pytest                                                         |

---

## 3. Project Structure

```
vocabulary-teacher/
├── run.py                  <── Cross-platform runner (python run.py)
├── AGENTS.md               <── This file
├── README.md               <── User-facing documentation
├── .gitignore
├── .prettierrc.js
├── index.html              <── Frontend (Alpine.js)
├── index.js                <── Frontend logic
├── privacy.html            <── Privacy policy
├── assets/                 <── Static assets (icons, logo)
│
└── server/
    ├── .env.example
    ├── .env                <── LIVE CREDENTIALS — gitignored
    ├── config.py           <── Environment config reader
    ├── main.py             <── FastAPI app, CORS, lifespan, scheduler
    ├── requirements.txt
    ├── pytest.ini
    ├── __init__.py
    ├── routes/
    │   ├── vocabulary.py   <── GET /vocabulary
    │   └── telegram.py     <── POST /telegram/webhook
    ├── services/
    │   ├── vocabulary.py   <── Google Sheets read/write & caching
    │   ├── llm.py          <── OpenRouter LLM calls
    │   └── telegram_bot.py <── Bot message handling & state
    └── tests/
        └── test_vocabulary.py
```

---

## 4. Key Conventions & Patterns

### 4.1 Code Style

- **Python**: Follow PEP 8. Max line length is 100 characters.
- **JavaScript**: Uses `function` declarations (no arrow functions for top-level). Prefer `const`/`let` over `var`.
- **No TypeScript** — the frontend is plain JavaScript with Alpine.js.

### 4.2 Python Imports

Order:
1. Standard library
2. Third-party
3. Local application

Groups separated by blank lines.

### 4.3 Logging

Use `logging.getLogger(__name__)` at module level. Configure once in `main.py`:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
```

### 4.4 Configuration (config.py)

- All environment variables are read through `config.py`.
- The `Config` class uses `@property` descriptors for lazy evaluation.
- Sensitive defaults are stored as class-level constants (e.g., `default_cors_allow_origins`).
- The `.env` file is loaded from **both** the project root and `server/` (server overrides root).
- Required variables raise `RuntimeError` if unset; use `get_required_env()`.
- CSV-style variables use `get_csv_env()`.

### 4.5 Google Sheets Service

- The Sheets API service is **cached globally** (`_sheets_service`) to avoid rebuilding the HTTP transport.
- Vocabulary data is **cached in memory** (`_vocabulary: dict[str, list[dict]]`).
- `make_vocabulary()` refreshes the cache; called:
  - On server startup (in `lifespan`)
  - Periodically via APScheduler (cron schedule from `CACHE_CRON_SCHEDULE`)
  - On demand if `get_vocabulary()` finds the cache empty
- Column names from the sheet headers are lowercased and used as dictionary keys.
- Single quotes in sheet names are escaped by doubling (`'` → `''`).

### 4.6 Telegram Bot

- Bot instance is **globally cached** (`_bot`).
- User state is stored in a dict keyed by `(chat_id, message_id)`.
- The bot **inserts new rows at the top** of the sheet (not appended at the bottom).
- Callback flow: Confirm / Retry / Cancel.
- LLM calls are run in a thread via `asyncio.to_thread()` to avoid blocking the event loop.

### 4.7 LLM Service (llm.py)

- Retries up to **3 times** on 429 (rate limit) and 503 (service unavailable) with backoff (5s, 10s, 20s).
- Expects JSON responses from the LLM; parses with fallback to extracting from markdown code blocks.
- `response_format: {"type": "json_object"}` is sent to OpenRouter.

### 4.8 API Design

- The server has a **strict allowlist middleware** (`only_known_endpoints`) that returns 404 for unknown paths.
- Allowed paths:
  - `GET /vocabulary`
  - `GET /healthz`, `HEAD /healthz`
  - `POST /telegram/webhook`
- CORS is configured via `CORS_ALLOW_ORIGINS` (comma-separated).
- The `/vocabulary` endpoint returns a dict mapping sheet names → arrays of row dicts.

### 4.9 Frontend State Management

- Data is fetched from `/vocabulary` and cached in `localStorage` until midnight.
- The cache key is `vocabularyCache`; the language preference key is `targetLanguage`.
- On fetch failure, stale cache is preserved (not cleared) to keep the app usable.

---

## 5. How to Run the Server

### One command (cross-platform):

```bash
python run.py
```

This will:
1. Create a virtual environment (`server/venv/`) if missing
2. Install dependencies from `server/requirements.txt`
3. Start uvicorn on `http://127.0.0.1:5000` with auto-reload

### Options:

```bash
python run.py --port 8080            # Change port
python run.py --no-reload             # Disable auto-reload
python run.py -- --forwarded-allow-ips '*'   # Pass extra uvicorn args
```

### Manual (any OS):

```bash
cd server
python -m venv venv
source venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 5000 --reload
```

---

## 6. Environment Variables

See `server/.env.example` for a full template.

| Variable                      | Required | Notes                                                                 |
| ----------------------------- | -------- | --------------------------------------------------------------------- |
| `CORS_ALLOW_ORIGINS`          | No       | Comma-separated; defaults to `localhost:8000`, `null`                 |
| `CACHE_CRON_SCHEDULE`         | Yes      | Crontab (e.g., `0 * * * *` = every hour). Used by APScheduler.        |
| `TELEGRAM_BOT_TOKEN`          | Yes      | From BotFather.                                                        |
| `TELEGRAM_WEBHOOK_URL`        | Yes      | Public HTTPS URL for Telegram to POST to.                              |
| `TELEGRAM_WEBHOOK_SECRET_TOKEN` | Yes    | Secret token for webhook verification.                                 |
| `TELEGRAM_ADMIN_CHAT_ID`      | No       | If set, bot sends a startup confirmation message.                      |
| `GOOGLE_SPREADSHEET_ID`       | Yes      | From the spreadsheet URL.                                              |
| `GOOGLE_SPREADSHEET_RANGE`    | Yes      | Column range (e.g., `A:F`).                                            |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Yes      | Full JSON string of the service account key.                           |
| `GOOGLE_SHEET_VOCABULARY`     | Yes      | Sheet tab name where the bot writes new words. Must exist already.     |
| `GOOGLE_SHEET_NAMES`          | No       | Comma-separated sheet tabs to read. Empty = read all tabs.             |
| `OPENROUTER_API_KEY`          | Yes      | OpenRouter API key.                                                    |
| `OPENROUTER_MODEL`            | No       | Model name (default: `google/gemini-2.5-flash`).                      |
---

## 7. Testing

```bash
# From project root (uses server/venv if created by run.py):
python -m pytest server/tests

# Or activate venv first:
cd server && python -m pytest

# Or via the venv python directly:
./server/venv/bin/python -m pytest server/tests   # Linux/macOS
.\server\venv\Scripts\python -m pytest server\tests  # Windows
```

Test configuration is in `server/pytest.ini`:
- `-p no:cacheprovider` — disables caching for cleaner runs
- `pythonpath = .` — allows importing from `services/` directly

### Writing Tests

- Place test files in `server/tests/` with `test_` prefix.
- Use descriptive function names (snake_case).
- Pure unit tests only (no network calls) — mock external APIs via `unittest.mock` or `pytest-monkeypatch`.

---

## 8. Common Development Workflows

### Adding a New Environment Variable

1. Add the key to `server/.env.example` with a placeholder.
2. Add a `@property` to the `Config` class in `server/config.py`.
3. If required, use `get_required_env()`; if optional with a default, use `os.getenv()`.
4. Reference `config.your_property` wherever needed.

### Adding a New Route

1. Create a new file in `server/routes/` (or add to an existing one).
2. Define an `APIRouter` and register endpoints.
3. Add the endpoint to the allowlist in `main.py` (`only_known_endpoints` middleware).
4. Include the router in `main.py` via `app.include_router()`.

### Adding a New Service

1. Create a new file in `server/services/`.
2. Use module-level logging: `logger = logging.getLogger(__name__)`.
3. Cache expensive resources globally (singleton pattern).

### Modifying the LLM Prompt

Edit `_build_prompt()` in `server/services/llm.py`. Ensure the output format stays JSON-compatible with the parsing logic.

### Setting Up the Frontend for Development

Just open `index.html` in a browser. The frontend fetches from `http://localhost:5000/vocabulary` (hardcoded in `index.js`). No build step, no bundler.

### Telegram Bot Testing Locally

1. Start the server + ngrok:
   ```bash
   python run.py
   ngrok http 5000
   ```
2. Set `TELEGRAM_WEBHOOK_URL` to `https://your-ngrok-id.ngrok-free.app/telegram/webhook`.
3. Send `/start` to your bot on Telegram.

---

## 9. Security Notes

- `.env` and any `service-account*.json` / `google-credentials*.json` files are in `.gitignore` — never commit them.
- The webhook endpoint validates `X-Telegram-Bot-Api-Secret-Token` header before processing.
- Only known endpoint paths are allowed through middleware (all others return 404).
- The frontend runs entirely client-side with no authentication. The `/vocabulary` endpoint is intentionally public (read-only, cached vocabulary).

