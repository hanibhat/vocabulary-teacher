import json
import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import config

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Cached service instance to avoid rebuilding the HTTP transport
# and re-parsing the discovery document on every request.
_sheets_service = None
_vocabulary: dict[str, list[dict]] = {}


def get_service_account_credentials():
    service_account_json = config.google_service_account_json
    try:
        service_account_info = json.loads(service_account_json)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"{config.google_service_account_json_env} must contain valid service account JSON"
        ) from error
    return service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES,
    )


def build_sheets_service():
    global _sheets_service
    if _sheets_service is not None:
        return _sheets_service
    logger.info("Building Google Sheets API service")
    credentials = get_service_account_credentials()
    _sheets_service = build(
        "sheets", "v4", credentials=credentials, cache_discovery=False
    )
    return _sheets_service


def get_sheet_names(service, spreadsheet_id):
    try:
        spreadsheet = (
            service.spreadsheets()
            .get(spreadsheetId=spreadsheet_id, fields="sheets.properties.title")
            .execute()
        )
    except HttpError as error:
        raise RuntimeError(
            f"Failed to read spreadsheet metadata: {error.reason}"
        ) from error
    sheet_names = [
        sheet["properties"]["title"]
        for sheet in spreadsheet.get("sheets", [])
        if sheet.get("properties", {}).get("title")
    ]
    if not sheet_names:
        raise RuntimeError("Spreadsheet does not contain any sheets")
    return sheet_names


def quote_sheet_name(sheet_name):
    escaped_sheet_name = sheet_name.replace("'", "''")
    return f"'{escaped_sheet_name}'"


def get_sheet_values(service, spreadsheet_id, sheet_name):
    try:
        result = (
            service.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=f"{quote_sheet_name(sheet_name)}!{config.google_sheet_range}",
                valueRenderOption="FORMATTED_VALUE",
            )
            .execute()
        )
    except HttpError as error:
        raise RuntimeError(
            f"Failed to read sheet '{sheet_name}': {error.reason}"
        ) from error
    return result.get("values", [])


def normalize_cell(value):
    return str(value or "").strip()


def parse_sheet_rows(rows):
    """Parse rows using column header names as keys."""
    entries = []
    columns = {}
    for rowIndex, row in enumerate(rows):
        # First row is the columns' headers
        if rowIndex == 0:
            columns = {cell.lower(): i for i, cell in enumerate(row)}
            continue
        cells = [normalize_cell(cell) for cell in row]
        entry = {key: cells[i] if i < len(cells) else "" for key, i in columns.items()}
        entries.append(entry)
    return entries


def fetch_vocabulary_from_sheets(service, spreadsheet_id, sheet_names):
    global _vocabulary
    for sheet_name in sheet_names:
        logger.info("Fetching sheet: %s", sheet_name)
        rows = get_sheet_values(service, spreadsheet_id, sheet_name)
        entries = parse_sheet_rows(rows)
        if entries:
            _vocabulary[sheet_name] = entries
    return _vocabulary


def make_vocabulary():
    service = build_sheets_service()
    spreadsheet_id = config.google_spreadsheet_id
    logger.info("Fetching vocabulary data")
    sheet_names = config.google_sheet_names or get_sheet_names(service, spreadsheet_id)
    global _vocabulary
    _vocabulary = fetch_vocabulary_from_sheets(service, spreadsheet_id, sheet_names)
    logger.info("Fetched %d vocabulary sheets", len(_vocabulary))


def get_vocabulary():
    global _vocabulary
    if not _vocabulary:
        make_vocabulary()
    return _vocabulary
