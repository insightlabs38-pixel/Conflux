"""PD-F002-B02-T02: the rich-content primitive, its conformance and its adopters."""

import json
import pathlib
import random
import string
from html import escape

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from core import rich
from django.test import Client
from markdown_it import MarkdownIt
from presentation.sanitize import sanitize_html
from presentation.technical import render_technical_description
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.util import ClassNotFound
from workspaces.models import Membership, Role, Workspace

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / "tests/fixtures/rich_cases.json").read_text())["cases"]


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_the_shared_fixtures_hold(case):
    """The same file is drawn by vitest (src/web/lib/rich.test.ts) from the server's trees."""
    assert rich.render_tree(case["source"], case["profile"]) == case["tree"]


# --- the absorbed near-implementations stay byte-identical ---------------------------------


def _legacy_highlight(code, language, _attrs):
    if not language:
        return escape(code)
    try:
        lexer = get_lexer_by_name(language, stripall=False)
    except ClassNotFound:
        lexer = TextLexer()
    return highlight(code, lexer, HtmlFormatter(nowrap=True, noclasses=True))


_LEGACY_MD = (
    MarkdownIt("commonmark", {"html": False, "highlight": _legacy_highlight})
    .enable("table")
    .disable("image")
)


def legacy_render_technical_description(value):
    """A frozen copy of `presentation.technical` as it was before it adopted `core.rich`."""
    tokens = _LEGACY_MD.parse(value or "")
    for token in tokens:
        if token.type in {"heading_open", "heading_close"}:
            token.tag = f"h{min(int(token.tag[1:]) + 1, 6)}"
    return _LEGACY_MD.renderer.render(tokens, _LEGACY_MD.options, {})


FRAGMENTS = [
    "# Title\n\n",
    "## Sub *heading*\n\n",
    "Plain text with `code` and **bold** and _em_.\n\n",
    "A [link](https://example.com/a?b=1&c=2) and [rel](/x/y) and <https://auto.example.com>.\n\n",
    "[mail](mailto:a@example.com) ![img](https://example.com/i.png)\n\n",
    "- one\n- two\n  - nested\n\n",
    "1. first\n2. second\n\n",
    "5. five\n\n6. six\n\n",
    "> a quote\n> over two lines\n\n",
    "| a | b |\n|:--|--:|\n| 1 | 2 |\n\n",
    "```python\ndef f(x):\n    return x * 2  # double\n```\n\n",
    "```js\nconst s = '<b>';\n```\n\n",
    "```nolang\n<script>alert(1)</script>\n```\n\n",
    "    indented code\n\n",
    "<script>alert(1)</script> <b>raw</b> &amp; &lt;\n\n",
    "[bad](javascript:alert(1)) [d](data:text/html,x) [v](vbscript:x)\n\n",
    "line one  \nline two\\\nline three\n\n",
    "---\n\n",
    "Ünïcode ✓ — 日本語\n\n",
]


def test_the_story_profile_renders_exactly_as_the_old_renderer_did():
    rng = random.Random(7)
    for fragment in FRAGMENTS:
        assert render_technical_description(fragment) == legacy_render_technical_description(
            fragment
        )
    for _ in range(300):
        source = "".join(rng.choice(FRAGMENTS) for _ in range(rng.randint(1, 8)))
        assert rich.render_html(source, "story") == legacy_render_technical_description(source)
        assert render_technical_description(source) == legacy_render_technical_description(source)
    assert render_technical_description("") == legacy_render_technical_description("")
    assert render_technical_description(None) == "" == legacy_render_technical_description(None)


def test_the_one_intended_difference_is_that_only_three_schemes_are_links():
    source = "[f](ftp://example.com/x) [t](tel:+15551234) [g](git://example.com/r)"
    assert legacy_render_technical_description(source).count("<a ") == 3
    html = rich.render_html(source, "story")
    assert "<a " not in html and "ftp://example.com/x" in html
    for allowed in ("https://e.com", "http://e.com", "mailto:a@e.com", "/relative", "#anchor"):
        assert f'href="{allowed}"' in rich.render_html(f"[x]({allowed})", "story")


