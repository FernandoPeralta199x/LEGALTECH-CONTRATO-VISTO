# PERSIST — Fluxo Operacional (correções) Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans para implementar task-by-task. Steps usam checkbox (`- [ ]`).
> **Verificação:** o sandbox NÃO roda PostgreSQL/app completo. Cada task é verificada rodando os testes de rota no ambiente do usuário (Windows + `.venv` + Postgres). O autor do plano diagnostica; o usuário executa e confirma.

**Goal:** Eliminar os 15 reds restantes dos testes de rota (operational/report/triage), que são sintomas do split-brain `_STORE` em memória ↔ PostgreSQL.

**Architecture:** O fluxo operacional está meio-migrado: `RequestService` persiste em Postgres, mas as rotas operacionais (cases/triage/reports) ainda usam `MockRequestRepository`/`InMemoryOperationalStore` (`_STORE`). Os bugs vêm de (a) um endpoint que retorna ORM cru sem mapper, e (b) leituras no store em memória que não enxergam o que foi criado no banco.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic v2, unittest, Alembic, PostgreSQL.

---

## Diagnóstico (causa-raiz dos 3 bugs)

1. **`AttributeError: 'Case' object has no attribute 'model_dump'` (13x)**
   `requests/router.py:get_request_case` → `RequestService.get_request_case` → `requests/repository.py:get_case` retorna o `Case` **cru do ORM**. O helper `dump_model` chama `.model_dump()` (Pydantic). Já existe o mapper `case_bridge.OperationalCaseRepository._to_schema(case) -> CaseSchema`, mas o `get_case` não o usa.

2. **`ValueError: Case not found for organization` + 3. `status 'case_created' != 'submitted'`**
   Levantados em `contracts/mock_repositories.py` (o `_STORE` em memória). As rotas operacionais leem/escrevem no store em memória, que não compartilha estado com o que `RequestService` grava no banco → split-brain. Núcleo do PERSIST-02/03.

---

## File Structure

- `src/modules/contracts/case_bridge.py` — extrair `case_to_schema()` (mapper Case→CaseSchema) reutilizável.
- `src/modules/requests/repository.py` — `get_case()` passa a retornar `CaseSchema`.
- `src/modules/contracts/operational.py` — fiação dos repositórios operacionais (mock vs DB).
- `src/modules/contracts/mock_repositories.py` — `_STORE` em memória (a ser substituído por repos DB-backed).
- Testes: `tests/test_operational_backend_routes.py`, `tests/test_report_generation.py`, `tests/test_triage_provider_results.py`.

---

## Task 1: Mapper Case→CaseSchema no get_request_case (resolve os 13 `model_dump`)

**Files:**
- Modify: `src/modules/contracts/case_bridge.py`
- Modify: `src/modules/requests/repository.py`
- Test: `tests/test_operational_backend_routes.py` (já existentes; rodar para verificar)

- [ ] **Step 1 — Extrair mapper reutilizável em `case_bridge.py`**

Adicionar função module-level (o corpo é idêntico ao `_to_schema` atual, que não usa `self`):

```python
def case_to_schema(case) -> CaseSchema:
    return CaseSchema(
        id=case.id,
        request_id=case.request_id,
        code=case.code or "",
        organization_id=case.organization_id,
        created_by=case.created_by,
        product_type=case.product_type,
        product_label=case.product_label,
        title=case.title,
        description=case.description or "",
        status=CaseStatus(case.status),
        progress=case.progress,
        risk_level=RiskLevel(case.risk_level),
        recommendation=case.recommendation,
        source_mode=case.source_mode,
        is_local_simulation=case.is_local_simulation,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )
```

E fazer `OperationalCaseRepository._to_schema` delegar: `return case_to_schema(case)` (DRY).

- [ ] **Step 2 — Usar o mapper em `requests/repository.py:get_case`**

```python
def get_case(self, *, organization_id: UUID, request_id: UUID) -> "CaseSchema | None":
    from src.models.case import Case
    from src.modules.contracts.case_bridge import case_to_schema

    case = self._db.execute(
        select(Case).where(
            Case.request_id == _as_uuid(request_id),
            Case.organization_id == _as_uuid(organization_id),
        )
    ).scalar_one_or_none()
    return case_to_schema(case) if case is not None else None
```

