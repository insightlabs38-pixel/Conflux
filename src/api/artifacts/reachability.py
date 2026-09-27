"""Advanced submission CI (S07): real, explicitly-triggered reachability,
commit-capture and license evidence for `repository`/`live_url` artifacts.

Deliberately never wired into the synchronous `validators.inspect_artifact`
path -- that check runs inline during ordinary artifact create/update
requests and is intentionally network-free (see
tests/integration/test_artifact_validation.py::
test_external_links_are_ready_with_explicit_warning_without_network_fetch).
This module is only reached via an organizer/owner-triggered action (see
views.ArtifactEvidenceCheckView), the same "explicit action, not inline"
shape webhooks.py uses for its own outbound calls.

Reuses integrations.webhooks.validate_destination for the actual SSRF
guard (public-HTTPS-only, DNS-resolved-and-pinned) rather than
reimplementing it -- one reviewed guard for every project-initiated
outbound request, not two subtly different ones.
"""

import http.client
import json
import re
import socket
from urllib.parse import quote

GITHUB_REPO_PATH = re.compile(r"^/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?/?$")
# S23: same simple owner/repo shape github.com uses. GitLab also allows
# nested subgroups (group/subgroup/project); those fall outside this
# pattern and simply get no evidence, the same "best-effort, never
# guessed" degrade as a private or rate-limited repository below.
GITLAB_REPO_PATH = re.compile(r"^/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?/?$")


def pinned_get(host: str, address: str, path: str, *, timeout: float = 5.0) -> int:
    """GET a URL that the caller has already resolved and validated (see
    integrations.webhooks.validate_destination/send_delivery, whose
    connection-pinning this mirrors exactly): TLS/Host stay the real
    hostname so SNI and certificate validation are correct, but the TCP
    socket is forced onto the pre-validated public IP so a DNS answer that
    changes between validation and connection can never redirect the
    request onto a private address.
    """
    connection = http.client.HTTPSConnection(host, 443, timeout=timeout)
    connection._create_connection = (
        lambda _address, connect_timeout, source_address: socket.create_connection(
            (address, 443), connect_timeout, source_address
        )
    )
    try:
        connection.request(
            "GET", path, headers={"User-Agent": "conflux-submission-ci", "Accept": "*/*"}
        )
        response = connection.getresponse()
        response.read(65536)
        return response.status
    finally:
        connection.close()


def _github_get_json(path: str) -> dict | None:
    """A plain HTTPS GET to the fixed `api.github.com` host -- not the SSRF
    guard above, because that host is never attacker-controlled (a
    submitted repository URL is only ever parsed for owner/repo here, this
    function never receives it directly).
    """
    connection = http.client.HTTPSConnection("api.github.com", 443, timeout=5)
    try:
        connection.request(
            "GET",
            path,
            headers={
                "User-Agent": "conflux-submission-ci",
                "Accept": "application/vnd.github+json",
            },
        )
        response = connection.getresponse()
        body = response.read(65536)
        if response.status != 200:
            return None
        return json.loads(body)
    except (OSError, TimeoutError, http.client.HTTPException, ValueError):
        return None
    finally:
        connection.close()


def github_evidence(owner: str, repo: str) -> str:
    """Best-effort license + latest-commit evidence for a public GitHub
    repository. Never raises: a GitHub API miss (rate limit, private repo,
    renamed repo) is reported as missing evidence, not silently guessed at
    or treated as a reachability failure -- the repository URL itself may
    still be perfectly reachable.
    """
    info = _github_get_json(f"/repos/{owner}/{repo}")
    if info is None:
        return "GitHub metadata unavailable (rate-limited, private, or not found)."
    branch = info.get("default_branch") or "HEAD"
    license_id = (info.get("license") or {}).get("spdx_id") or "none detected"
    commit = _github_get_json(f"/repos/{owner}/{repo}/commits/{branch}")
    sha = (commit or {}).get("sha") or ""
    commit_note = (
        f"HEAD commit {sha[:12]} on {branch}" if sha else f"commit unavailable on {branch}"
    )
    return f"license: {license_id}; {commit_note}."


def _gitlab_get_json(path: str) -> dict | None:
    """A plain HTTPS GET to the fixed `gitlab.com` host -- same fixed-host
    reasoning as `_github_get_json` above.
    """
    connection = http.client.HTTPSConnection("gitlab.com", 443, timeout=5)
    try:
        connection.request(
            "GET",
            path,
            headers={"User-Agent": "conflux-submission-ci", "Accept": "application/json"},
        )
        response = connection.getresponse()
        body = response.read(65536)
        if response.status != 200:
            return None
        return json.loads(body)
    except (OSError, TimeoutError, http.client.HTTPException, ValueError):
        return None
    finally:
        connection.close()


def gitlab_evidence(owner: str, repo: str) -> str:
    """Best-effort license + latest-commit evidence for a public GitLab
    project, mirroring `github_evidence` exactly. Never raises.
    """
    project_id = quote(f"{owner}/{repo}", safe="")
    info = _gitlab_get_json(f"/api/v4/projects/{project_id}?license=true")
    if info is None:
        return "GitLab metadata unavailable (rate-limited, private, or not found)."
    branch = info.get("default_branch") or "HEAD"
    license_id = (info.get("license") or {}).get("key") or "none detected"
    commit = _gitlab_get_json(f"/api/v4/projects/{project_id}/repository/commits/{branch}")
    sha = (commit or {}).get("id") or ""
    commit_note = (
        f"HEAD commit {sha[:12]} on {branch}" if sha else f"commit unavailable on {branch}"
    )
    return f"license: {license_id}; {commit_note}."