def test_the_page_profile_is_the_presentation_sanitiser():
    assert rich.render_html("<p onclick=x()>Hi<script>a</script></p>", "page") == "<p>Hi</p>"
    for source in ("<p>unterminated", "<div>hello</div>", '<a href="javascript:x">y</a>'):
        assert rich.render_html(source, "page") == sanitize_html(source)


# --- the tree is a closed set, whatever the input -----------------------------------------

NODE_KEYS = {
    "doc": {"children"},
    "paragraph": {"children"},
    "heading": {"level", "children"},
    "list": {"ordered", "start", "children"},
    "item": {"children"},
    "quote": {"children"},
    "code": {"language", "text", "tokens"},
    "table": {"children"},
    "row": {"header", "children"},
    "cell": {"align", "children"},
    "rule": set(),
    "text": {"text"},
    "emphasis": {"children"},
    "strong": {"children"},
    "code_span": {"text"},
    "link": {"href", "children"},
    "break": set(),
}


def walk(node):
    yield node
    for child in node.get("children", []):
        yield from walk(child)


def assert_closed(tree):
    for node in walk(tree):
        assert node["type"] in NODE_KEYS, node["type"]
        assert set(node) - {"type"} == NODE_KEYS[node["type"]], node
        if node["type"] == "link":
            assert node["href"] and rich.safe_url(node["href"]), node["href"]
        if node["type"] == "heading":
            assert 2 <= node["level"] <= 6


HOSTILE = [
    '<script>alert(1)</script><img src=x onerror=alert(1)><a href="javascript:alert(1)">x</a>',
    "[x](JaVaScRiPt:alert(1)) [y](  javascript:alert(1)) [z](&#106;avascript:alert(1))",
    "[a](data:text/html;base64,PHNjcmlwdD4=) ![i](data:image/svg+xml,<svg onload=x>)",
    "<iframe src=//evil></iframe><style>*{}</style><svg onload=alert(1)>",
    "```\n</code></pre><script>alert(1)</script>\n```",
]


@pytest.mark.parametrize("name", sorted(rich.PROFILES))
@pytest.mark.parametrize("source", HOSTILE)
def test_hostile_input_never_leaves_the_node_set(name, source):
    tree = rich.render_tree(source, name)
    assert_closed(tree)
    html = rich.render_html(source, name)
    for tag in ("<script", "<iframe", "<img", "<svg", "<style"):
        assert tag not in html.lower()
    assert 'href="javascript:' not in html.lower() and 'href="data:' not in html.lower()


def test_text_that_looks_like_markup_stays_text():
    tree = rich.render_tree("<b>x</b> <script>alert(1)</script>", "story")
    assert [n["text"] for n in walk(tree) if n["type"] == "text"] == [
        "<b>x</b> <script>alert(1)</script>"
    ]


@pytest.mark.parametrize("name", sorted(rich.PROFILES))
def test_random_input_renders_or_is_refused_with_a_code(name):
    rng = random.Random(11)
    alphabet = string.printable + "<>[]()`*_#|-\\&;:\"'ü日"
    for _ in range(400):
        source = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 200)))
        try:
            assert_closed(rich.render_tree(source, name))
        except rich.RichError as error:
            assert error.code in {"too_complex", "too_deep", "too_long"}


# --- limits and errors ------------------------------------------------------------------


def test_a_source_over_the_limit_is_refused_and_not_truncated():
    with pytest.raises(rich.RichError) as caught:
        rich.render_tree("a" * (rich.MAX_SOURCE + 1), "story")
    assert caught.value.code == "too_long" and "100,000" in caught.value.message
    assert rich.render_tree("a" * rich.MAX_SOURCE, "story")["children"]


def test_a_tree_with_too_many_parts_is_refused():
    with pytest.raises(rich.RichError) as caught:
        rich.render_tree("*a* " * 9000, "story")
    assert caught.value.code == "too_complex"


def test_html_nested_too_deep_is_refused():
    with pytest.raises(rich.RichError) as caught:
        rich.render_tree("<blockquote>" * 40, "page")
    assert caught.value.code == "too_deep"
    assert rich.render_tree("<blockquote>" * 10 + "x", "page")


def test_deep_markdown_is_bounded_by_the_parser_and_still_a_valid_tree():
    assert_closed(rich.render_tree("> " * 200 + "x", "story"))
    assert_closed(rich.render_tree("- " * 200 + "x", "story"))


