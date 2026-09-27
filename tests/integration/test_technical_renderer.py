from presentation.technical import render_technical_description


def test_renders_project_technical_content():
    html = render_technical_description(
        "# Build notes\n\nUses `pytest` and [source](https://example.com/repo).\n\n"
        "| Tool | Role |\n| --- | --- |\n| Python | API |\n\n"
        "```python\nprint('ready')\n```"
    )
    assert "<h2>Build notes</h2>" in html
    assert "<code>pytest</code>" in html
    assert '<a href="https://example.com/repo">source</a>' in html
    assert "<table>" in html
    assert '<code class="language-python">' in html
    assert "print" in html


def test_escapes_html_and_unsafe_links_and_code():
    html = render_technical_description(
        '<script>alert("bad")</script>\n\n'
        "[bad](javascript:alert(1)) ![remote](https://example.com/tracker.png)\n\n"
        "```unlisted-language\n<img src=x onerror=alert(1)>\n```"
    )
    assert "<script" not in html
    assert "<img" not in html
    assert "javascript:" in html
    assert 'href="javascript:' not in html
    assert "onerror=alert(1)" in html
    assert "&lt;img" in html


def test_plain_legacy_description_remains_readable():
    assert render_technical_description("Grades things.") == "<p>Grades things.</p>\n"
