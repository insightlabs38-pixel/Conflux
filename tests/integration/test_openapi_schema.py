import yaml
from django.test import Client


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
