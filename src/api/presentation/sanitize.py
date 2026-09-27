"""Allowlist HTML sanitizer for organizer-authored rich text (PAGE-003).

Stdlib only (`html.parser`), so there is no arbitrary organizer JS: only a
fixed set of formatting tags survive, `href`/`src` are restricted to safe
schemes, and every other attribute (including all `on*` handlers) is
dropped. Applied both when an organizer saves a RichText block and again
when it's rendered, so a bypass at one layer isn't a compromise on its own.
"""

from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit

ALLOWED_TAGS = {
    "p",
    "br",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "a",
    "h2",
    "h3",
    "h4",
    "blockquote",
}
ALLOWED_ATTRS = {"a": {"href"}}
SAFE_URL_SCHEMES = {"http", "https", "mailto"}
VOID_TAGS = {"br"}
# HTMLParser hands these tags' bodies to handle_data verbatim (CDATA mode);
# an allowlist on tags alone would still leak the script/style *text*.
RAW_TEXT_TAGS = {"script", "style"}


def _safe_href(value: str) -> str | None:
    value = value.strip()
    scheme = urlsplit(value).scheme.lower()
    # No scheme at all means a relative link (e.g. "/gallery"), which is safe;
    # anything else must be on the explicit allowlist (blocks "javascript:").
    if scheme and scheme not in SAFE_URL_SCHEMES:
        return None
    return value


class _Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.open_stack: list[str] = []
        self.raw_text_tag: str | None = None

    def handle_starttag(self, tag, attrs):
        if tag in RAW_TEXT_TAGS:
            self.raw_text_tag = tag
            return
        self._open(tag, attrs, self_closing=False)

    def handle_startendtag(self, tag, attrs):
        self._open(tag, attrs, self_closing=True)

    def _open(self, tag, attrs, *, self_closing):
        if tag not in ALLOWED_TAGS:
            return
        kept = []
        for name, value in attrs:
            if tag in ALLOWED_ATTRS and name in ALLOWED_ATTRS[tag] and value:
                if name == "href":
                    value = _safe_href(value)
                    if value is None:
                        continue
                kept.append(f'{name}="{escape(value, quote=True)}"')
        attr_str = (" " + " ".join(kept)) if kept else ""
        if tag in VOID_TAGS or self_closing:
            self.out.append(f"<{tag}{attr_str}>")
        else:
            self.out.append(f"<{tag}{attr_str}>")
            self.open_stack.append(tag)

    def handle_endtag(self, tag):
        if tag in RAW_TEXT_TAGS:
            if self.raw_text_tag == tag:
                self.raw_text_tag = None
            return
        if tag not in ALLOWED_TAGS or tag in VOID_TAGS:
            return
        if tag in self.open_stack:
            # Close out any unbalanced inner tags first, then this one.
            while self.open_stack and self.open_stack[-1] != tag:
                self.out.append(f"</{self.open_stack.pop()}>")
            self.open_stack.pop()
            self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if self.raw_text_tag:
            return
        self.out.append(escape(data))

    def close(self):
        super().close()
        while self.open_stack:
            self.out.append(f"</{self.open_stack.pop()}>")


def sanitize_html(value: str) -> str:
    """Return `value` with only ALLOWED_TAGS/ALLOWED_ATTRS surviving."""
    parser = _Sanitizer()
    parser.feed(value or "")
    parser.close()
    return "".join(parser.out)
