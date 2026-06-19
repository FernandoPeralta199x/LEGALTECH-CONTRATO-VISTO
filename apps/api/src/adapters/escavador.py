"""Escavador API adapter — consulta de processos judiciais.

- ``MockEscavadorAdapter``: retorna dados ficticios para dev local.
- ``RealEscavadorAdapter``: placeholder para integracao real (requer API key).
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from src.adapters.base import AdapterResult

logger = logging.getLogger(__name__)


@runtime_checkable
class EscavadorPort(Protocol):
    """Interface publica do adapter Escavador."""

    async def search_lawsuits(self, cpf_cnpj: str) -> AdapterResult:
        """Busca processos judiciais por CPF/CNPJ."""
        ...

    async def get_lawsuit_details(self, lawsuit_id: str) -> AdapterResult:
        """Retorna detalhes de um processo especifico."""
        ...


class MockEscavadorAdapter:
    """Implementacao local com dados ficticios."""

    async def search_lawsuits(self, cpf_cnpj: str) -> AdapterResult:
        logger.info("MockEscavador.search_lawsuits cpf_cnpj=%s", cpf_cnpj[:6])
        return AdapterResult(
            success=True,
            source="mock",
            data={
                "cpf_cnpj": cpf_cnpj,
                "total": 2,
                "lawsuits": [
                    {
                        "id": "mock-proc-001",
                        "number": "0001234-56.2024.8.26.0100",
                        "court": "TJSP",
                        "subject": "Cobranca",
                        "status": "Em andamento",
                        "parties": ["Parte A", "Parte B"],
                    },
                    {
                        "id": "mock-proc-002",
                        "number": "0009876-54.2023.8.19.0001",
                        "court": "TJRJ",
                        "subject": "Indenizacao",
                        "status": "Arquivado",
                        "parties": ["Parte C"],
                    },
                ],
            },
        )

    async def get_lawsuit_details(self, lawsuit_id: str) -> AdapterResult:
        logger.info("MockEscavador.get_lawsuit_details id=%s", lawsuit_id)
        return AdapterResult(
            success=True,
            source="mock",
            data={
                "id": lawsuit_id,
                "number": "0001234-56.2024.8.26.0100",
                "court": "TJSP",
                "subject": "Cobranca",
                "status": "Em andamento",
                "movements": [
                    {"date": "2024-06-01", "description": "Distribuicao"},
                    {"date": "2024-07-15", "description": "Citacao"},
                ],
            },
        )


class RealEscavadorAdapter:
    """Placeholder — requer API key em ESCAVADOR_API_KEY."""

    def __init__(self, api_key: str, base_url: str = "https://api.escavador.com") -> None:
        self._api_key = api_key
        self._base_url = base_url

    async def search_lawsuits(self, cpf_cnpj: str) -> AdapterResult:
        raise NotImplementedError("RealEscavadorAdapter nao implementado — aguardando contrato/API key.")

    async def get_lawsuit_details(self, lawsuit_id: str) -> AdapterResult:
        raise NotImplementedError("RealEscavadorAdapter nao implementado — aguardando contrato/API key.")


def create_escavador_adapter(
    backend: str = "mock",
    api_key: str | None = None,
) -> EscavadorPort:
    if backend == "real":
        if not api_key:
            raise ValueError("ESCAVADOR_API_KEY obrigatoria para backend=real")
        return RealEscavadorAdapter(api_key=api_key)
    return MockEscavadorAdapter()
