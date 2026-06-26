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
        client = client_ip_from_request(
            request, trust_proxy=get_settings().trusted_proxy_enabled
        )
        get_rate_limiter().check(f"{scope}:{client}", limit=limit, window_seconds=window)

    return _dependency


def client_ip_from_request(request, *, trust_proxy: bool) -> str:
    """Resolve o IP do cliente.

    So confia no X-Forwarded-For quando trust_proxy=True (atras de proxy
    confiavel: ALB/CloudFront). Caso contrario usa request.client.host, pois
    um cliente direto pode forjar o header e burlar o rate-limit por IP.
    """
    if trust_proxy:
        headers = getattr(request, "headers", None)
        xff = headers.get("x-forwarded-for") if headers is not None else None
        if xff:
            return xff.split(",")[0].strip()
    client = getattr(request, "client", None)
    host = getattr(client, "host", None) if client is not None else None
    return host or "unknown"


class AccountLockoutStore(Protocol):
    def record_failure(self, key: str, window_seconds: int) -> int: ...
    def failures(self, key: str, window_seconds: int) -> int: ...
    def reset(self, key: str) -> None: ...


class InMemoryAccountLockoutStore:
    """Contador de falhas por conta, janela fixa, em memoria (single-process).

    Multi-instancia (ECS/Fargate): trocar por store compartilhado (Redis)
    que implemente o mesmo protocolo `AccountLockoutStore`.
    """

    def __init__(self, *, time_func: Callable[[], float] = time.time) -> None:
        self._time = time_func
        self._data: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _active(self, key: str, window_seconds: int):
        entry = self._data.get(key)
        if entry is None or self._time() >= entry[0] + window_seconds:
            return None
        return entry

    def failures(self, key: str, window_seconds: int) -> int:
        with self._lock:
            entry = self._active(key, window_seconds)
            return int(entry[1]) if entry else 0

    def record_failure(self, key: str, window_seconds: int) -> int:
        with self._lock:
            entry = self._active(key, window_seconds)
            if entry is None:
                self._data[key] = [self._time(), 1]
                return 1
            entry[1] += 1
            return int(entry[1])

    def reset(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)


class AccountLockout:
    """Soft-lockout por conta: trava apos `max_failures` falhas na janela.

    Conta apenas falhas; `reset` no login bem-sucedido. Nao bloqueia
    permanentemente (a janela expira), evitando DoS de lockout do legitimo.
    """

    def __init__(
        self, store: AccountLockoutStore, *, max_failures: int, window_seconds: int
    ) -> None:
        self._store = store
        self._max = max_failures
        self._window = window_seconds

    def is_locked(self, key: str) -> bool:
        return self._store.failures(key, self._window) >= self._max

    def register_failure(self, key: str) -> int:
        return self._store.record_failure(key, self._window)

    def reset(self, key: str) -> None:
        self._store.reset(key)


_default_account_lockout: AccountLockout | None = None


def get_account_lockout() -> AccountLockout:
    global _default_account_lockout
    if _default_account_lockout is None:
        settings = get_settings()
        _default_account_lockout = AccountLockout(
            InMemoryAccountLockoutStore(),
            max_failures=settings.auth_lockout_max_failures,
            window_seconds=settings.auth_lockout_window_seconds,
        )
    return _default_account_lockout