def test_an_unknown_profile_is_named():
    with pytest.raises(rich.RichError) as caught:
        rich.render_tree("x", "wiki")
    assert caught.value.code == "unknown_profile"


def test_stored_content_keeps_rendering_whatever_its_length():
    big = "word " * 60_000
    assert render_technical_description(big).startswith("<p>word")


# --- the preview endpoint ---------------------------------------------------------------


@pytest.fixture
def world(db):
    workspace = Workspace.objects.create(name="W", slug="w")
    other = Workspace.objects.create(name="O", slug="o")
    people = {}
    for name, role in (("org", Role.ORGANIZER), ("par", Role.PARTICIPANT), ("judge", Role.JUDGE)):
        user = User.objects.create_user(username=name, password="unused")
        Membership.objects.create(user=user, workspace=workspace, role=role)
        people[name] = user
    people["out"] = User.objects.create_user(username="out", password="unused")
    Membership.objects.create(user=people["out"], workspace=other, role=Role.ORGANIZER)
    clients = {}
    for name, user in people.items():
        client = Client()
        client.cookies["session"] = Session.issue(user).token
        clients[name] = client
    return {
        "url": f"/api/v1/workspaces/{workspace.public_id}/rich/preview/",
        "client": clients,
    }


def preview(world, who="par", **body):
    return world["client"][who].post(world["url"], data=body, content_type="application/json")


@pytest.mark.django_db
@pytest.mark.parametrize("who", ["org", "par", "judge"])
def test_every_workspace_member_can_preview(world, who):
    response = preview(world, who, profile="story", source="# Hi\n\n`x`")
    assert response.status_code == 200
    body = response.json()
    assert body["profile"] == "story" and body["length"] == 9 and body["max_length"] == 100000
    assert body["tree"]["children"][0] == {
        "type": "heading",
        "level": 2,
        "children": [{"type": "text", "text": "Hi"}],
    }


@pytest.mark.django_db
def test_a_preview_is_for_members_only(world):
    assert preview(world, "out", profile="story", source="x").status_code == 403
    anonymous = Client().post(
        world["url"], data={"profile": "story", "source": "x"}, content_type="application/json"
    )
    assert anonymous.status_code in (401, 403)


@pytest.mark.django_db
def test_a_preview_stores_and_audits_nothing(world):
    before = AuditEvent.objects.count()
    assert preview(world, profile="page", source="<p>x</p>").status_code == 200
    assert AuditEvent.objects.count() == before


@pytest.mark.django_db
def test_a_preview_is_the_same_every_time(world):
    first = preview(world, profile="story", source="*a*").json()
    assert preview(world, profile="story", source="*a*").json() == first


@pytest.mark.django_db
@pytest.mark.parametrize(
    "body, field",
    [
        ({"profile": "wiki", "source": "x"}, "profile"),
        ({"source": "x"}, "profile"),
        ({"profile": "story"}, "source"),
        ({"profile": "story", "source": 5}, "source"),
        ({"profile": "story", "source": "a" * 100_001}, "source"),
        ({"profile": "story", "source": "*a* " * 9000}, "source"),
    ],
)
def test_a_bad_preview_names_the_field(world, body, field):
    response = preview(world, **body)
    assert response.status_code == 400
    assert field in response.json() and response.json()[field][0]


@pytest.mark.django_db
def test_a_preview_of_hostile_text_is_a_closed_tree(world):
    for source in HOSTILE:
        assert_closed(preview(world, profile="story", source=source).json()["tree"])
        assert_closed(preview(world, profile="page", source=source).json()["tree"])


# --- an independent consumer, with no private coupling ----------------------------------


def test_a_consumer_outside_presentation_uses_only_the_public_functions():
    """A feature that wants to show a summary of its own text needs `core.rich` and nothing else."""

    def first_heading(source):
        tree = rich.render_tree(source, "story")
        return next(
            (
                "".join(t["text"] for t in walk(n) if t["type"] == "text")
                for n in tree["children"]
                if n["type"] == "heading"
            ),
            None,
        )

    assert first_heading("intro\n\n# Build notes\n\nbody") == "Build notes"
    assert first_heading("no heading") is None
