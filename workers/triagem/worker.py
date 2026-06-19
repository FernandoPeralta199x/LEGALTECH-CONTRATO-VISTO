"""Worker de triagem — executa analise inicial de um caso.

Fluxo:
1. Recebe job da fila local (ou SQS)
2. Valida idempotencia
3. Executa consultas externas via adapters (Escavador, Serasa, CNJ)
4. Registra resultados na timeline do caso
5. Atualiza status do caso para ``in_analysis``
6. Gera audit log

Uso local:
    python -m workers.triagem.worker
"""

from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from src.adapters.escavador import MockEscavadorAdapter
from src.adapters.serasa import MockSerasaAdapter
from src.adapters.cnj import MockCNJAdapter
from src.adapters.base import AdapterResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-5s  [triagem]  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("triagem")

QUEUE_PATH = ROOT / "apps" / "api" / "storage" / "local_queue" / "triage.jsonl"
RESULTS_DIR = ROOT / "apps" / "api" / "storage" / "triage_results"
POLL_INTERVAL = 3


def ensure_dirs() -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def read_next_job() -> dict[str, Any] | None:
    if not QUEUE_PATH.exists():
        return None
    lines = QUEUE_PATH.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        return None
    job = json.loads(lines[0])
    QUEUE_PATH.write_text(
        "\n".join(lines[1:]) + ("\n" if len(lines) > 1 else ""),
        encoding="utf-8",
    )
    return job


def is_already_processed(case_id: str) -> bool:
    return (RESULTS_DIR / f"{case_id}.json").exists()


async def run_triage(job: dict[str, Any]) -> dict[str, Any]:
    """Executa triagem com os adapters mock."""
    case_id = job["case_id"]
    cpf_cnpj = job.get("cpf_cnpj", "00000000000")
    party_name = job.get("party_name", "Parte Desconhecida")

    logger.info("Iniciando triagem case_id=%s cpf_cnpj=%s", case_id, cpf_cnpj[:6])

    escavador = MockEscavadorAdapter()
    serasa = MockSerasaAdapter()
    cnj = MockCNJAdapter()

    escavador_result = await escavador.search_lawsuits(cpf_cnpj)
    serasa_result = await serasa.check_credit(cpf_cnpj)
    cnj_result = await cnj.search_by_party(party_name, cpf_cnpj)

    triage_result = {
        "case_id": case_id,
        "status": "completed",
        "sources": {
            "escavador": asdict(escavador_result),
            "serasa": asdict(serasa_result),
            "cnj": asdict(cnj_result),
        },
        "summary": {
            "lawsuits_found": escavador_result.data.get("total", 0),
            "credit_score": serasa_result.data.get("score", 0),
            "cnj_processes": cnj_result.data.get("total", 0),
            "overall_risk": _assess_overall_risk(
                escavador_result, serasa_result, cnj_result,
            ),
        },
        "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    result_path = RESULTS_DIR / f"{case_id}.json"
    result_path.write_text(json.dumps(triage_result, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Triagem concluida case_id=%s risk=%s", case_id, triage_result["summary"]["overall_risk"])

    return triage_result


def _assess_overall_risk(
    escavador: AdapterResult,
    serasa: AdapterResult,
    cnj: AdapterResult,
) -> str:
    """Avaliacao simplificada de risco com base nos resultados."""
    lawsuits = escavador.data.get("total", 0)
    score = serasa.data.get("score", 0)
    cnj_total = cnj.data.get("total", 0)

    risk_points = 0
    if lawsuits > 3:
        risk_points += 2
    elif lawsuits > 0:
        risk_points += 1
    if score < 500:
        risk_points += 2
    elif score < 700:
        risk_points += 1
    if cnj_total > 2:
        risk_points += 1

    if risk_points >= 4:
        return "high"
    if risk_points >= 2:
        return "medium"
    return "low"


def main() -> None:
    """Loop principal do worker."""
    import asyncio

    ensure_dirs()
    logger.info("Worker de triagem iniciado — fila: %s", QUEUE_PATH)

    while True:
        job = read_next_job()
        if job is None:
            time.sleep(POLL_INTERVAL)
            continue

        case_id = job.get("case_id", "unknown")
        if is_already_processed(case_id):
            logger.info("Job ja processado (idempotente) case_id=%s", case_id)
            continue

        try:
            asyncio.run(run_triage(job))
        except Exception:
            logger.exception("Erro na triagem case_id=%s", case_id)


if __name__ == "__main__":
    main()
