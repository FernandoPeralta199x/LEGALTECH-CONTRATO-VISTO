# FIN-READY-DIAG — Diagnostico financeiro (Fase 4)

**Data:** 2026-06-24
**Tipo:** diagnostico read-only (nenhuma alteracao de codigo)
**Escopo:** integridade financeira do modulo de pricing e do fluxo de pedido.

## Conformidades (fortes)

- **Dinheiro = integer em centavos.** Nenhum `Float`/`Numeric`/`Double` para dinheiro nos
  models (o unico float e o vetor de embedding em `document_embedding`, legitimo).
  Campos monetarios sao `*_cents: int` (ex.: `base_price_cents`, `price_cents`,
  `modules_total_cents`).
- **Backend calcula o preco.** `POST /api/v1/pricing/estimate` faz o calculo **server-side**
  (`compute_product_base_price`, soma de modulos em `modules_total_cents`). O frontend nao e
  fonte de verdade do valor.
- **RBAC correto.** `pricing:read` para catalogo/estimate/leitura de config; **`pricing:write`
  para mutacao de config** (`PUT /api/v1/pricing/config`).
- **Auditoria sempre presente na alteracao de preco.** O update de config grava `audit_log`
  com snapshot **old/new**, e a factory `get_pricing_admin_service` **sempre injeta** o
  `AuditLogService` (o guard `if self._audit is not None` e apenas para testes). FIN-02 e
  FIN-03 essencialmente satisfeitos.

## Gap central — FIN-01 (alta prioridade)

**O pedido nao congela o preco (sem snapshot na ordem).**

Evidencia: `/estimate` calcula sob demanda e **nunca persiste** o valor; `request`/`case`
nao possuem campo de preco; `requests/service.py:create_request` nao calcula nem grava preco.

Consequencia: o valor de um pedido e **recalculado a partir da config atual**. Se o admin
alterar o preco, **um pedido antigo passaria a refletir o preco novo** — violando a regra
"pedido antigo nao muda com preco novo".

## Recomendacoes priorizadas

1. **FIN-01 (fazer):** persistir um **snapshot de preco na ordem** na criacao —
   `base_price_cents`, `modules_total_cents`, `total_cents` e o detalhamento dos modulos,
   gravados no pedido. Billing/exibicao usam o snapshot, nao o calculo atual.
   Requer: campo(s) no model + migration; gravar no `create_request` a partir do `estimate`.
2. **FIN-02 / FIN-03 (reforco):** ja cobertos (audit + RBAC). Adicionar **teste** de regressao
   garantindo que mutacao de preco gera `audit_log` e exige `pricing:write`.
3. **Frontend (fora do backend):** garantir que a UI usa o snapshot persistido, nao recalcula.

## Conclusao

Financeiro bem construido (centavos inteiros, calculo no backend, RBAC, auditoria). O unico
bloqueador de integridade para staging/prod e o **snapshot de preco no pedido (FIN-01)**.
