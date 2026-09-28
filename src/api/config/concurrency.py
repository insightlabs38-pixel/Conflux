import asyncio

UNBOUNDED_PATHS = frozenset({"/api/v1/health/"})


class BoundedInflight:
    """Caps concurrently executing HTTP requests per worker process.

    Django runs each in-flight sync view on its own thread with its own database
    connection (CONN_MAX_AGE=0), so unbounded concurrency turns a request burst into
    a burst of PostgreSQL connections until the server refuses them. Excess requests
    wait here instead of failing; health checks bypass the queue so an overloaded
    but working worker is never restarted for being busy.
    """

    def __init__(self, app, limit):
        self.app = app
        self.limit = limit
        self._semaphore = None

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") in UNBOUNDED_PATHS or self.limit <= 0:
            return await self.app(scope, receive, send)
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.limit)
        async with self._semaphore:
            await self.app(scope, receive, send)
