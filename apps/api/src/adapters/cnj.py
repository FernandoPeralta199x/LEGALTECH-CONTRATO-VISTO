"""CNJ / Tribunal API adapter — consulta processual direta.

- ``MockCNJAdapter``: retorna dados ficticios para dev local.
- ``RealCNJAdapter``: placeholder para integracao com DataJud / APIs dos tribunais.
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from src.adapters.base import AdapterResult

logger = logging.getLogger(__name__)


@runtime_checkable
class CNJPort(Protocol):
    """Interface publica do adapter CNJ/Tribunal."""

    async def search_by_number(self, process_number: str) -> AdapterResult:
        """Consulta processo por numero unificado."""
        ...

    async def search_by_party(self, name: str, document: str | None = None) -> AdapterResult:
        """Consulta processos por nome/documento de parte."""
        ...


class MockCNJAdapter:
    """Implementacao local com dados ficticios."""

    async def search_by_number(self, process_number: str) -> AdapterResult:
        logger.info("MockCNJ.search_by_number number=%s", process_number)
        return AdapterResult(
            success=True,
            source="mock",
            data={
                "process_number": process_number,
                "court": "TJSP",
                "class": "Procedimento Comum Civel",
                "subject": "Contratos Bancarios",
                "judge": "Juiz Mock da Silva",
                "filing_date": "2024-03-15",
                "status": "Em andamento",
                "last_movement": {
                    "date": "2024-12-01",
                    "description": "Conclusos para despacho",
                },
            },
        )

    async def search_by_party(self, name: str, document: str | None = None) -> AdapterResult:
        logger.info("MockCNJ.search_by_party name=%s", name[:10])
        return AdapterResult(
            success=True,
            source="mock",
            data={
                "name": name,
                "total": 1,
                "processes": [
                    {
                        "number": "0005555-12.2024.8.26.0100",
                        "court": "TJSP",
                        "role": "Autor",
                        "status": "Ativo",
                    },
                ],
            },
        )


class RealCNJAdapter:
    """Placeholder — requer acesso ao DataJud ou API de tribunal."""

    def __init__(self, api_key: str, base_url: str = "https://api-publica.datajud.cnj.jus.br") -> None:
        self._api_key = api_key
        self._base_url = base_url

    async def search_by_number(self, process_number: str) -> AdapterResult:
        raise NotImplementedError("RealCNJAdapter nao implementado — aguardando acesso DataJud.")

    async def search_by_party(self, name: str, document: str | None = None) -> AdapterResult:
        raise NotImplementedError("RealCNJAdapter nao implementado — aguardando acesso DataJud.")


def create_cnj_adapter(
    backend: str = "mock",
    api_key: str | None = None,
) -> CNJPort:
    if backend == "real":
        if not api_key:
            raise ValueError("CNJ_API_KEY obrigatoria para backend=real")
        return RealCNJAdapter(api_key=api_key)
    return MockCNJAdapter()
