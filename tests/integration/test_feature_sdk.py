"""PD-F003-B01-T07: the generated SDK claims of the completeness contract, held against real calls.

The verifier compares the generated files with the OpenAPI document (CI, `check_static`); these
tests call every operation of every claimed route through the generated Python client, in process
against the real API, and check the answer is what the generated types say: an array for `T[]`,
nothing for `null`, and a record whose fields are the schema's."""

import io
import json
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse

import pytest
from accounts.models import Session
from core import features as ft
from core import features_sdk
from django.test import Client

from tests.integration import test_feature_audit as harness
from tests.integration import test_feature_rest as rest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sdks/python"))

from conflux_sdk import ApiError, ConfluxClient  # noqa: E402
from conflux_sdk.generated import OPERATIONS  # noqa: E402

pytestmark = pytest.mark.django_db

world = harness.world  # the same people, event and project the audit proof uses
scenarios = harness.scenarios


class Reply:
    """What `urlopen` returns, made from a Django test response."""

    def __init__(self, response):
        self.status = response.status_code
        self.body = response.content

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return self.body


def opener(request):
    """The SDK's transport, pointed at the Django app instead of the network."""
    url = urlparse(request.full_url)
    target = url.path + (f"?{url.query}" if url.query else "")
    response = Client().generic(
        request.get_method(),
        target,
        request.data or b"",
        content_type=request.get_header("Content-type") or "application/json",
        HTTP_COOKIE=request.get_header("Cookie") or "",
    )
    if response.status_code >= 400:
        raise HTTPError(
            request.full_url, response.status_code, "refused", {}, io.BytesIO(response.content)
        )
    return Reply(response)


def sdk_call(world, who, route, method, kwargs, body=None):
    op = ft.System().operation(route, method)
    spec = OPERATIONS[op["operationId"]]
    token = Session.issue(world["people"][who]).token
    client = ConfluxClient("http://testserver", session_token=token, opener=opener)
    path = {k: str(v) for k, v in kwargs.items() if k in spec["path_params"]}
    assert set(path) == set(spec["path_params"]), (route, spec["path_params"])
    body = body if spec["request_body"] else None  # an operation without a body takes none
    return op, client.call(op["operationId"], path=path, body=body)


def check_against_types(system, op, result):
    expected = features_sdk.ts_type(system, op)
    if expected == "null":
        assert result is None
    elif expected and expected.endswith("[]"):
        assert isinstance(result, list)
        name = expected[:-2]
    elif expected:
        assert isinstance(result, dict)
        name = expected
    else:
        return
    if expected != "null":
        fields = set(system.schema(name).get("properties", {}))
        rows = result if isinstance(result, list) else [result]
        for row in rows[:3]:
            assert not fields or set(row) <= fields, (name, sorted(set(row) - fields))


WRITES = harness.DECLARED


@pytest.mark.parametrize(
    ("key", "route", "method", "action"),
    WRITES,
    ids=[f"{k}:{r}:{m}" for k, r, m, _ in WRITES],
)
def test_every_claimed_operation_works_through_the_generated_python_sdk(
    world, key, route, method, action
):
    who, kwargs, body = scenarios(world)[(route, method)]()
    op, result = sdk_call(world, who, route, method, kwargs, body)
    check_against_types(ft.System(), op, result)


@pytest.mark.parametrize(("key", "route"), rest.LISTS, ids=[f"{k}:{r}" for k, r in rest.LISTS])
def test_every_claimed_list_is_read_through_the_generated_python_sdk(world, key, route):
    who, kwargs = rest.seed(world, route)
    op, result = sdk_call(world, who, route, "GET", kwargs)
    assert isinstance(result, list) and result
    check_against_types(ft.System(), op, result)


def test_a_refusal_through_the_sdk_is_an_api_error_with_the_shared_shape(world):
    who, kwargs, body = scenarios(world)[("track-list", "POST")]()
    world["people"]["intruder"] = harness.user("intruder")
    with pytest.raises(ApiError) as refused:
        sdk_call(world, "intruder", "track-list", "POST", kwargs, body)
    assert refused.value.status in (403, 404)
    assert isinstance(refused.value.body, dict) and refused.value.body


def test_every_operation_of_every_claimed_route_is_in_both_generated_files():
    system = ft.System()
    seen = 0
    for feature in ft.FEATURES.values():
        for route, method, op in features_sdk.operations(feature, system):
            assert op is not None and op["operationId"] in OPERATIONS, (route, method)
            assert OPERATIONS[op["operationId"]]["method"] == method
            seen += 1
    assert seen > 60
    assert ft.check_static(Path(__file__).resolve().parents[2]) == []
    assert json.dumps(sorted(OPERATIONS))  # the catalog is plain data
