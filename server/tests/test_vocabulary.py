from services.vocabulary import parse_sheet_rows, quote_sheet_name


def test_parse_sheet_rows_extracts_entries_and_skips_header():
    rows = [
        ["Deutsch", "Englisch", "Beispiel Deutsch", "Beispiel Englisch"],
        ["Hallo", "Hello", "Hallo Welt", "Hello world"],
        ["Tschuess", "Bye"],
        ["", "Missing source"],
        ["Missing translation", ""],
    ]

    assert parse_sheet_rows(rows) == [
        {
            "source": "Hallo",
            "translation": "Hello",
            "sourceExample": "Hallo Welt",
            "translationExample": "Hello world",
        },
        {
            "source": "Tschuess",
            "translation": "Bye",
            "sourceExample": None,
            "translationExample": None,
        },
    ]


def test_quote_sheet_name_escapes_single_quotes():
    assert quote_sheet_name("Hani's Words") == "'Hani''s Words'"
