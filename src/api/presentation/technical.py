"""Render participant-authored project descriptions for the public site.

The `story` profile of the shared rich-content primitive (`core.rich`) does the work; this name
stays for the pages and tests that import it.
"""

from core.rich import render_html


def render_technical_description(value: str) -> str:
    return render_html(value, "story")
