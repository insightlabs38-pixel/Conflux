from django.urls import URLPattern, URLResolver, get_resolver


def _routes(patterns, prefix=""):
    for entry in patterns:
        route = prefix + str(entry.pattern)
        if isinstance(entry, URLResolver):
            yield from _routes(entry.url_patterns, route)
        elif isinstance(entry, URLPattern):
            yield route, entry


def test_application_routes_are_versioned_and_have_stable_names():
    routes = list(_routes(get_resolver().url_patterns))
    api_routes = [(route, entry) for route, entry in routes if route.startswith("api/")]
    assert api_routes
    assert all(route.startswith("api/v1/") for route, _ in api_routes)
    assert all(route.endswith(("/", ".csv")) for route, _ in api_routes)
    assert all(entry.name for _, entry in api_routes)
    assert len({entry.name for _, entry in api_routes}) == len(api_routes)
