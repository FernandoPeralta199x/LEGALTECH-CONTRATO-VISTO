# PERSIST Caminho F — Migração Plena do Fluxo Operacional para PostgreSQL — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:executing-plans` (ou `subagent-driven-development`) para executar task-by-task. Steps usam checkbox `- [ ]`.
>
> **REGRA DE VERIFICAÇÃO (não-negociável):** o ambiente do **autor do plano não roda PostgreSQL** (sandbox Python 3.10; o projeto exige 3.11+). **Toda** verificação que toca banco/rota é feita por quem executa, num ambiente com Postgres (Windows + `.venv`). Cada passo só é considerado "done" depois do `unittest` correspondente verde no ambiente do executor. Nunca commitar sem o verde do executor.

**Goal:** Eliminar o split-brain operacional fazendo o caminho de leitura operacional (lista de casos + agregado) ler do PostgreSQL, com repositórios DB-backed para parties/documents/timeline/triage/provider_results/reports (criando as 3 tabelas que ainda não existem), co-migrando os testes de rota para semear no banco em vez do `_STORE`, e removendo o `InMemoryOperationalStore` do fluxo de produção.

**Architecture:** `build_operational_repositories(db)` já aceita `db` (Item 1, commit `e526f5e`). Quando `db` está presente, o builder passa a montar repos DB-backed; sem `db`, mantém mock (preserva unit tests que instanciam o builder direto). Os repos DB-backed espelham o padrão de `src/modules/contracts/case_bridge.py` (`OperationalCaseRepository`/`SqlCaseRepository`) e `src/modules/requests/repository.py`. `parties`, `documents` e `reports` já têm ORM; `timeline_events`, `triage_modules` e `provider_results` precisam de novos modelos ORM + migration Alembic. Os testes de rota operacional são reescritos para semear via `build_operational_repositories(db=session)` (escrevendo no banco) em vez do `_STORE`.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, PostgreSQL + pgvector, unittest.

---

## Restrição multi-tenant e auditoria (aplicar em TODOS os passos)

- Toda query DB filtra por `organization_id` (parâmetro obrigatório em cada método de repositório).
- Toda tabela nova carrega `organization_id UUID NOT NULL` + índice por `(organization_id, case_id)`.
- Eventos críticos de escrita (criação de report, liberação) continuam gerando `audit_log` na camada de serviço (não regredir o que já existe).
- Nunca logar PII (CPF/CNPJ/documento bruto). `PartySchema.document` é `exclude=True` — manter.

---

## Protocolo de verificação por passo (executor)

```powershell
cd X:\QUOARYA\legaltech-aws\apps\api
$env:DATABASE_URL="postgresql+psycopg://legaltech:legaltech_dev@localhost:5432/legaltech"
# aplicar migrations quando o passo criar/alterar schema:
.\.venv\Scripts\alembic.exe upgrade head
# rodar o(s) arquivo(s) de teste do passo:
.\.venv\Scripts\python.exe -m unittest -v `
  tests.test_operational_backend_routes `
  tests.test_triage_provider_results `
  tests.test_report_generation
