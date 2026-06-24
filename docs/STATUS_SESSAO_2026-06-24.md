# STATUS / Handoff da sessao — 2026-06-24

Documento de retomada: o que foi feito, o que esta pendente e como continuar de cada ponto.

## Resumo executivo
- Saimos de workspace travado (indice git corrompido, mount sem unlink) para a fase de
  auth/seguranca endurecida e publicada no `origin/main`.
- **Testes: 31 -> 14 reds**, cada mudanca verificada onde havia como.
- PERSIST (Task 2) **desenhada** (ADR-0002) e mapeada, pausada para execucao com banco no loop.
- FIN-READY-DIAG (Fase 4) concluido; **FIN-01 Increment 1** iniciado (no working tree).

## Estado do git
- `origin/main`: contem auth/seguranca + TENANT + registro de modelos + FK seed + mapper.
- **Local ahead** (falta push): `ADR-0002`, `FIN-READY-DIAG`, `STATUS` (este).
- **Working tree (NAO commitado):** FIN-01 Increment 1 — `src/models/request.py` (+2 colunas)
  e `alembic/versions/0012_request_price_snapshot.py`. Salvos em disco; commitar apos validar.

## Concluido (verificado)
- **SAFE-01:** limpeza de EOL, reparo do indice corrompido, `.gitignore` de governanca.
- **Fase 1 (BUGs):** BUG-01/02 ja resolvidos no codigo; **BUG-03** (branch morto mock_ai) corrigido.
- **Fase 2 (Auth/Seguranca):**
  - `ADR-0001` — auth de producao (Cognito Hosted UI / OIDC+PKCE).
  - `AUTH-07` — gate de ambiente (auth local 404 fora de `local`), TDD real.
  - `AUTH-03/C-02` — verify_email nao concede tenant/sessao (pending_approval), TDD real.
  - Cognito **fail-closed** quando `client_id` ausente, TDD real.
  - `SEC-02 fatia 1` — rate limiting por IP nos endpoints de auth (in-memory, plugavel p/ Redis), TDD.
  - Runbook de implementacao Cognito (`docs/COGNITO_OPCAO_A_RUNBOOK.md`).
- **Modelos / multi-tenant:**
  - `organization_id` NOT NULL nas entidades tenant, nullable so em `users` (realinha modelo ao schema).
  - Registro dos modelos `request*` no `src/models/__init__` + `test_models_metadata` 100% verde.
  - Seed do usuario autenticado nos testes de rota (resolve FK `requests.created_by`).
  - Mapper `Case->CaseSchema` em `get_request_case` (resolve `model_dump`).
- **Fase 4:** `FIN-READY-DIAG` (`docs/diagnostics/FIN-READY-DIAG.md`): financeiro forte
  (centavos inteiros, calculo no backend, RBAC, audit em alteracao de preco). Gap = FIN-01.

## Pendente — como retomar

### Task 2 — PERSIST (unificar repositorios operacionais no banco)
- Guia: `docs/adr/ADR-0002-unificacao-repositorios-operacionais.md` + `docs/superpowers/plans/2026-06-24-persist-fluxo-operacional.md`.
- Causa-raiz: split-brain `_STORE`(memoria) x Postgres. `build_operational_repositories` monta
  8 repos default mock; servicos de leitura nao recebem `db`.
- LICAO PROVADA: threading de leitura sozinho **regride** (14->15). Migrar **caminho-coeso**
  (escrita+leitura), com `pytest` a cada micro-passo (banco no loop).
- Primeiro alvo concreto: o bug `AttributeError: NoneType ... 'value'` no caminho DB de
  `list-cases`/`aggregate`.

### FIN-01 — snapshot de preco no pedido
- **Increment 1 (no working tree, validar):** colunas `total_price_cents` + `price_snapshot`
  no `requests` + migration `0012`. Verificacao:
  ```powershell
  cd X:\QUOARYA\legaltech-aws\apps\api
  $env:DATABASE_URL="postgresql+psycopg://legaltech:legaltech_dev@localhost:5432/legaltech"
  .\.venv\Scripts\alembic.exe upgrade head
  .\.venv\Scripts\alembic.exe current        # deve mostrar 0012_request_price_snapshot (head)
  .\.venv\Scripts\python.exe -m unittest discover -s tests -v   # igual a antes (14 reds, nada NOVO)
  ```
  Se verde: commitar `feat(fin): colunas de snapshot de preco no pedido (FIN-01 fundacao)`.
- **Increment 2 (proximo):** em `create_request`, calcular o estimate (server-side, com overrides
  da org) e gravar `total_price_cents` + `price_snapshot = estimate.model_dump()`; expor no
  response (`LegalRequestSchema`). Verificar persistencia no banco.

## Restricoes de ambiente (importantes)
- O sandbox do agente **nao roda PostgreSQL** e tem **Python 3.10** (projeto exige 3.11+).
  Testes de rota/persistencia/migration sao verificados **no ambiente do usuario** (Windows + venv).
- O agente verifica aqui: logica pura, schema/metadata (sem DB), AST. O usuario roda a suite real.

## Documentos de referencia
- `docs/adr/ADR-0001-autenticacao-producao.md`
- `docs/adr/ADR-0002-unificacao-repositorios-operacionais.md`
- `docs/COGNITO_OPCAO_A_RUNBOOK.md`
- `docs/superpowers/plans/2026-06-24-persist-fluxo-operacional.md`
- `docs/diagnostics/FIN-READY-DIAG.md`
