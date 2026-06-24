import unittest

from fastapi import HTTPException

from src.core.rate_limit import InMemoryRateLimitStore, RateLimiter


class _Clock:
    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


class RateLimiterTest(unittest.TestCase):
    def _limiter(self, clock: _Clock) -> RateLimiter:
        return RateLimiter(InMemoryRateLimitStore(time_func=clock))

    def test_allows_requests_up_to_limit(self) -> None:
        limiter = self._limiter(_Clock())
        for _ in range(5):
            limiter.check("auth_login:1.2.3.4", limit=5, window_seconds=60)

    def test_blocks_over_limit_with_429_and_retry_after(self) -> None:
        limiter = self._limiter(_Clock())
        for _ in range(5):
            limiter.check("k", limit=5, window_seconds=60)
        with self.assertRaises(HTTPException) as ctx:
            limiter.check("k", limit=5, window_seconds=60)
        self.assertEqual(429, ctx.exception.status_code)
        self.assertIn("Retry-After", ctx.exception.headers)

    def test_window_resets_after_expiry(self) -> None:
        clock = _Clock()
        limiter = self._limiter(clock)
        for _ in range(5):
            limiter.check("k", limit=5, window_seconds=60)
        clock.advance(61)
        limiter.check("k", limit=5, window_seconds=60)  # nova janela, permitido

    def test_keys_are_isolated_per_client(self) -> None:
        limiter = self._limiter(_Clock())
        for _ in range(5):
            limiter.check("ip-A", limit=5, window_seconds=60)
        limiter.check("ip-B", limit=5, window_seconds=60)  # outro IP, independente


if __name__ == "__main__":
    unittest.main()


class RateLimitDependencyTest(unittest.TestCase):
    def test_dependency_blocks_same_ip_after_limit(self) -> None:
        import asyncio
        from types import SimpleNamespace

        from src.core.rate_limit import RATE_LIMITS, rate_limit

        dependency = rate_limit("auth_login")
        request = SimpleNamespace(client=SimpleNamespace(host="203.0.113.77"))
        limit = RATE_LIMITS["auth_login"][0]

        async def run() -> None:
            for _ in range(limit):
                await dependency(request)
            with self.assertRaises(HTTPException) as ctx:
                await dependency(request)
            self.assertEqual(429, ctx.exception.status_code)

        asyncio.run(run())