```
Baseline atual (antes deste plano): **14 reds** (8 fail + 6 error), todos split-brain. Critério final do plano: **0 reds** nesses 3 arquivos, sem regressão nos demais.

---

## File Structure

**Criar:**
- `src/models/timeline_event.py` — ORM `TimelineEvent` (tabela `timeline_events`).
- `src/models/triage_module.py` — ORM `TriageModule` (tabela `triage_modules`).
- `src/models/provider_result.py` — ORM `ProviderResult` (tabela `provider_results`).
- `alembic/versions/0013_operational_tables.py` — migration das 3 tabelas + índices.
- `src/modules/contracts/db_repositories.py` — repos DB-backed: `SqlPartyRepository`, `SqlDocumentRepository`, `SqlTimelineRepository`, `SqlTriageRepository`, `SqlProviderResultRepository`, `SqlReportRepository` (espelham a interface dos `Mock*Repository`).

**Modificar:**
- `src/models/__init__.py` — registrar os 3 novos modelos.
- `src/modules/contracts/case_bridge.py` — `OperationalCaseRepository.get_aggregate` compõe o agregado a partir dos repos DB (não mais vazio); corrige `triage_status`.
- `src/modules/contracts/operational.py` — `build_operational_repositories(db=...)` monta os repos DB quando `db` presente.
- `tests/test_models_metadata.py` — registrar as 3 tabelas novas + índices esperados.
- `tests/test_operational_backend_routes.py`, `tests/test_triage_provider_results.py`, `tests/test_report_generation.py` — semear via `build_operational_repositories(db=<session de teste>)`.

**Referências de padrão (ler antes de escrever cada tipo):**
- ORM model + mixins: `src/models/case_party.py`, `src/models/report.py`, `src/models/mixins.py`, `src/models/types.py`.
- Migration: `alembic/versions/0012_request_price_snapshot.py`.
- Repo DB (mapper ORM↔schema): `src/modules/contracts/case_bridge.py` (`case_to_schema`, `SqlCaseRepository`).
- Interface a espelhar (assinaturas `create`/`list_by_case`): `src/modules/contracts/mock_repositories.py` (`MockPartyRepository` L520, `MockDocumentRepository` L627, `MockTimelineRepository` L728, `MockTriageRepository` L775, `MockProviderResultRepository` L879, `MockReportRepository` L956).

---

## Campos das entidades (fonte: `src/modules/contracts/schemas.py`)

Use estes campos ao definir ORM e migration. Tipos enum são strings na coluna (`VARCHAR`), convertidos no mapper.

- **TimelineEventSchema:** id, case_id, organization_id, type:str, title:str, description:str, severity:enum, source:enum, source_mode:enum, metadata:jsonb(default {}), created_at:ts.
- **TriageModuleSchema:** id, case_id, organization_id, module_key:str, module_label:str, provider:str, status:enum, source_mode:enum, required:bool, reason:str, started_at:ts?, finished_at:ts?, attempts:int(0), error_code:str?.
- **ProviderResultSchema:** id, case_id, triage_module_id, organization_id, provider:str, provider_request_id:str?, source_mode:enum, status:enum, input_hash:str, raw_result_ref:str?, normalized_result:jsonb({}), summary:str?, risk_signals:jsonb([]), confidence:float?.
- (parties/documents/reports: usar ORM existente `case_party.py`/`document.py`/`report.py`.)

---

## Phase A — Novas tabelas DB (timeline, triage, provider_results)

### Task A1: Modelos ORM das 3 entidades

**Files:**
- Create: `src/models/timeline_event.py`, `src/models/triage_module.py`, `src/models/provider_result.py`
- Modify: `src/models/__init__.py`
- Test: `tests/test_models_metadata.py`

- [ ] **Step 1 — Ler o padrão.** Abrir `src/models/case_party.py` e `src/models/mixins.py` para copiar exatamente: base declarativa, `TimestampMixin`/`UUIDPkMixin` (nomes reais), tipo UUID (`src/models/types.py`), e o estilo de `__tablename__`/`Index`.

- [ ] **Step 2 — Escrever `tests/test_models_metadata.py` (falha primeiro).** Adicionar `timeline_events`, `triage_modules`, `provider_results` ao set `expected_tables` (L13) e ao `tenant_tables` (L40), e os índices ao `expected_indexes` (L98):

```python
# em expected_tables:
"timeline_events", "triage_modules", "provider_results",
# em tenant_tables (exigem organization_id NOT NULL):
"timeline_events", "triage_modules", "provider_results",
# em expected_indexes:
"idx_timeline_events_org_case",
"idx_triage_modules_org_case",
"idx_provider_results_org_case",
"idx_provider_results_triage_module",
```

- [ ] **Step 3 — Rodar e ver falhar.**
Run: `.\.venv\Scripts\python.exe -m unittest -v tests.test_models_metadata`
Expected: FAIL (`timeline_events` etc. não em `Base.metadata.tables`).

- [ ] **Step 4 — Criar os 3 modelos ORM** seguindo o padrão do `case_party.py`. Exemplo concreto (`src/models/triage_module.py`); replicar a estrutura para timeline_event e provider_result usando os campos da seção "Campos das entidades":

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base            # confirmar caminho real em case_party.py
from src.models.mixins import TimestampMixin, UUIDPkMixin  # confirmar nomes reais
from src.models.types import GUID       # tipo UUID usado no projeto


class TriageModule(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "triage_modules"

    organization_id: Mapped[GUID] = mapped_column(GUID(), ForeignKey("organizations.id"), nullable=False)
    case_id: Mapped[GUID] = mapped_column(GUID(), ForeignKey("cases.id"), nullable=False)
    module_key: Mapped[str] = mapped_column(String(100), nullable=False)
    module_label: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    source_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        Index("idx_triage_modules_org_case", "organization_id", "case_id"),
    )
```
(timeline_events: type/title/description/severity/source/source_mode/metadata(JSONB); provider_results: + `triage_module_id` FK→triage_modules, normalized_result/risk_signals JSONB, confidence Float. Use `from sqlalchemy.dialects.postgresql import JSONB` como em modelos existentes.)

