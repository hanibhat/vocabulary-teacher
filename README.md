# Vocabulary Teacher

Vocabulary Teacher is a small vocabulary practice app with a FastAPI backend and a static Alpine.js frontend. The backend reads vocabulary from a Google Spreadsheet with a Google service account and exposes it through one endpoint. The frontend loads that endpoint, caches usable vocabulary in `localStorage` until midnight, and gives learners a simple German UI for category-based practice.

## Features

- Organizes words by category so users can study one topic at a time or review everything together.
- Lets users filter by source phrase.
- Creates random practice sets from all words or from a selected category.
- Lets users manually refresh content when the spreadsheet changes.
- Includes a privacy policy page and does not use analytics, advertising cookies, or tracking cookies.

## How It Works

- The backend reads one or more sheet tabs from a Google Spreadsheet.
- Each sheet tab becomes one vocabulary category.
- Vocabulary is served from a single `GET /vocabulary` endpoint.
- The frontend caches non-empty API responses in `localStorage` until the next midnight.
- Empty responses are not cached, so temporary source or parsing issues do not poison the browser cache.

## Project Shape

```text
server/main.py                 FastAPI app, CORS, and route lockdown
server/config.py               Environment configuration
server/routes/vocabulary.py    /vocabulary route and API error mapping
server/services/vocabulary.py  Google Sheets fetching and vocabulary shaping
server/requirements.txt        Backend dependencies
server/tests/                  Backend parser tests
index.html                     Static German frontend
index.js                       Frontend state, caching, filtering, and shuffle logic
privacy.html                   Privacy policy
```

## Expected Google Spreadsheet

Create one sheet tab per category. Each sheet should use columns A-D:

| Column | Meaning                       |
| ------ | ----------------------------- |
| A      | Source phrase                 |
| B      | Translation                   |
| C      | Source example, optional      |
| D      | Translation example, optional |

The first row can be a header row such as `Deutsch`, `Englisch`, `Beispiel Deutsch`, `Beispiel Englisch`; the backend skips it automatically.

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
GOOGLE_SPREADSHEET_ID=your-google-spreadsheet-id
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}
# Optional: leave empty to read every sheet tab in the spreadsheet.
GOOGLE_SHEET_NAMES=
```

`CORS_ALLOW_ORIGINS` is a comma-separated allowlist. The default includes `null` so the app can be opened directly from `index.html` during local development.

`GOOGLE_SERVICE_ACCOUNT_JSON` should contain the full service account JSON key. Keep it in environment variables or local `.env` files only; never commit it.

`GOOGLE_SHEET_NAMES` is optional. If it is empty, the backend reads every sheet tab. If set, use a comma-separated list such as:

```text
GOOGLE_SHEET_NAMES=Basics,Verben,Redewendungen
```

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
