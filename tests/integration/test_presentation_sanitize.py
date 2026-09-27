from presentation.sanitize import sanitize_html


def test_strips_script_tags_and_their_text_content():
    assert sanitize_html("<p>Hi <script>alert(1)</script></p>") == "<p>Hi </p>"


def test_strips_event_handler_attributes():
    assert sanitize_html('<p onclick="evil()">Hi</p>') == "<p>Hi</p>"


def test_blocks_javascript_scheme_links_but_keeps_safe_ones():
    assert sanitize_html('<a href="javascript:evil()">x</a>') == "<a>x</a>"
    assert sanitize_html('<a href="https://example.com">x</a>') == (
        '<a href="https://example.com">x</a>'
    )
    assert sanitize_html('<a href="/gallery">x</a>') == '<a href="/gallery">x</a>'


def test_drops_disallowed_tags_but_keeps_their_text():
    assert sanitize_html("<div>hello</div>") == "hello"


def test_closes_unbalanced_tags():
    assert sanitize_html("<p>unterminated") == "<p>unterminated</p>"