- [ ] **Step 5 — Registrar em `src/models/__init__.py`** (mesmo padrão dos demais imports). Adicionar import dos 3 e incluir no `__all__` se houver.

- [ ] **Step 6 — Rodar e ver passar.**
Run: `.\.venv\Scripts\python.exe -m unittest -v tests.test_models_metadata`
Expected: PASS. (Não toca o banco ainda — é metadata.)

- [ ] **Step 7 — Commit** (após verde do executor):
```bash
git add apps/api/src/models/timeline_event.py apps/api/src/models/triage_module.py apps/api/src/models/provider_result.py apps/api/src/models/__init__.py apps/api/tests/test_models_metadata.py
git commit -m "feat(models): tabelas operacionais timeline/triage/provider_results (ORM)"
```

### Task A2: Migration Alembic das 3 tabelas

**Files:**
- Create: `alembic/versions/0013_operational_tables.py`

- [ ] **Step 1 — Gerar a migration base.**
Run: `.\.venv\Scripts\alembic.exe revision --autogenerate -m "operational tables"`
Renomear o arquivo para `0013_operational_tables.py` e ajustar `down_revision = "0012_request_price_snapshot"` (confirmar id real do head com `alembic history`).

- [ ] **Step 2 — Revisar o autogenerate** contra a Task A1 (3 tabelas, FKs para organizations/cases, FK provider_results→triage_modules, índices `idx_*_org_case`, JSONB onde aplicável). Conferir que NÃO criou/dropou nada além das 3 tabelas (se criou diffs espúrios, remover).

- [ ] **Step 3 — Aplicar e checar.**
Run:
```
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current   # deve mostrar 0013_operational_tables (head)
```
Run downgrade smoke: `.\.venv\Scripts\alembic.exe downgrade -1` depois `upgrade head` — sem erro.

