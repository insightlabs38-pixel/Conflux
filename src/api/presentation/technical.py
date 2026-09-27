"""Render participant-authored project descriptions for the public site."""

from html import escape

from markdown_it import MarkdownIt
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.util import ClassNotFound


def _highlight(code: str, language: str, _attrs: str) -> str:
    if not language:
        return escape(code)
    try:
        lexer = get_lexer_by_name(language, stripall=False)
    except ClassNotFound:
        lexer = TextLexer()
    return highlight(code, lexer, HtmlFormatter(nowrap=True, noclasses=True))


_markdown = (
    MarkdownIt("commonmark", {"html": False, "highlight": _highlight})
    .enable("table")
    .disable("image")
)


def render_technical_description(value: str) -> str:
    tokens = _markdown.parse(value or "")
    for token in tokens:
        if token.type in {"heading_open", "heading_close"}:
            token.tag = f"h{min(int(token.tag[1:]) + 1, 6)}"
    return _markdown.renderer.render(tokens, _markdown.options, {})
