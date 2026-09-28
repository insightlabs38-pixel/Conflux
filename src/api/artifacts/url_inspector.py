"""Static facts about a submitted demo/repository link (PVS08). The fetch is
public-HTTPS-only with the resolved address pinned (the same guard webhooks and
submission CI use), never follows a redirect it has not re-validated, and never
executes or renders anything it receives.
"""

import html
import http.client
import ipaddress
import re
import socket
from urllib.parse import urljoin, urlsplit

from integrations.webhooks import validate_destination

MAX_REDIRECTS = 3
BODY_BYTES = 8192
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "cutt.ly", "rebrand.ly"}
TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)


def pinned_fetch(host, address, path, *, timeout=5.0):
    connection = http.client.HTTPSConnection(host, 443, timeout=timeout)
    connection._create_connection = (
        lambda _address, connect_timeout, source_address: socket.create_connection(
            (address, 443), connect_timeout, source_address
        )
    )
    try:
        connection.request(
            "GET", path, headers={"User-Agent": "conflux-artifact-inspector", "Accept": "*/*"}
        )
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read(BODY_BYTES)
    finally:
        connection.close()


def _link_flags(url):
    host = (urlsplit(url).hostname or "").lower()
    flags = []
    try:
        ipaddress.ip_address(host)
        flags.append(("warning", "ip_literal", "The link uses a raw IP address."))
    except ValueError:
        pass
    if "xn--" in host:
        flags.append(
            (
                "warning",
                "punycode",
                "The host uses internationalized characters that can imitate another site.",
            )
        )
    if host in SHORTENERS:
        flags.append(
            ("warning", "url_shortener", "The link is a URL shortener; the destination is hidden.")
        )
    return flags


def inspect_url(url, report, *, fetcher=pinned_fetch, validator=validate_destination):
    report.detected_type = "link"
    for severity, code, detail in _link_flags(url):
        report.add(severity, code, detail)
    chain, current = [], url
    status = headers = body = None
    for _ in range(MAX_REDIRECTS + 1):
        try:
            parts, address = validator(current)
        except ValueError as exc:
            report.add("blocked", "unsafe_destination", str(exc))
            break
        chain.append(parts.hostname)
        try:
            status, headers, body = fetcher(
                parts.hostname,
                address,
                (parts.path or "/") + (f"?{parts.query}" if parts.query else ""),
            )
        except (OSError, http.client.HTTPException, TimeoutError):
            report.add("warning", "unreachable", "The link could not be fetched.")
            break
        headers = {k.lower(): v for k, v in headers.items()}
        if status in (301, 302, 303, 307, 308) and headers.get("location"):
            current = urljoin(current, headers["location"])
            continue
        break
    else:
        report.add("warning", "redirect_loop", f"More than {MAX_REDIRECTS} redirects.")
    report.facts["redirect_chain"] = chain
    if len(set(chain)) > 1:
        report.add("warning", "cross_domain_redirect", "The link redirects to a different domain.")
    if status is None or headers is None:
        return
    report.facts["status"] = status
    if status >= 400:
        report.add("warning", "http_error", f"The link answered with HTTP {status}.")
    content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
    report.facts["content_type"] = content_type
    disposition = headers.get("content-disposition", "").lower()
    if "attachment" in disposition or content_type in (
        "application/octet-stream",
        "application/x-msdownload",
        "application/zip",
        "application/x-apple-diskimage",
    ):
        report.add(
            "warning", "forces_download", "The link downloads a file instead of showing a page."
        )
    report.facts["embeddable"] = not (
        "x-frame-options" in headers
        or "frame-ancestors" in headers.get("content-security-policy", "")
    )
    report.facts["server"] = html.escape(headers.get("server", ""))[:80]
    if content_type.startswith("text/html") and body:
        match = TITLE.search(body.decode("utf-8", "replace"))
        if match:
            title = " ".join(html.unescape(match.group(1)).split())
            report.facts["title"] = "".join(c for c in title if c.isprintable())[:200]