- [ ] **Step 4 — Rodar a suite (sem regressão).**
Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests`
Expected: ainda **14 reds** (as tabelas existem mas nada as usa). Nenhum novo.

- [ ] **Step 5 — Commit:**
```bash
git add apps/api/alembic/versions/0013_operational_tables.py
git commit -m "feat(db): migration 0013 cria tabelas operacionais"
```

---

## Phase B — Repositórios DB-backed (write + read)

> Cada repo espelha a interface do `Mock*Repository` correspondente (mesma assinatura de `create`/`list_by_case`/`create_module`/`list_modules`) para que os testes possam semear via `build_operational_repositories(db=session)` sem mudar a forma de chamada. Mapper ORM↔schema no estilo `case_to_schema`.

### Task B1: `SqlPartyRepository` e `SqlDocumentRepository` (ORM já existe)

**Files:**
- Create: `src/modules/contracts/db_repositories.py`
- Test: `tests/test_operational_backend_routes.py` (cobertura indireta na Phase D); aqui um teste de repo dedicado.

- [ ] **Step 1 — Teste de repo (falha primeiro)** em `tests/test_db_repositories.py` (novo), usando a fixture de sessão DB já usada nos testes de rota (copiar o setup de sessão de `tests/test_operational_backend_routes.py`). Testar: `SqlPartyRepository(db).create(organization_id, case_id, values={...})` persiste e `list_by_case(organization_id, case_id)` retorna `PartySchema` com `document` mascarado e filtrado por org.

```python
def test_sql_party_repository_persists_and_lists_scoped(self):
    repo = SqlPartyRepository(self.db)
    repo.create(organization_id=ORG_A, case_id=self.case_id,
                values={"name": "Parte A", "role": "contratante", "document": "00000000000"})
    items = repo.list_by_case(organization_id=ORG_A, case_id=self.case_id)
    self.assertEqual(1, len(items))
    self.assertEqual("Parte A", items[0].name)
    self.assertIsNone(repo.list_by_case(organization_id=ORG_B, case_id=self.case_id) or None) \
        if False else self.assertEqual([], repo.list_by_case(organization_id=ORG_B, case_id=self.case_id))
```

- [ ] **Step 2 — Rodar e ver falhar** (`ImportError`/método inexistente).
Run: `.\.venv\Scripts\python.exe -m unittest -v tests.test_db_repositories`

- [ ] **Step 3 — Implementar** `SqlPartyRepository` e `SqlDocumentRepository` em `db_repositories.py`, mapeando do ORM `CaseParty`/`Document` para `PartySchema`/`DocumentSchema`. Espelhar as assinaturas exatas de `MockPartyRepository.create` (L524) e `list_by_case` (L555). Mascarar `document` no mapper (reusar util de `src/modules/common/pii.py`). Toda query com `.where(Model.organization_id == org, Model.case_id == case)`.

- [ ] **Step 4 — Rodar e ver passar.** Run o mesmo unittest. Expected: PASS.

- [ ] **Step 5 — Commit:** `feat(persist): SqlPartyRepository e SqlDocumentRepository`.

### Task B2: `SqlTimelineRepository`, `SqlTriageRepository`, `SqlProviderResultRepository`, `SqlReportRepository`

- [ ] Repetir o ciclo TDD da Task B1 para cada repo, um por vez, com teste dedicado em `tests/test_db_repositories.py`:
  - `SqlTimelineRepository`: espelhar `MockTimelineRepository.list_by_case` (L732) + um `create_event` se os serviços escreverem timeline (conferir chamadas em `src/modules/timeline/`).
  - `SqlTriageRepository`: espelhar `MockTriageRepository.create_module` (L779) e `list_modules` (L815).
  - `SqlProviderResultRepository`: espelhar `MockProviderResultRepository.create` (L883) e `list_by_case` (L923); FK `triage_module_id`.
  - `SqlReportRepository`: espelhar `MockReportRepository.create` (L960) + leitura do "current report"; mapear do ORM `Report` existente.
- [ ] Cada um: teste falha → implementa → passa → commit (`feat(persist): Sql<Entidade>Repository`).

---

## Phase C — Agregado DB-backed no `OperationalCaseRepository`

### Task C1: `get_aggregate` compõe do banco + corrige enums

**Files:**
- Modify: `src/modules/contracts/case_bridge.py:89-126`

- [ ] **Step 1 — Teste (via Phase D)**: a verificação real é `test_case_aggregate_returns_only_case_scoped_operational_data`. Aqui, garantir o comportamento no nível do bridge.

- [ ] **Step 2 — Reescrever `get_aggregate`** para receber/usar os repos DB (injetar via `__init__`, ver Task D1) e compor parties/documents/timeline/triage/provider_results/report do banco, replicando a lógica de derivação do `MockCaseRepository.get_aggregate` (L261-330): `parties_count=len(parties)`, `documents_count=len(documents)`, `triage_status=self._triage_status(triage_modules)` (mesma regra: vazio → `ModuleStatus.NOT_STARTED`, nunca `None`), `report_status=report.status if report else ReportStatus.NOT_STARTED`, `latest_event_at=max(created_at, default=None)`, `progress` pela mesma fórmula. **Esta correção elimina o `triage_status=None` (L107) que causava `NoneType.value`.**

- [ ] **Step 3 — Verificação:** Phase D (rota). Expected após Phase D: `test_case_aggregate_*` verde.

- [ ] **Step 4 — Commit:** `feat(persist): OperationalCaseRepository.get_aggregate compoe do banco`.

---

## Phase D — Wiring do builder (db presente → repos DB)

### Task D1: `build_operational_repositories(db)` monta repos DB

**Files:**
- Modify: `src/modules/contracts/operational.py:172-188`
- Modify: `src/modules/contracts/case_bridge.py` (`OperationalCaseRepository.__init__` aceita os repos DB)

- [ ] **Step 1 — Ajustar o builder:** quando `db is not None`, construir:
```python
if db is not None:
    from src.modules.contracts.case_bridge import OperationalCaseRepository
    from src.modules.contracts.db_repositories import (
        SqlPartyRepository, SqlDocumentRepository, SqlTimelineRepository,
        SqlTriageRepository, SqlProviderResultRepository, SqlReportRepository,
    )
    from src.modules.requests.repository import RequestRepository
    parties = SqlPartyRepository(db)
    documents = SqlDocumentRepository(db)
    timeline = SqlTimelineRepository(db)
    triage = SqlTriageRepository(db)
    provider_results = SqlProviderResultRepository(db)
    reports = SqlReportRepository(db)
    return OperationalRepositories(
        requests=requests or RequestRepository(db),
        cases=cases or OperationalCaseRepository(
            db, parties=parties, documents=documents, timeline=timeline,
            triage=triage, provider_results=provider_results, reports=reports),
        parties=parties, documents=documents, timeline=timeline, triage=triage,
        provider_results=provider_results, reports=reports,
    )
