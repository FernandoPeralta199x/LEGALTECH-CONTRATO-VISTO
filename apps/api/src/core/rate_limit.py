from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Protocol

from fastapi import HTTPException, Request, status

from src.core.config import get_settings


class RateLimitStore(Protocol):
    def hit(self, key: str, window_seconds: int) -> tuple[int, int]:
        """Registra um hit e retorna (contagem_na_janela, segundos_para_reset)."""
        ...


class InMemoryRateLimitStore:
    """Contador de janela fixa, em memoria. Apenas single-process.

    Para multi-instancia (ECS/Fargate) trocar por um store compartilhado
    (Redis/ElastiCache) que implemente o mesmo protocolo `RateLimitStore`.
    """

    def __init__(self, *, time_func: Callable[[], float] = time.time) -> None:
        self._time = time_func
        self._data: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str, window_seconds: int) -> tuple[int, int]:
        now = self._time()
        with self._lock:
            entry = self._data.get(key)
            if entry is None or now >= entry[0] + window_seconds:
                self._data[key] = [now, 1]
                return 1, window_seconds
            entry[1] += 1
            reset_in = int(entry[0] + window_seconds - now)
            return int(entry[1]), max(reset_in, 1)


class RateLimiter:
    def __init__(self, store: RateLimitStore) -> None:
        self._store = store

    def check(self, key: str, *, limit: int, window_seconds: int) -> None:
        count, reset_in = self._store.hit(key, window_seconds)
        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Try again later.",
                headers={"Retry-After": str(reset_in)},
            )


# Escopo -> (limite, janela_em_segundos). Defaults alinhados a OWASP
# (restritivo-mas-usavel) para o brute-force dos endpoints de auth.
RATE_LIMITS: dict[str, tuple[int, int]] = {
    "auth_login": (5, 60),
    "auth_register": (3, 60),
    "auth_verify": (5, 60),
}

_default_limiter = RateLimiter(InMemoryRateLimitStore())


def get_rate_limiter() -> RateLimiter:
    return _default_limiter


def rate_limit(scope: str) -> Callable:
    """Dependencia FastAPI que aplica rate limit por IP para um escopo.

    NOTA: atras de ALB/CloudFront o IP real vem em X-Forwarded-For; nao confiar
    nesse header sem proxy confiavel. Por ora usa request.client.host.
    """
    limit, window = RATE_LIMITS[scope]

    async def _dependency(request: Request) -> None:
        if not get_settings().rate_limit_enabled:
            return
        client = request.client.host if request.client else "unknown"
        get_rate_limiter().check(f"{scope}:{client}", limit=limit, window_seconds=window)

    return _dependency
