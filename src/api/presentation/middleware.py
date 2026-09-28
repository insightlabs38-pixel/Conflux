from django.utils.cache import add_never_cache_headers


class PublicationCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            request.path.startswith("/e/")
            and request.path != "/e/sw.js"
            or request.path.startswith("/api/v1/events/")
            or "/feedback/" in request.path
        ):
            add_never_cache_headers(response)
        return response