# senão: bloco mock atual (inalterado)
```
(Remover o `_ = db` do Item 1.) `OperationalCaseRepository.__init__` passa a aceitar e guardar esses repos para o `get_aggregate` (Task C1).

- [ ] **Step 2 — `OperationalRepositories` dataclass:** os tipos dos campos parties/documents/etc. hoje são `Mock*`. Trocar para os Protocols correspondentes (ou `Any`) para aceitar as duas implementações. Definir Protocols mínimos se necessário (espelhar o estilo de `CaseRepositoryProtocol`).

- [ ] **Step 3 — Verificação (rota):**
Run: `.\.venv\Scripts\python.exe -m unittest -v tests.test_operational_backend_routes`
Expected: **ainda falha** — porque os testes semeiam o `_STORE` (mock), não o banco. Isso é esperado; a Phase E reescreve os testes. NÃO commitar ainda se quebrar outros arquivos; se quebrar, revisar fiação.

- [ ] **Step 4 — Commit** (somente após Phase E verde-conjunta): adiar.

---

## Phase E — Co-migração dos testes (semear no banco)

> Causa de a Phase D não bastar: os testes fazem `build_operational_repositories().parties.create(...)` (mock). Trocar para `build_operational_repositories(db=<session de teste>).parties.create(...)`, escrevendo no banco que a rota agora lê.

### Task E1: Reescrever seeds em `test_operational_backend_routes.py`

**Files:**
- Modify: `tests/test_operational_backend_routes.py` (linhas 341, 431, e demais `build_operational_repositories()`); idem `test_triage_provider_results.py`, `test_report_generation.py`.

- [ ] **Step 1 — Localizar a sessão de teste.** Identificar como o teste obtém a `Session` do banco (a mesma usada por `create_request`/override de `get_db`). Expor um helper no `setUp`, ex. `self.db_session`.

- [ ] **Step 2 — Trocar o builder de seed** em cada ponto:
```python
# antes:
repositories = build_operational_repositories()
# depois:
repositories = build_operational_repositories(db=self.db_session)
```
As chamadas `.parties.create(...)`, `.documents.create(...)`, `.triage.create_module(...)`, `.reports.create(...)` agora persistem no banco (graças à Phase B). As asserções (`parties_count=1`, `triage_status="completed"`, `report_status="ready"`) passam a refletir o banco que a rota lê.

- [ ] **Step 3 — Rodar os 3 arquivos.**
Run:
```
.\.venv\Scripts\python.exe -m unittest -v tests.test_operational_backend_routes tests.test_triage_provider_results tests.test_report_generation
```
Iterar entidade por entidade: se `test_cases_list` falhar em `documents_count`, revisar `SqlDocumentRepository`/seed; um sintoma por vez (systematic-debugging).

- [ ] **Step 4 — Rodar a suite inteira** (garantir que os unit tests que usam `build_operational_repositories()` SEM db continuam mock e verdes).
Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests`
Expected: os 14 reds operacionais → 0; total de reds cai para os não-relacionados (idealmente 0).

