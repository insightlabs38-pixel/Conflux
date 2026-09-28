import asyncio

from config.concurrency import BoundedInflight


def run_burst(limit, paths):
    active = peak = 0

    async def app(scope, receive, send):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1

    wrapped = BoundedInflight(app, limit)

    async def main():
        await asyncio.gather(*(wrapped({"type": "http", "path": p}, None, None) for p in paths))

    asyncio.run(main())
    return peak


def test_burst_never_exceeds_the_limit_and_every_request_still_runs():
    assert run_burst(3, ["/api/v1/x/"] * 40) == 3


def test_health_checks_bypass_the_queue():
    assert run_burst(1, ["/api/v1/health/"] * 10) == 10


def test_non_http_scopes_and_disabled_limit_pass_through():
    calls = []

    async def app(scope, receive, send):
        calls.append(scope["type"])

    asyncio.run(BoundedInflight(app, 1)({"type": "lifespan"}, None, None))
    asyncio.run(BoundedInflight(app, 0)({"type": "http", "path": "/x/"}, None, None))
    assert calls == ["lifespan", "http"]
