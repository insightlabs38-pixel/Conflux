import socket

from artifacts.reachability import GITHUB_REPO_PATH, github_evidence, pinned_get


class FakeResponse:
    def __init__(self, status, body=b""):
        self.status = status
        self._body = body

    def read(self, _limit):
        return self._body


def test_pinned_get_connects_to_the_resolved_address_not_a_fresh_dns_lookup(monkeypatch):
    captured = []

    class Connection:
        def __init__(self, host, port, timeout):
            captured.append(("init", host, port, timeout))

        def request(self, method, target, headers):
            self._create_connection(("attacker.example", 443), 5, None)
            captured.append(("request", method, target, headers))

        def getresponse(self):
            return FakeResponse(200)

        def close(self):
            pass

    monkeypatch.setattr("artifacts.reachability.http.client.HTTPSConnection", Connection)
    monkeypatch.setattr(
        socket, "create_connection", lambda address, timeout, source: captured.append(address)
    )
    status = pinned_get("target.example", "203.0.113.9", "/repo")
    assert status == 200
    # The pinned connection call used the pre-resolved address, not a
    # fresh lookup of the hostname (which an attacker-controlled DNS
    # rebind could have pointed somewhere private by the time it connects).
    assert ("203.0.113.9", 443) in captured


def test_github_evidence_reports_license_and_commit_on_success(monkeypatch):
    calls = {"count": 0}

    def fake_get_json(path):
        calls["count"] += 1
        if path == "/repos/octo/demo":
            return {"default_branch": "main", "license": {"spdx_id": "MIT"}}
        if path == "/repos/octo/demo/commits/main":
            return {"sha": "abcdef0123456789"}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr("artifacts.reachability._github_get_json", fake_get_json)
    result = github_evidence("octo", "demo")
    assert "license: MIT" in result
    assert "abcdef012345" in result
    assert calls["count"] == 2


def test_github_evidence_degrades_honestly_when_the_api_is_unavailable(monkeypatch):
    monkeypatch.setattr("artifacts.reachability._github_get_json", lambda path: None)
    result = github_evidence("octo", "demo")
    assert "unavailable" in result


def test_github_repo_path_pattern_extracts_owner_and_repo():
    match = GITHUB_REPO_PATH.match("/octo/demo.git")
    assert match["owner"] == "octo"
    assert match["repo"] == "demo"
    assert GITHUB_REPO_PATH.match("/octo") is None
