from server.services.vocabulary import parse_vocabulary_tables


def test_parse_vocabulary_tables_extracts_categories_and_entries():
    html = """
    <table>
      <thead>
        <tr><td><h2>Grundlagen</h2></td></tr>
      </thead>
      <tbody>
        <tr><td><p><span>Header</span></p></td></tr>
        <tr>
          <td><p><span>Hallo</span></p></td>
          <td><p><span>Hello</span></p></td>
          <td><p><span>Hallo Welt</span></p></td>
        </tr>
        <tr>
          <td><p><span>Tschuess</span></p></td>
          <td><p><span>Bye</span></p></td>
        </tr>
      </tbody>
    </table>
    """

    assert parse_vocabulary_tables(html) == {
        "Grundlagen": [
            {
                "source": "Hallo",
                "translation": "Hello",
                "sourceExample": "Hallo Welt",
            },
            {
                "source": "Tschuess",
                "translation": "Bye",
                "sourceExample": None,
            },
        ]
    }


def test_parse_vocabulary_tables_ignores_tables_without_category():
    html = """
    <table>
      <tbody>
        <tr><td><p><span>Hallo</span></p></td><td><p><span>Hello</span></p></td></tr>
      </tbody>
    </table>
    """

    assert parse_vocabulary_tables(html) == {}
