# ADR-0002: Unificacao dos repositorios operacionais no PostgreSQL

**Status:** Proposed
**Date:** 2026-06-24
**Deciders:** Fernando Peralta (owner)
**Relacionados:** PERSIST-01/02/03, plano docs/superpowers/plans/2026-06-24-persist-fluxo-operacional.md, C-03

## Context

O fluxo operacional esta meio-migrado (split-brain). `RequestService` persiste em Postgres,
mas `build_operational_repositories()` monta 8 repositorios **todos default Mock**
(`InMemoryOperationalStore`/`_STORE`). Os servicos operacionais (`cases/operational_detail`,
`operational_list`, `provider_results/service`, triagem, reports) chamam
`build_operational_repositories()` **sem sessao `db`**, lendo do store em memoria.

Sintomas (14 testes de rota vermelhos): `ValueError: Case not found`, `TypeError: NoneType`,
e vazamento multi-tenant (`200/201 != 404`) — o store global nao isola por `organization_id`
como o banco isola.

Forcas: seguranca multi-tenant (isolamento real), persistencia apos restart, paridade
single-source-of-truth, e nao quebrar os testes unitarios que dependem do mock.

Restricao de verificacao: o ambiente de quem desenha o ADR nao roda PostgreSQL; cada
incremento e verificado pelo usuario rodando a suite de rota.

## Decision

Introduzir implementacoes **DB-backed** dos protocolos de repositorio operacional, construidas
a partir de uma `Session`, e fazer `build_operational_repositories(db: Session | None = None)`
retornar repos DB-backed quando `db` for fornecido, mantendo Mock quando `db is None`
(preserva testes unitarios). A sessao `db` e injetada pelas dependencias FastAPI
(`get_operational_*_service(db = Depends(get_db))`) e desce ate o builder.

Migracao **incremental por caminho coeso** (nao repo-isolado), porque o agregado do case
depende de varios sub-repos juntos. Toda query DB filtra por `organization_id`; eventos
criticos geram `audit_log`.

## Options Considered

### Option A — Builder com `db` opcional + repos DB-backed incrementais  [ESCOLHIDA]
`build_operational_repositories(db=None)`: com `db`, usa repos DB-backed (existentes +
novos); sem `db`, mock. Threading do `db` pelas dependencias das rotas.

| Dimensao | Avaliacao |
|---|---|
| Complexidade | Media (incremental) |
| Risco | Baixo-Medio (mock preservado para unit tests; um caminho por vez) |
| Isolamento multi-tenant | Resolve (banco filtra por org) |
| Familiaridade | Alta (segue o padrao de `RequestRepository`/`case_bridge`) |

**Pros:** incremental e verificavel passo a passo; mock continua para unit tests; reusa
`OperationalCaseRepository`/`SqlCaseRepository`/repos existentes.
**Cons:** exige implementar DB-backed faltantes (timeline, triage, provider_results, reports).

### Option B — Override das dependencias operacionais so nas rotas
Injetar repos DB nas rotas via `dependency_overrides`/Depends, sem mexer no builder.
**Cons:** logica de fiacao espalhada nas rotas; o builder continua mentindo (default mock);
menos central, mais facil de divergir.

### Option C — Big bang: remover o mock e reescrever servicos direto contra repos DB
**Cons:** mudanca enorme, nao verificavel incrementalmente, alto risco de regressao nos
testes que hoje passam com mock. Rejeitada.

## Trade-off Analysis

A vs B: A centraliza a decisao mock-vs-DB num unico ponto (`build_operational_repositories`),
o que torna a migracao auditavel e reversivel por flag (`db` presente/ausente). B dispersa.
A vs C: C resolveria de uma vez, mas sem verificacao incremental num ambiente sem DB e
temerario. A permite avancar caminho a caminho, cada um verificado pelo usuario.

## Consequences

**Fica mais facil:** isolamento multi-tenant real; persistencia apos restart; remover o
`_STORE` do fluxo real (C-03); paridade de fonte de verdade.
**Fica mais dificil:** manter dois caminhos (mock/DB) durante a transicao; implementar os
repos DB-backed faltantes; garantir filtro por org em cada query nova.
**A revisitar:** quando todos os caminhos estiverem em DB, remover o mock do fluxo de
producao (manter so para unit tests) e simplificar o builder.

## Action Items (ordem incremental, cada um verificado pelo usuario)
1. [ ] Infra: `build_operational_repositories(db=None)` + threading do `db` nas dependencias das rotas (sem trocar default ainda).
2. [ ] Caminho de leitura do agregado do case (case + parties + documents + timeline) em DB-backed; verificar `test_operational_backend_routes` de leitura/isolamento.
3. [ ] Triagem + provider_results em DB-backed; verificar `test_triage_provider_results`.
4. [ ] Reports em DB-backed; verificar `test_report_generation`.
5. [ ] Confirmar suite de rota verde; remover dependencia de `_STORE` do fluxo real.
6. [ ] Garantir `organization_id` em toda query e `audit_log` nos eventos criticos (PERSIST-06).
