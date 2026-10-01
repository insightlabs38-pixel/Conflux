"""Rich technical content as one primitive (RICH_DOC, PD-F002-B02-T02).

A *profile* names how a piece of source text is understood: `story` is CommonMark for what
participants write about their projects, `page` is the allowlist HTML organizers write on public
pages. Each profile renders in two forms that agree: `render_html` for server-rendered pages and
`render_tree` for the browser, a closed tree of nodes that React renders without ever injecting
HTML. Nothing here stores anything, and the node set is the only thing that can reach a page:
raw HTML, images, scripts, event handlers and every URL scheme other than http, https and mailto
(or none at all, a relative link) are dropped or shown as text.

A feature registers no profile of its own: it names one of these two and, if it needs a third,
adds it here beside them so every rendering keeps a single set of rules.
"""

from collections.abc import Callable
from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit

from markdown_it import MarkdownIt
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.token import STANDARD_TYPES
from pygments.util import ClassNotFound

from .rich_page import SAFE_URL_SCHEMES, sanitize_html

MAX_SOURCE = 100_000
MAX_NODES = 20_000
MAX_DEPTH = 32


class RichError(ValueError):
    """The source cannot be rendered; `code` is machine readable, the message is for people."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def safe_url(value: str) -> bool:
    """A relative link, or one on http, https or mailto; never `javascript:` or `data:`."""
    scheme = urlsplit((value or "").strip()).scheme.lower()
    return not scheme or scheme in SAFE_URL_SCHEMES


# --- story: CommonMark ----------------------------------------------------------------------


def _highlight(code: str, language: str, _attrs: str) -> str:
    if not language:
        return escape(code)
    try:
        lexer = get_lexer_by_name(language, stripall=False)
    except ClassNotFound:
        lexer = TextLexer()
    return highlight(code, lexer, HtmlFormatter(nowrap=True, noclasses=True))


def _markdown() -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": False, "highlight": _highlight})
    md.enable("table").disable("image")
    # markdown-it refuses javascript:, vbscript:, file: and data: only; the platform allows three.
    md.validateLink = lambda url: safe_url(url)
    return md


_md = _markdown()


def _story_html(source: str) -> str:
    tokens = _md.parse(source or "")
    for token in tokens:
        if token.type in {"heading_open", "heading_close"}:
            token.tag = f"h{min(int(token.tag[1:]) + 1, 6)}"
    return _md.renderer.render(tokens, _md.options, {})


def _kind(token_type) -> str:
    while token_type is not None and token_type not in STANDARD_TYPES:
        token_type = token_type.parent
    return STANDARD_TYPES.get(token_type, "") if token_type is not None else ""


def _tokens(code: str, language: str) -> list[list[str]]:
    """Highlighted runs `[kind, text]` (kind is pygments' short class, "" for plain text)."""
    try:
        lexer = get_lexer_by_name(language, stripall=False) if language else TextLexer()
    except ClassNotFound:
        lexer = TextLexer()
    runs: list[list[str]] = []
    for token_type, text in lexer.get_tokens(code):
        kind = _kind(token_type)
        if runs and runs[-1][0] == kind:
            runs[-1][1] += text
        else:
            runs.append([kind, text])
    return runs


class _Builder:
    """Builds the tree and enforces its size and depth limits."""

    def __init__(self):
        self.count = 0
        self.root = {"type": "doc", "children": []}
        self.stack = [self.root]

    def add(self, node: dict) -> dict:
        self.count += 1
        if self.count > MAX_NODES:
            raise RichError("too_complex", f"The content has more than {MAX_NODES} parts.")
        self.stack[-1]["children"].append(node)
        return node

    def push(self, node: dict) -> None:
        self.add(node)
        if len(self.stack) >= MAX_DEPTH:
            raise RichError("too_deep", f"The content nests deeper than {MAX_DEPTH} levels.")
        self.stack.append(node)

    def pop(self) -> None:
        if len(self.stack) > 1:
            self.stack.pop()


_OPEN = {
    "paragraph_open": lambda t: {"type": "paragraph", "children": []},
    "heading_open": lambda t: {
        "type": "heading",
        "level": min(int(t.tag[1:]) + 1, 6),
        "children": [],
    },
    "bullet_list_open": lambda t: {"type": "list", "ordered": False, "start": 1, "children": []},
    "ordered_list_open": lambda t: {
        "type": "list",
        "ordered": True,
        "start": int(t.attrGet("start") or 1),
        "children": [],
    },
    "list_item_open": lambda t: {"type": "item", "children": []},
    "blockquote_open": lambda t: {"type": "quote", "children": []},
    "table_open": lambda t: {"type": "table", "children": []},
    "tr_open": lambda t: {"type": "row", "header": False, "children": []},
    "th_open": lambda t: {"type": "cell", "align": _align(t), "children": []},
    "td_open": lambda t: {"type": "cell", "align": _align(t), "children": []},
    "em_open": lambda t: {"type": "emphasis", "children": []},
    "strong_open": lambda t: {"type": "strong", "children": []},
}
# Wrappers that carry no node of their own (their content goes to the parent).
_TRANSPARENT = {"thead_open", "thead_close", "tbody_open", "tbody_close"}


def _align(token) -> str | None:
    style = token.attrGet("style") or ""
    for value in ("left", "center", "right"):
        if value in style:
            return value
    return None


def _story_tree(source: str) -> dict:
    builder = _Builder()
    header = False

    def walk(tokens):
        nonlocal header
        for token in tokens:
            kind = token.type
            if kind == "inline":
                walk(token.children or [])
            elif kind == "thead_open":
                header = True
            elif kind == "thead_close":
                header = False
            elif kind in _TRANSPARENT:
                continue
            elif kind == "paragraph_open" and token.hidden:
                continue  # a tight list item's text sits directly in the item
            elif kind == "paragraph_close" and token.hidden:
                continue
            elif kind == "link_open":
                builder.push({"type": "link", "href": token.attrGet("href") or "", "children": []})
            elif kind in _OPEN:
                node = _OPEN[kind](token)
                if node["type"] == "row":
                    node["header"] = header
                builder.push(node)
            elif kind.endswith("_close"):
                builder.pop()
            elif kind == "text":
                builder.add({"type": "text", "text": token.content})
            elif kind == "code_inline":
                builder.add({"type": "code_span", "text": token.content})
            elif kind == "softbreak":
                builder.add({"type": "text", "text": "\n"})
            elif kind == "hardbreak":
                builder.add({"type": "break"})
            elif kind in {"fence", "code_block"}:
                language = (token.info or "").strip().split(" ")[0] if kind == "fence" else ""
                builder.add(
                    {
                        "type": "code",
                        "language": language,
                        "text": token.content,
                        "tokens": _tokens(token.content, language),
                    }
                )
            elif kind == "hr":
                builder.add({"type": "rule"})
            # anything else (html, images, extensions) is not part of the node set

    walk(_md.parse(source or ""))
    return builder.root


# --- page: allowlist HTML -------------------------------------------------------------------

_PAGE_BLOCKS = {"p": "paragraph", "blockquote": "quote", "ul": "list", "ol": "list", "li": "item"}
_PAGE_INLINE = {"strong": "strong", "em": "emphasis"}


class _PageTree(HTMLParser):
    """Reads already-sanitised HTML (`presentation.sanitize`) into the node tree."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.builder = _Builder()
        self.tags: list[bool] = []  # per open element: did it push a node

    def handle_starttag(self, tag, attrs):
        if tag == "br":  # void: no end tag follows
            self.builder.add({"type": "break"})
            return
        node = None
        if tag in _PAGE_BLOCKS:
            node = {"type": _PAGE_BLOCKS[tag], "children": []}
            if tag in ("ul", "ol"):
                node.update(ordered=tag == "ol", start=1)
        elif tag in ("h2", "h3", "h4"):
            node = {"type": "heading", "level": int(tag[1]), "children": []}
        elif tag in _PAGE_INLINE:
            node = {"type": _PAGE_INLINE[tag], "children": []}
        elif tag == "a":
            href = dict(attrs).get("href") or ""
            if href and safe_url(href):  # the sanitiser already dropped the rest
                node = {"type": "link", "href": href, "children": []}
        if node is None:
            self.tags.append(False)
            return
        self.builder.push(node)
        self.tags.append(True)

    def handle_startendtag(self, tag, attrs):
        if tag == "br":
            self.builder.add({"type": "break"})

    def handle_endtag(self, tag):
        if self.tags and self.tags.pop():
            self.builder.pop()

    def handle_data(self, data):
        if data:
            self.builder.add({"type": "text", "text": data})


def _page_tree(source: str) -> dict:
    parser = _PageTree()
    parser.feed(sanitize_html(source))
    parser.close()
    return parser.builder.root


# --- profiles -------------------------------------------------------------------------------


@dataclass(frozen=True)
class Profile:
    name: str
    label: str
    max_length: int
    html: Callable[[str], str]
    tree: Callable[[str], dict]


PROFILES = {
    "story": Profile("story", "Project story (Markdown)", MAX_SOURCE, _story_html, _story_tree),
    "page": Profile("page", "Page text (HTML)", MAX_SOURCE, sanitize_html, _page_tree),
}


def profile(name: str) -> Profile:
    try:
        return PROFILES[name]
    except KeyError:
        raise RichError("unknown_profile", f"There is no content profile '{name}'.") from None


def render_html(source: str, name: str) -> str:
    """The page rendering. Unbounded on purpose: stored content keeps rendering as it always did."""
    return profile(name).html(source or "")


def render_tree(source: str, name: str) -> dict:
    """The browser rendering. Bounded: a source above `max_length` is refused, not truncated."""
    selected = profile(name)
    source = source or ""
    if len(source) > selected.max_length:
        raise RichError(
            "too_long",
            f"The text is {len(source):,} characters; the limit is {selected.max_length:,}.",
        )
    return selected.tree(source)
