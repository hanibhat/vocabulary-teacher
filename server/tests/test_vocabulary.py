from services.vocabulary import parse_sheet_rows, quote_sheet_name


def test_parse_sheet_rows_extracts_entries_using_header_columns():
    rows = [
        ["Deutsch", "Englisch", "Beispiel Deutsch", "Beispiel Englisch"],
        ["Hallo", "Hello", "Hallo Welt", "Hello world"],
        ["Tschuess", "Bye"],
        ["", "Missing source"],
        ["Missing translation", ""],
    ]

    assert parse_sheet_rows(rows) == [
        {
            "deutsch": "Hallo",
            "englisch": "Hello",
            "beispiel deutsch": "Hallo Welt",
            "beispiel englisch": "Hello world",
        },
        {
            "deutsch": "Tschuess",
            "englisch": "Bye",
            "beispiel deutsch": "",
            "beispiel englisch": "",
        },
        {
            "deutsch": "",
            "englisch": "Missing source",
            "beispiel deutsch": "",
            "beispiel englisch": "",
        },
        {
            "deutsch": "Missing translation",
            "englisch": "",
            "beispiel deutsch": "",
            "beispiel englisch": "",
        },
    ]


def test_quote_sheet_name_escapes_single_quotes():
    assert quote_sheet_name("Hani's Words") == "'Hani''s Words'"
