"""Serasa / bureau de credito adapter — consulta de score e restritivos.

- ``MockSerasaAdapter``: retorna dados ficticios para dev local.
- ``RealSerasaAdapter``: placeholder para integracao real.
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from src.adapters.base import AdapterResult

logger = logging.getLogger(__name__)


@runtime_checkable
class SerasaPort(Protocol):
    """Interface publica do adapter Serasa/bureau."""

    async def check_credit(self, cpf_cnpj: str) -> AdapterResult:
        """Consulta score de credito e restritivos."""
        ...


class MockSerasaAdapter:
    """Implementacao local com dados ficticios."""

    async def check_credit(self, cpf_cnpj: str) -> AdapterResult:
        logger.info("MockSerasa.check_credit cpf_cnpj=%s", cpf_cnpj[:6])
        return AdapterResult(
            success=True,
            source="mock",
            data={
                "cpf_cnpj": cpf_cnpj,
                "score": 720,
                "score_range": "bom",
                "pendencies": 0,
                "protests": 0,
                "bounced_checks": 0,
                "last_query_date": "2024-11-20",
            },
        )


class RealSerasaAdapter:
    """Placeholder — requer credenciais Serasa."""

    def __init__(self, api_key: str, base_url: str = "https://api.serasaexperian.com.br") -> None:
        self._api_key = api_key
        self._base_url = base_url

    async def check_credit(self, cpf_cnpj: str) -> AdapterResult:
        raise NotImplementedError("RealSerasaAdapter nao implementado — aguardando contrato/API key.")


def create_serasa_adapter(
    backend: str = "mock",
    api_key: str | None = None,
) -> SerasaPort:
    if backend == "real":
        if not api_key:
            raise ValueError("SERASA_API_KEY obrigatoria para backend=real")
        return RealSerasaAdapter(api_key=api_key)
    return MockSerasaAdapter()