(Atualizar a anotação de retorno de `Any | None` para `CaseSchema | None`. `CaseSchema` já é importado no módulo.)

- [ ] **Step 3 — Verificar (no ambiente do usuário)**

```powershell
cd X:\QUOARYA\legaltech-aws\apps\api
.\.venv\Scripts\python.exe -m unittest -v `
  tests.test_operational_backend_routes `
  tests.test_report_generation `
  tests.test_triage_provider_results
```
Esperado: os erros `'Case' object has no attribute 'model_dump'` desaparecem. (Podem restar os 2 bugs de store — Task 2.)

- [ ] **Step 4 — Commit** (após verde do usuário)

```bash
git add apps/api/src/modules/contracts/case_bridge.py apps/api/src/modules/requests/repository.py
git commit -m "fix(requests): get_request_case retorna CaseSchema via mapper (resolve model_dump)"
```

---

## Task 2: Unificar repositórios operacionais no PostgreSQL (resolve ValueError + status; núcleo PERSIST-02/03)

> Este é o trabalho substantivo do PERSIST e exige tracing do fluxo completo + verificação no banco. Estruturado como investigação→migração→verificação, task a task, com o usuário rodando os testes.

- [x] **Step 1 — Mapa mock vs DB (CONCLUIDO)**

`build_operational_repositories()` monta 8 repositorios, todos default Mock (`_STORE` em memoria). So `requests`/`cases` aceitam override; os outros 6 sao forcados a mock. Os servicos operacionais chamam `build_operational_repositories()` SEM sessao `db`.

| Operacao | Repo atual | Versao DB existe? |
|---|---|---|
| requests | Mock | sim (`RequestRepository`) |
| cases | Mock | sim (`OperationalCaseRepository`/case_bridge -> `SqlCaseRepository`) |
| parties | Mock | parcial |
| documents | Mock | parcial |
| timeline | Mock | nao |
| triage | Mock | nao |
| provider_results | Mock | nao |
| reports | Mock | nao |

Consumidores em mock: `cases/operational_detail.py`, `cases/operational_list.py`, `provider_results/service.py` (e triage/reports). `RequestService` ja usa o banco -> split-brain.

Implicacao para os proximos steps: alem de implementar os repos DB faltantes, e preciso **threading da sessao `db`** pela cadeia rota->servico->`build_operational_repositories`, e remover o forcamento a mock dos 6 repositorios.

- [ ] **Step 2 — Definir repositórios DB-backed para as operações ainda em memória**

Para cada operação mapeada no Step 1 que usa `_STORE`, implementar a versão Postgres (espelhando o padrão de `requests/repository.py`, usando `case_bridge` para mapear ORM↔Schema). Uma operação por vez, com teste de rota correspondente como critério.

- [ ] **Step 3 — Trocar a fiação para os repos DB-backed**

Ajustar `build_operational_repositories` (e/ou as dependências das rotas) para usar os repositórios Postgres. Garantir filtro por `organization_id` em toda query (multi-tenant) e `audit_log` nos eventos críticos.

- [ ] **Step 4 — Verificar incrementalmente (usuário)**

Após cada operação migrada, rodar os 3 arquivos de teste de rota. Critério final: `ValueError: Case not found` e `'case_created' != 'submitted'` resolvidos; suíte de rota verde.

- [ ] **Step 5 — Commits incrementais** (um por operação migrada, mensagem `feat(persist): migra <operação> para PostgreSQL`).

**Critério de aceite (PERSIST-02/03):** nenhuma rota operacional depende de `_STORE`/`InMemoryOperationalStore`; dados persistem após restart; `organization_id` aplicado em todas as queries; eventos críticos em `audit_log`.

---

## Notas de verificação
- O autor do plano **não consegue executar** os testes de rota (sandbox sem Postgres). Toda verificação é do lado do usuário, com os comandos acima.
- Task 1 é cirúrgica e de baixo risco. Task 2 é o núcleo do PERSIST e deve ser feita incrementalmente, operação por operação, com verificação a cada passo.
