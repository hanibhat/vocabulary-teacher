# Vocabulary Teacher

Vocabulary Teacher is a vocabulary practice app with a FastAPI backend, a static Alpine.js frontend, and a Telegram bot for adding words to a Google Spreadsheet.

> **For AI agents:** See [`AGENTS.md`](AGENTS.md) for architecture, conventions, and development workflows.

## Features

- **Web frontend** — Organizes words by category, random practice sets, filter by source phrase, choose translation language (Arabic/English).
- **Telegram bot** — Send a German word to the bot and it translates it to English and Arabic, generates example sentences, and lets you confirm to add it to your Google Sheet.
- **Dynamic columns** — The spreadsheet can use any naming convention for columns.
- **Cache** — Vocabulary is cached in-memory on the server (refreshed via cron) and in `localStorage` on the frontend (until midnight).

## Project Shape

```text
server/
  main.py                 FastAPI app, CORS, route lockdown, scheduler
  config.py               Environment configuration
  requirements.txt        Backend dependencies
  .env.example            Environment variable template
  routes/
    vocabulary.py         GET /vocabulary
    telegram.py           POST /telegram/webhook
  services/
    vocabulary.py         Google Sheets read/write
    llm.py                OpenRouter LLM translation & example generation
    telegram_bot.py       Telegram bot logic & state management
  tests/
    test_vocabulary.py    Parser tests
index.html                Static German frontend
index.js                  Frontend state, caching, filtering, shuffle
privacy.html              Privacy policy
```

## Prerequisites

- Python 3.13+
- A Google Spreadsheet with vocabulary data
- A Telegram bot (create one via [@BotFather](https://t.me/botfather))
- An [OpenRouter](https://openrouter.ai) API key

## Configuration

Copy `server/.env.example` to `server/.env` and fill in the values:

| Variable                      | Required | Description                                                       |
| ----------------------------- | -------- | ----------------------------------------------------------------- |
| `CORS_ALLOW_ORIGINS`          | No       | Comma-separated allowlist. Default includes `null` for local dev. |
| `CACHE_CRON_SCHEDULE`         | Yes      | Crontab for vocabulary refresh (e.g. `0 * * * *` = every hour).   |
| `TELEGRAM_BOT_TOKEN`          | Yes      | Token from BotFather.                                             |
| `TELEGRAM_WEBHOOK_URL`        | Yes      | Public HTTPS URL pointing to `/telegram/webhook`.                 |
| `GOOGLE_SPREADSHEET_ID`       | Yes      | The ID from the spreadsheet URL.                                  |
| `GOOGLE_SPREADSHEET_RANGE`    | Yes      | Column range (e.g. `A:F`).                                        |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Yes      | Full Google service account JSON key.                             |
| `GOOGLE_SHEET_VOCABULARY`     | Yes      | Sheet tab name where the bot adds words (e.g. `Wortschatz`).      |
| `OPENROUTER_API_KEY`          | Yes      | OpenRouter API key for LLM calls.                                 |
| `OPENROUTER_MODEL`            | No       | Model to use (default: `google/gemini-2.5-flash`).                |
| `GOOGLE_SHEET_NAMES`          | No       | Comma-separated sheet tabs to read. Empty = all tabs.             |

## Google Service Account Setup

1. Create or choose a Google Cloud project.
2. Enable the Google Sheets API.
3. Create a service account and a JSON key.
4. Share the spreadsheet with the service account email (edit access required for the bot to write).
5. Set `GOOGLE_SERVICE_ACCOUNT_JSON` in `.env` to the full JSON.

## Endpoints

| Method         | Path                | Description                                   |
| -------------- | ------------------- | --------------------------------------------- |
| `GET`          | `/vocabulary`       | Returns all vocabulary grouped by sheet name. |
| `GET` / `HEAD` | `/healthz`          | Health check, returns `{}`.                   |
| `POST`         | `/telegram/webhook` | Telegram bot updates (webhook).               |

## Running Locally

### One command (cross-platform)

```bash
python run.py
```

This will create the virtual environment, install dependencies, and start the server on `http://127.0.0.1:5000` with auto-reload.

Options:

```bash
python run.py --port 8080       # Change port
python run.py --no-reload        # Disable auto-reload
python run.py -- --root-path /api  # Pass extra uvicorn args after --
```

### Manual (any OS)

```bash
cd server
python -m venv venv
source venv/bin/activate      # Linux/macOS
# .\venv\Scripts\activate     # Windows
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 5000 --reload
```

### Telegram Bot (local testing)

Run [ngrok](https://ngrok.com) alongside the server:

```bash
ngrok http 5000
```

Then set `TELEGRAM_WEBHOOK_URL` to `https://your-ngrok-id.ngrok-free.app/telegram/webhook`.

Open `index.html` in a browser or send `/start` to your bot on Telegram.

## Tests

```bash
cd server
python -m pytest
```

Or from the project root (if the venv was created by `run.py`):

```bash
python -m pytest server/tests
```

## Security Notes

- The `.env` file and `server/service-account.json` contain live credentials and are gitignored — never commit them.
- The sheet tab specified in `GOOGLE_SHEET_VOCABULARY` must already exist in the spreadsheet. The bot will error out if it's missing.