- [ ] **Step 5 — Commit conjunto** (Phases C+D+E, pois só fazem sentido juntas):
```bash
git add apps/api/src/modules/contracts/ apps/api/tests/test_operational_backend_routes.py apps/api/tests/test_triage_provider_results.py apps/api/tests/test_report_generation.py
git commit -m "feat(persist): caminho operacional le do PostgreSQL (agregado + wiring + testes)"
```

---

## Phase F — Cleanup e endurecimento

### Task F1: Remover `_STORE` do fluxo de produção

- [ ] **Step 1 — Auditar consumidores** de `build_operational_repositories()` SEM `db` no código de produção (não-teste):
Run: `grep -rn "build_operational_repositories()" apps/api/src` (sem `db=`).
Esperado após Phases A-E: nenhum no caminho de rota (todos recebem `db`). Se sobrar algum em produção, threadar `db` (como no Item 1).

- [ ] **Step 2 — Confirmar isolamento multi-tenant** com o teste cross-org existente (`test_*_isolated_by_*_organization`) verde.

- [ ] **Step 3 — Confirmar `audit_log`** nos eventos de criação de report/liberação (não regrediu).

- [ ] **Step 4 — Tornar os testes de backend bloqueantes no CI** (`.github/workflows/ci.yml`): remover `continue-on-error` do step "Run tests (baseline)" do job backend — **somente** quando a suite estiver 100% verde. Commit isolado: `ci(api): testes backend bloqueantes (suite verde)`.

- [ ] **Step 5 — Atualizar STATUS doc** e marcar PERSIST/ADR-0002 como `Accepted`/implementado.

### Task F2 (opcional, pós-verde): RLS

- [ ] Avaliar Row Level Security (Postgres) nas tabelas sensíveis (`cases`, `documents`, `reports`, `audit_log`, + as 3 novas) conforme o doc de arquitetura V2 (seção 8). Plano separado — não bloquear o fechamento do PERSIST.

---

## Self-Review (cobertura × spec)

- Split-brain (case lido do banco) → Phases C/D. ✓
- Sub-dados operacionais no banco → Phases A/B. ✓
- `NoneType.value` (triage_status) → Task C1 (default `NOT_STARTED`). ✓
- Tabelas faltantes (timeline/triage/provider_results) → Phase A. ✓
- Testes acoplados ao `_STORE` → Phase E. ✓
- Multi-tenant em toda query → seção de restrições + filtros por `organization_id`. ✓
- `_STORE` fora do fluxo de produção → Task F1. ✓
- CI backend bloqueante → Task F1 Step 4. ✓
- Unit tests que usam mock direto → preservados (db=None mantém mock). ✓

**Riscos conhecidos:** (1) nomes reais de mixins/base/tipo UUID podem diferir do exemplo — Step A1.1 manda conferir no `case_party.py`. (2) A `Session` de teste para seed (E1.1) depende do setup atual — confirmar antes. (3) Se algum serviço (não só leitura) escreve sub-dados via `_STORE`, a escrita também precisa ir ao banco — cobrir ao migrar cada entidade (Phase B inclui `create`).
