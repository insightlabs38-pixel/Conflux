import io
import json
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sdks/python"))

from conflux_sdk import ApiError, ConfluxClient  # noqa: E402
from conflux_sdk.generated import OPERATIONS  # noqa: E402

from scripts.generate_sdks import ts_type  # noqa: E402


class Response:
    def __init__(self, status, body=b""):
        self.status = status
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return self.body


def test_generated_catalog_matches_checked_openapi():
    subprocess.run([sys.executable, "scripts/generate_sdks.py", "--check"], cwd=ROOT, check=True)
    assert "get_api_v1_accounts_me" in OPERATIONS
    assert "post_api_v1_accounts_logout" in OPERATIONS


def test_generator_rejects_schema_shapes_it_cannot_type():
    with pytest.raises(ValueError, match="Unsupported union"):
        ts_type({"oneOf": [{"type": "string"}, {"type": "integer"}]})


def test_python_client_encodes_path_auth_query_and_body():
    seen = []

    def opener(request):
        seen.append(request)
        return Response(200, b'{"ok":true}')

    client = ConfluxClient("https://example.test", bearer_token="secret", opener=opener)
    result = client.call(
        "get_api_v1_audit_workspace_public_id",
        path={"workspace_public_id": "a/b"},
    )
    assert result == {"ok": True}
    assert seen[0].full_url.endswith("/api/v1/audit/a%2Fb/")
    assert seen[0].get_header("Authorization") == "Bearer secret"

    client.call("get_api_v1_schema", query={"format": "yaml"})
    assert seen[1].full_url.endswith("/api/v1/schema/?format=yaml")

    client.call("post_api_v1_accounts_login", body={"username": "user", "password": "pass"})
    assert json.loads(seen[2].data) == {"username": "user", "password": "pass"}
    assert seen[2].get_header("Content-type") == "application/json"
    with pytest.raises(ValueError, match="Unknown query"):
        client.call("get_api_v1_accounts_me", query={"surprise": True})


def test_python_client_returns_none_for_204_and_preserves_http_error():
    client = ConfluxClient(
        "https://example.test", session_token="cookie", opener=lambda _: Response(204)
    )
    assert client.call("post_api_v1_accounts_logout") is None

    def reject(request):
        assert request.get_header("Cookie") == "session=cookie"
        raise HTTPError(request.full_url, 403, "Forbidden", {}, io.BytesIO(b'{"detail":"denied"}'))

    client.opener = reject
    with pytest.raises(ApiError) as error:
        client.call("get_api_v1_accounts_me")
    assert error.value.status == 403
    assert error.value.body == {"detail": "denied"}
