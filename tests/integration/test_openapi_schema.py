import re

import yaml
from django.test import Client
from django.urls import URLPattern, URLResolver, get_resolver


def _api_paths(patterns, prefix=""):
    for entry in patterns:
        route = prefix + str(entry.pattern)
        if isinstance(entry, URLResolver):
            yield from _api_paths(entry.url_patterns, route)
        elif isinstance(entry, URLPattern) and route.startswith("api/v1/"):
            yield "/" + re.sub(r"<[^:>]+:([^>]+)>", r"{\1}", route)


def test_live_schema_contains_workspace_routes_and_auth_schemes():
    response = Client().get("/api/v1/schema/")
    assert response.status_code == 200
    schema = yaml.safe_load(response.content)
    assert schema["openapi"].startswith("3.")
    assert "/api/v1/workspaces/{workspace_public_id}/events/" in schema["paths"]
    assert "/api/v1/workspaces/{workspace_public_id}/api-credentials/" in schema["paths"]
    schemes = schema["components"]["securitySchemes"]
    assert schemes["sessionCookie"]["in"] == "cookie"
    assert schemes["scopedBearer"]["scheme"] == "bearer"
    assert set(schema["paths"]) == set(_api_paths(get_resolver().url_patterns))
    operation_ids = [
        operation["operationId"]
        for methods in schema["paths"].values()
        for operation in methods.values()
    ]
    assert len(operation_ids) == len(set(operation_ids))
