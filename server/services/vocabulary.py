import json
import logging
import time

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import config

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
VALUE_RANGE = "A:D"

# Cached service instance to avoid rebuilding the HTTP transport
# and re-parsing the discovery document on every request.
_sheets_service = None

_cache: dict = {}
_cache_timestamp: float = 0
_cache_ttl_seconds = config.cache_ttl_seconds


class VocabularyConfigError(RuntimeError):
    pass


class VocabularyFetchError(RuntimeError):
    pass


def get_service_account_credentials():
    try:
        service_account_json = config.google_service_account_json
    except RuntimeError as error:
        raise VocabularyConfigError(str(error)) from error
    try:
        service_account_info = json.loads(service_account_json)
    except json.JSONDecodeError as error:
        raise VocabularyConfigError(
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
        raise VocabularyFetchError(
            f"Failed to read spreadsheet metadata: {error.reason}"
        ) from error
    sheet_names = [
        sheet["properties"]["title"]
        for sheet in spreadsheet.get("sheets", [])
        if sheet.get("properties", {}).get("title")
    ]
    if not sheet_names:
        raise VocabularyFetchError("Spreadsheet does not contain any sheets")
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
                range=f"{quote_sheet_name(sheet_name)}!{VALUE_RANGE}",
                valueRenderOption="FORMATTED_VALUE",
            )
            .execute()
        )
    except HttpError as error:
        raise VocabularyFetchError(
            f"Failed to read sheet '{sheet_name}': {error.reason}"
        ) from error
    return result.get("values", [])


def normalize_cell(value):
    return str(value or "").strip()


def normalize_row(row):
    return [
        normalize_cell(row[index]) if index < len(row) else "" for index in range(4)
    ]


def has_required_cells(cells):
    return bool(cells[0] and cells[1])


def parse_sheet_rows(rows):
    entries = []
    for i, row in enumerate(rows):
        # Skip the first row, which is expected to be a header row.
        if i == 0:
            continue
        cells = normalize_row(row)
        if not has_required_cells(cells):
            continue
        entries.append(
            {
                "source": cells[0],
                "translation": cells[1],
                "sourceExample": cells[2] or None,
                "translationExample": cells[3] or None,
            }
        )
    return entries


def fetch_vocabulary_from_sheets(service, spreadsheet_id, sheet_names):
    vocabulary: dict[str, list[dict]] = {}
    for sheet_name in sheet_names:
        logger.info("Fetching sheet: %s", sheet_name)
        rows = get_sheet_values(service, spreadsheet_id, sheet_name)
        entries = parse_sheet_rows(rows)
        if entries:
            vocabulary[sheet_name] = entries
    return vocabulary


def is_cache_valid():
    return bool(_cache) and (time.monotonic() - _cache_timestamp) < _cache_ttl_seconds


def make_vocabulary():
    global _cache, _cache_timestamp
    if is_cache_valid():
        logger.info("Returning cached vocabulary data")
        return _cache

    service = build_sheets_service()
    logger.info("Fetching vocabulary data")
    try:
        spreadsheet_id = config.google_spreadsheet_id
    except RuntimeError as error:
        raise VocabularyConfigError(str(error)) from error
    sheet_names = config.google_sheet_names or get_sheet_names(service, spreadsheet_id)
    vocabulary = fetch_vocabulary_from_sheets(service, spreadsheet_id, sheet_names)
    logger.info("Fetched %d vocabulary sheets", len(vocabulary))

    _cache = vocabulary
    _cache_timestamp = time.monotonic()

    return vocabulary
