from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from pyquery import PyQuery

from config import config


class VocabularyConfigError(RuntimeError):
    pass


class VocabularyFetchError(RuntimeError):
    pass


def get_html():
    try:
        source_url = config.doc_url
    except RuntimeError as error:
        raise VocabularyConfigError(str(error)) from error

    parsed_url = urlparse(source_url)
    if parsed_url.scheme not in {"http", "https"}:
        raise VocabularyConfigError(f"{config.doc_url_env} must be an http or https URL")

    request = Request(source_url)

    try:
        with urlopen(request, timeout=config.fetch_timeout_seconds) as response:
            return response.read().decode(response.headers.get_content_charset() or "utf-8")
    except HTTPError as error:
        raise VocabularyFetchError(f"Failed to fetch vocabulary page: HTTP {error.code}") from error
    except URLError as error:
        raise VocabularyFetchError(f"Failed to fetch vocabulary page: {error.reason}") from error


def parse_vocabulary_tables(html):
    page = PyQuery(html)
    vocabulary = {}

    for table in page("table").items():
        category = table("thead tr td h2").eq(0).text().strip()
        if not category:
            continue

        entries = []
        for i, row in enumerate(table("tr").items()):
            # skip category row and header row
            if i <= 1:
                continue
            cells = [cell("p span").text().strip() for cell in row("td").items()]

            entries.append(
                {
                    "source": cells[0],
                    "translation": cells[1],
                    "sourceExample": cells[2] if len(cells) > 2 else None,
                    "translationExample": cells[3] if len(cells) > 3 else None,
                }
            )

        if len(entries) > 0:
            vocabulary[category] = entries

    return vocabulary


def make_vocabulary():
    html = get_html()
    return parse_vocabulary_tables(html)
