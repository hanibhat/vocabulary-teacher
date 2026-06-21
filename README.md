# Vocabulary Teacher

Vocabulary Teacher is a small vocabulary practice app with a FastAPI backend and a static Alpine.js frontend. The backend reads vocabulary from a Google Spreadsheet with a Google service account and exposes it through one endpoint. The frontend loads that endpoint, caches usable vocabulary in `localStorage` until midnight, and gives learners a simple German UI for category-based practice.

## Features

- Organizes words by category so users can study one topic at a time or review everything together.
- Lets users filter by source phrase.
- Creates random practice sets from all words or from a selected category.
- Lets users choose their translation language (Arabic, English) — persisted in `localStorage`.
- Uses dynamic column headers: the spreadsheet can use any language or naming convention for columns.
- Proactively refreshes vocabulary cache on a cron schedule via APScheduler.

## How It Works

- The backend reads one or more sheet tabs from a Google Spreadsheet.
- Each sheet tab becomes one vocabulary category.
- Vocabulary is served from a single `GET /vocabulary` endpoint.
- The backend caches vocabulary in memory and refreshes it on a cron schedule (`CACHE_CRON_SCHEDULE`) via APScheduler.
- On server startup, vocabulary is fetched immediately so the cache is warm.
- The frontend caches non-empty API responses in `localStorage` until the next midnight.
- Empty responses are not cached, so temporary source or parsing issues do not poison the browser cache.
- The frontend stores the user's chosen translation language in `localStorage` separately.

## Project Shape

```text
server/main.py                 FastAPI app, CORS, route lockdown, scheduler, /healthz
server/config.py               Environment configuration
server/routes/vocabulary.py    /vocabulary route and API error mapping
server/services/vocabulary.py  Google Sheets fetching, caching, vocabulary shaping
server/requirements.txt        Backend dependencies
server/tests/                  Backend parser tests
index.html                     Static German frontend
index.js                       Frontend state, caching, filtering, shuffle logic, language selection
privacy.html                   Privacy policy
```

## Expected Google Spreadsheet

Create one sheet tab per category. The column range is configurable via `GOOGLE_SPREADSHEET_RANGE`. The **first row** must be a header row. Column names are detected dynamically:

Share the spreadsheet with the service account email address, just like sharing it with a normal Google user. Read access is enough.

## Google Service Account Setup

1. Create or choose a Google Cloud project.
2. Enable the Google Sheets API for that project.
3. Create a service account.
4. Create a JSON key for the service account.
5. Share the spreadsheet with the service account email address.
6. Put the service account JSON in the backend environment as `GOOGLE_SERVICE_ACCOUNT_JSON`.

## Configuration

Create `server/.env` from `server/.env.example`:

```text
CORS_ALLOW_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,null
CACHE_CRON_SCHEDULE=0 * * * *
GOOGLE_SPREADSHEET_ID=your-google-spreadsheet-id
GOOGLE_SPREADSHEET_RANGE=A:D
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}
# Optional: leave empty to read every sheet tab in the spreadsheet.
GOOGLE_SHEET_NAMES=
```

| Variable                      | Required | Description                                                                |
| ----------------------------- | -------- | -------------------------------------------------------------------------- |
| `CORS_ALLOW_ORIGINS`          | No       | Comma-separated allowlist. Default includes `null` for local dev.          |
| `CACHE_CRON_SCHEDULE`         | Yes      | Crontab expression for vocabulary refresh (e.g. `0 * * * *` = every hour). |
| `GOOGLE_SPREADSHEET_ID`       | Yes      | The ID from the spreadsheet URL.                                           |
| `GOOGLE_SPREADSHEET_RANGE`    | Yes      | Column range to read (e.g. `A:D` or `A:F`).                                |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Yes      | Full JSON key. Never commit this.                                          |
| `GOOGLE_SHEET_NAMES`          | No       | Comma-separated list of sheet tabs to read. Empty = read all tabs.         |

## Endpoints

| Method         | Path          | Description                                           |
| -------------- | ------------- | ----------------------------------------------------- |
| `GET`          | `/vocabulary` | Returns all vocabulary grouped by sheet name.         |
| `GET` / `HEAD` | `/healthz`    | Returns `{}` with status 200. Used for health checks. |

## Running Locally

```powershell
cd server
```

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the API from the `server` directory:

```powershell
uvicorn main:app --host 127.0.0.1 --port 5000 --reload
```

Open `index.html` in a browser. The frontend calls:

```text
http://localhost:5000/vocabulary
```

## Tests

Run the backend tests under `server` with:

```powershell
pytest
```
