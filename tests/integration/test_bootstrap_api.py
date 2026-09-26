from django.test import Client


def test_health_endpoint_is_versioned_and_get_only():
    client = Client()
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert client.post("/api/v1/health/").status_code == 405


def test_unimplemented_product_route_is_not_advertised():
    assert Client().get("/api/v1/events/").status_code == 404
