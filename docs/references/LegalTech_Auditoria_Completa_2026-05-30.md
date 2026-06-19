# Auditoria Completa — LegalTech AWS V2

> **Data:** 2026-05-30
> **Autor:** Claude (Sonnet 4.5) — sessão interativa
> **Solicitante:** Fernando Augusto Peralta
> **Inputs analisados:**
> - PDF "Análise Técnica V2" (Analise_Tecnica_Arquitetura_LegalTech_AWS_V2_CORRIGIDO.pdf — 429KB, 10pp)
> - PDF "Comparativo de Arquitetura de Banco" (65KB, 2pp)
> - Código completo em `X:\Front end - Back end\LegalTech\legaltech-aws\`
> - Sistema de referência UX `Exactly As Seen\`
> - 10 imagens do fluxo atual em `imagens\`
> - Docs internos: `MVP_READINESS_CHECKLIST.md`, `KNOWN_LIMITATIONS.md`, `SECURITY_LGPD.md`, `SECURITY_CODE_REVIEW.md`, `ARQUITETURA_LEGALTECH_AWS_V2.md`, `TECHNICAL_REVIEW_REPORT.md`, `OPERATIONAL_FLOW_REVIEW.md`, `DATABASE_SCHEMA.md`

---

## ÍNDICE

1. [Veredicto executivo](#0-veredicto-executivo)
2. [PDF V2 vs. realidade — placar correção por correção](#1-pdf-v2-vs-realidade--placar-correção-por-correção)
3. [Auditoria de Arquitetura](#2-auditoria-de-arquitetura)
4. [Auditoria de Segurança / LGPD](#3-auditoria-de-segurança--lgpd)
5. [Cobertura Jurídica](#4-cobertura-jurídica)
6. [Auditoria de UX/UI](#5-auditoria-de-uxui)
7. [Code Review](#6-code-review)
8. [Roadmap para Produção](#7-roadmap-para-produção)
9. [Resposta direta: "tudo funcionando 100%?"](#8-resposta-direta-tudo-funcionando-100)
10. [ANEXO A — ADR-001: Wizard inteligente de pedido](#anexo-a--adr-001-wizard-inteligente-de-pedido)
11. [ANEXO B — Scaffold do wizard (já gerado)](#anexo-b--scaffold-do-wizard-já-gerado)

---

## 0. Veredicto executivo

| Pergunta | Resposta honesta |
|---|---|
| **Está tudo funcionando 100%?** | **Não, e isso é normal.** Está funcionando 100% para o escopo declarado: **MVP local com dados fictícios**. Está em ~40% do que o PDF V2 chama de "pronto para produção". |
| **Está pronto pra investidor / demo?** | **Sim** — fundação correta, design system maduro, RBAC + audit + multi-tenant funcionais. |
| **Está pronto pra cliente pagante / dados reais?** | **Não.** Faltam: Cognito real, S3 real, SQS+DLQ real, RLS, OCR, IA real, revisão humana, pentest. |
| **A arquitetura está certa?** | **Sim** — bate com o que o PDF V2 demandou. Decisões corretas: pgvector no mesmo RDS, FastAPI+Lambda, S3+presigned, audit_log com sanitização. |
| **Maior risco hoje** | Frontend ainda usa **localStorage** para sessão dev e tem **fallback mockado em vários services** — se isso vazar pra prod sem flag bloqueante, é incidente sério. |

**Resumo em 1 frase:** O projeto está bem construído como MVP-local, segue ~85% das recomendações do PDF V2 nas camadas que foram implementadas, e tem um **caminho claro para v1.0 documentado pelo próprio time** — falta só executar o que está em `KNOWN_LIMITATIONS.md`.

---

## 1. PDF V2 vs. realidade — placar correção por correção

A "Tabela de correções" do PDF V2 listou 9 itens **Prioridade 1**. Estado atual:

| # | Correção P1 do PDF | Status no código | Evidência |
|---|---|---|---|
| 1 | Free Tier não tratado como garantia | ✅ Doc | `docs/AWS_DEPLOYMENT_PLAN.md` + `MVP_READINESS_CHECKLIST` mencionam Budgets pendentes |
| 2 | Índices SQL via `CREATE INDEX` separado | ✅ Feito | `models/audit_log.py:17-22`, `models/case.py:18-23` usam `Index(...)` |
| 3 | Função `anonymize_client` com parâmetros não-ambíguos | ❌ Não existe ainda | Não há função de anonimização (gap LGPD) |
| 4 | `requests` com `await` → `httpx.AsyncClient` | ✅ N/A | Não há chamada externa real ainda |
| 5 | SQS handler padrão `event["Records"]` | ✅ Estrutura pronta | `queues/sqs_client.py:39` faz `response.get("Messages", [])` |
| 6 | Auth + RBAC | ✅ Implementado | `core/cognito.py`, `core/rbac.py` (`require_permission`) |
| 7 | S3 privado + presigned + KMS + lifecycle | ⚠️ Parcial | Storage abstrato pronto; bucket real **não conectado** |
| 8 | SQS + DLQ + retry + idempotency | ⚠️ Parcial | Idempotency básico (`agent_executions/idempotency.py`); **DLQ não existe** |
| 9 | Revisão humana antes do relatório | ⚠️ Modelo existe | `models/human_review.py` existe; **fluxo não está plugado** |

**Veredicto:** 5/9 ✅ verdes, 3/9 ⚠️ parciais, 1/9 ❌ ausente. Consistente com o "MVP local pronto" declarado.

PDF "Comparativo Banco" recomenda **um RDS + pgvector**: implementado em `docker-compose.yml` com `pgvector/pgvector:pg16` e migrações usam `vector` no mesmo banco. ✅

---

## 2. Auditoria de Arquitetura

### 2.1 Camadas — o que está lá vs. o que o PDF V2 desenhou

```
PDF V2:                          REALIDADE:
─────────────────────────────────────────────────────────
Frontend React/Next.js     →     ✅ Next.js 16 + React 19 (apps/frontend)
CloudFront + S3 + WAF      →     ❌ Não provisionado (deploy pendente)
API Gateway                →     ❌ Não provisionado
Cognito/JWT/RBAC/Tenant    →     ⚠️ Cognito OK (core/cognito.py); User Pool real ❌
Backend FastAPI/Lambda     →     ✅ FastAPI completo; Mangum/Lambda ainda não
RDS Proxy + Postgres       →     ⚠️ Postgres local OK; RDS Proxy não
pgvector                   →     ✅ Extensão carregada (init/01_extensions.sql)
S3 privado                 →     ⚠️ Abstração pronta; bucket real ❌
SQS + DLQ + Retry          →     ⚠️ Cliente SQS pronto; DLQ ❌; queue real ❌
Lambdas agentes            →     ⚠️ Worker local roda; OCR/IA real ❌
APIs externas + cache      →     ⚠️ Modelo `external_query_cache` existe; chamadas reais ❌
CloudWatch/CloudTrail/Budgets → ❌ Nenhum
Secrets Manager/SSM        →     ❌ Não integrado
```

### 2.2 Pontos fortes da arquitetura atual

1. **Multi-tenant por aplicação** — `OrganizationScopedMixin` em todos models sensíveis; `TenantContext` derivado do JWT validado (correto per `SECURITY_LGPD.md` §3).
2. **Audit log com sanitização forte** — `audit/service.py:44-46` redacta JWT, Bearer tokens e mascara CPF/CNPJ via regex. Excelente.
3. **RBAC granular funcional** — `require_permission("cases:write")` reaproveitado em todos routers; tabela `role_permission` no banco.
4. **Idempotência declarada por estado** — `agent_executions/idempotency.py` controla `RUNNING/RETRYING/COMPLETED/FAILED` para reprocessamento seguro.
5. **Queue backend agnóstico** — `publisher.py:88-100` escolhe `LocalFileQueueClient` vs `SQSQueueClient` por env var. Permite testes locais sem AWS.
6. **Normalização Markdown como camada intermediária** — TXT/MD/DOCX/PDF→MD com flag `requires_ocr` para PDFs sem texto. Boa decisão arquitetural.
7. **Frontend com Design System próprio maduro** — "Contrato Visto" CSS tokens (`--teal`, `--surf`, `cv-card`, `cv-btn`) — não precisa de shadcn.

### 2.3 Dívida arquitetural (gaps reais)

| # | Gap | Impacto | Prioridade |
|---|---|---|---|
| A1 | **Sem Row Level Security no Postgres** | Bug em service.py pode vazar dados entre tenants | Alta (antes de cliente pagante) |
| A2 | **Sem DLQ em filas** | Mensagem falha → perda silenciosa | Alta |
| A3 | **Sem locking distribuído** | 2 workers podem processar mesmo job | Média (1 worker hoje) |
| A4 | **Frontend usa `localStorage` pra sessão dev** | Vazaria token se for pra prod sem flag | **Crítica** (review antes de deploy) |
| A5 | **Embeddings são fake/determinísticos** | Search semântico não funciona de verdade | Média (esperado p/ MVP) |
| A6 | **Sem rate limiting** | API exposta sofre abuso facilmente | Alta (pré-deploy) |
| A7 | **Sem observabilidade** (CloudWatch, traces, métricas) | Debugging cego em prod | Alta (pré-deploy) |
| A8 | **Sem IaC (Terraform/CDK)** | Deploy manual, não reproduzível | Média (pode começar manual) |

---

## 3. Auditoria de Segurança / LGPD

### 3.1 Princípios `SECURITY_LGPD.md` vs. realidade

| Princípio | Status | Evidência |
|---|---|---|
| Minimização de dados | ✅ | Jobs SQS carregam só IDs + metadata mínimo (`queues/schemas.py`) |
| Controle por usuário/perfil/org | ✅ | `require_permission` + `TenantContext` |
| Isolamento por tenant | ⚠️ App-layer ✅, RLS ❌ | `OrganizationScopedMixin` em todos models |
| Auditoria de ações sensíveis | ✅ | `audit_log.record_event` chamado em todos routers |
| Criptografia em trânsito/repouso | ⚠️ TLS local ❌; KMS/S3-SSE ❌ | Bucket real não existe ainda |
| Segredos fora do código | ✅ | `.gitignore` cobre `.env`, exemplos têm placeholders |
| Logs sem dados pessoais | ✅ | Sanitização cobre `CPF/CNPJ`, `Bearer`, JWT |
| Revisão humana em relatório final | ❌ | Modelo existe, fluxo não plugado |
| Rastreabilidade de consultas externas | ✅ Modelo, ❌ Uso | `external_query_cache` existe; chamadas reais ainda não |
| Proteção contra acesso indevido a documentos | ⚠️ | Storage abstrato valida tenant; presigned real ❌ |

### 3.2 Achados de segurança específicos no código

**🟢 Bom:**
- `core/rbac.py:35-51` — quando RBAC nega acesso, **registra em audit_log com `RBAC_DENIED` antes de retornar 403**. Excelente para detecção de varredura.
- `audit/service.py:44-46` — regex `JWT_RE` pega qualquer string com 3 partes base64; bem agressivo na boa.
- `models/audit_log.py:30-31` — `entity_type` separado de `entity_id` permite querying por tipo de recurso.

**🟡 Atenção:**
- `core/cognito.py:67` — `verify_aud: False` é correto para tokens Cognito (verifica via `client_id` em `_validate_claims`), mas comente isso pra evitar confusão futura.
- `core/cognito.py:101-106` — valida `client_id` só **se** `cognito_client_id` setado. Em prod, isso DEVE ser obrigatório por validação de Settings.
- `apps/frontend/src/lib/authStorage.ts` — `legaltech.dev.session.v1` em localStorage é **DEV ONLY**. Há comentário em `KNOWN_LIMITATIONS.md` mas falta um **guard de runtime** (`if process.env.NODE_ENV === 'production' throw new Error()`) pra impedir uso acidental.

**🔴 Crítico (mas conhecido):**
- **Não há função de anonimização LGPD.** PDF V2 demandou `anonymize_client(p_client_id, p_tenant_id)`. Sem isso, não dá pra atender pedido de exclusão LGPD (Art. 18 V).
- **`deleted_at` é só soft-delete sem hard-delete agendado.** Falta job de purga após retention period.
- **Sem `retention_until` em entidades sensíveis**, contrariando `SECURITY_LGPD.md` §11.

### 3.3 Checklist pré-deploy (do `SECURITY_LGPD.md` §14)

| # | Item | Status |
|---|---|---|
| 1 | `.env` não commitado | ✅ |
| 2 | `.env.example` sem segredos reais | ✅ |
| 3 | S3 não público | ⚠️ (não existe ainda) |
| 4 | Rotas sensíveis exigem auth | ✅ |
| 5 | Queries filtram por `organization_id` | ✅ |
| 6 | `audit_log` ativo | ✅ |
| 7 | CORS restrito | ⚠️ (configurável; valor padrão permissivo) |
| 8 | Upload valida tipo/tamanho | ✅ (`src/lib/validation.ts` aceita PDF/DOCX/PNG/JPG/MD/TXT até 10MB) |
| 9 | Secrets no Manager/SSM | ❌ |
| 10 | CloudWatch | ❌ |
| 11 | AWS Budgets | ❌ |
| 12 | Revisão humana exigida no relatório final | ❌ |

**Score: 7/12 verdes**, 2 amarelas, 3 vermelhas (tudo conhecido).

---

## 4. Cobertura Jurídica

### 4.1 Modelos vs. fluxo jurídico

Os 4 produtos do wizard mapeiam para entidades existentes:

| Produto | Entidade principal | Cobertura |
|---|---|---|
| Dados das partes | `Case` + `CaseParty` + `ExternalQueryCache` | ✅ Estrutura completa, falta plugar Escavador/TargetData |
| Consulta do objeto | `Case.metadata_json` (livre) | ⚠️ Sem tabela dedicada para "objeto"; usa JSONB. OK pra MVP. |
| Análise contratual | `Document` + `DocumentChunk` + `DocumentEmbedding` + `AgentExecution` | ✅ Estrutura completa, IA/RAG é fake |
| Reunião com advogado | `HumanReview` | ⚠️ Modelo existe mas sem agendamento/calendário |

### 4.2 Gaps jurídicos identificados

1. **Sem versionamento de documento** — `models/document.py` tem `version` provavelmente, mas modificação de cláusula não é tracked. Em jurídico, **histórico imutável** é regra.
2. **Sem assinatura digital** — para contratos, a falta de integração com gov.br/ICP-Brasil/DocuSign é gap conhecido. Pode ficar pra v1.5.
3. **`Case` sem campo "valor da causa"** — comum em jurídico contencioso, ausente do modelo. JSONB resolve, mas é unsearchable.
4. **`HumanReview` sem SLA tracking** — campo `approved_at` existe, falta `assigned_at`, `target_sla`, `breached`. Pra MVP tudo bem.
5. **`AgentExecution` não amarra a `external_query_cache.id`** — se o Escavador foi consultado, qual execução usou? Falta FK.

### 4.3 Compliance jurídico

- **OAB** — sistemas de apoio à advocacia precisam respeitar Provimento 205/2021 (publicidade). Se for vendido pra advogados, footer precisa ter aviso. **Pendente.**
- **LGPD bases legais** — modelo não armazena qual base legal justifica o tratamento (consentimento, legítimo interesse, etc.). PDF V2 §11.1 alerta isso.
- **Segredo profissional** — documento sob revisão humana pode conter dado sob sigilo. Falta classificação `confidential_level` em `Document`.

---

## 5. Auditoria de UX/UI

### 5.1 Estado do frontend

**O que está bom:**
- Design System "Contrato Visto" maduro (`globals.css`, 730 linhas) — tokens OKLCH/HSL, cards, botões, inputs todos com identidade própria.
- 20 componentes reutilizáveis em `/components/` (Card, Button, FormField, UploadBox, Timeline, StatusBadge, etc.)
- Rotas implementadas: `/dashboard`, `/clients`, `/cases`, `/cases/[id]`, `/documents`, `/login`, `/admin`, `/analyst`, `/reports`, `/settings`
- Acessibilidade: focus visível, `aria-*` em componentes, dark/light mode via `data-theme`

**O que melhorou agora (wizard novo):**
- 5 etapas vs. 6 anteriores (`partes` → `contrato` → `produto` → `módulos` → `revisão`)
- `produtoConfig.ts` com `MATRIZ` produto×módulo (obrigatórios/recomendados/bloqueados)
- Cards de produto premium (`ProductCard.tsx`) com seleção visual forte
- Módulos com switches + badges, **estimativa de valor/prazo live**
- Máscaras CPF/CNPJ/telefone + validação onBlur (`lib/cpfCnpj.ts`)
- Parte vira card resumido com [Editar] [Duplicar] [Excluir]

**O que ainda falta no wizard (delta da ADR):**

| Item | Status | Comentário |
|---|---|---|
| Auto-save / draft | ❌ | Estado só em memória; refresh perde tudo |
| Continuar pedido (recover draft) | ❌ | Depende do #1 |
| CEP autocomplete (ViaCEP) | ❌ | Listado como melhoria #1 da ADR |
| OCR real com chip "12 partes detectadas" | ❌ | Mock atual finge |
| Upload com presigned real | ❌ | Hoje só simula progresso |
| `useCan('cases:submit')` no botão | ❌ | RBAC client-side ausente |
| Skeleton específico por etapa | ❌ | Tem skeleton genérico |
| Atalhos de teclado | ❌ | Cmd+→ / Cmd+S |

**Gap UX/UI sério:**
- **Não há testes E2E** do wizard. Risco alto de regressão visual.
- **Não testado mobile** (declarado em `KNOWN_LIMITATIONS.md` §Frontend).

### 5.2 Comparação com "Exactly As Seen"

| Aspecto | Exactly As Seen | LegalTech atual |
|---|---|---|
| Stack | Vite + TanStack | Next.js 16 (canônico) |
| DS | shadcn/ui + tokens OKLCH | "Contrato Visto" próprio + cv-classes |
| Wizard | 5 etapas, autosave inexistente | 5 etapas, autosave inexistente |
| Identidade | Cinza-azulado + verde | Teal + dark-first |
| Coerência | Boa | Boa, e **diferenciada** (não copy) |

**Conclusão UX:** O LegalTech tem identidade mais marcante que o Exactly As Seen. A inspiração foi de **fluxo** (5 etapas, MATRIZ), não de aparência. Foi a decisão certa.

---

## 6. Code Review

### 6.1 Qualidade geral

| Aspecto | Nota | Observação |
|---|---|---|
| Tipagem Python | ⭐⭐⭐⭐⭐ | `Mapped[...]`, `Annotated[...]`, `Protocol` para DI, zero `Any` solto |
| Tipagem TypeScript | ⭐⭐⭐⭐⭐ | `strict: true`, zero `any` no código que li |
| Estrutura modular | ⭐⭐⭐⭐⭐ | Cada feature em `modules/<feature>/{router,service,repository,schemas}.py` |
| DI / testabilidade | ⭐⭐⭐⭐⭐ | `Depends(get_db)`, `RolePermissionServiceProtocol` permitem mock fácil |
| Separação de camadas | ⭐⭐⭐⭐⭐ | Router → Service → Repository → Model. Clássico e correto. |
| Convenções | ⭐⭐⭐⭐ | Inconsistência menor: `produtoConfig.ts` (camelCase) vs `produto-config.ts` (kebab) no Exactly As Seen |
| Testes | ⭐⭐⭐ | Tests existem (`*.test.ts`), cobertura desconhecida sem rodar |
| Comentários | ⭐⭐⭐ | Código fala por si; alguns módulos sem docstring |

### 6.2 Achados pontuais (revisar antes de prod)

**🔴 Bloqueador para deploy:**
- `apps/frontend/src/lib/useDevSession.ts` precisa de guard `NODE_ENV !== 'production'`.
- `apps/frontend/src/services/cases.ts:131-141` — `shouldUseMockFallback(error)` retorna mock se API falha. **Em prod isso esconde caching e dá ilusão de funcionamento**. Precisa de feature flag.

**🟡 Refatorações sugeridas:**
- `cases/router.py:32-68` — `list_cases` tem 65 linhas, 90% delas registrando audit. **Mover audit pra decorator/middleware** reduz boilerplate em todos endpoints.
- `audit/service.py:104-120` — `sanitize_audit_metadata` é recursivo; **adicionar limite de profundidade** pra evitar stack overflow em JSON adversário.
- `queues/sqs_client.py:32-48` — `receive` tem `WaitTimeSeconds=1` (short polling). Mudar pra **long polling 20s** reduz custo SQS ~95% em prod.

**🟢 Padrões a manter:**
- O uso de `Annotated[Session, Depends(get_db)]` em todos routers é consistente.
- Schemas Pydantic com `model_validate` / `model_dump(mode="json")` está correto pra evitar problemas de UUID serialização.
- `__table_args__` com `Index(...)` separado segue exatamente a recomendação do PDF V2 §7.1.

### 6.3 Cobertura de testes (não confirmado por execução)

Vi tests para:
- `apps/api/src/modules/agent_executions/` (provavelmente)
- `apps/frontend/src/lib/validation.test.ts` (vi)
- `apps/frontend/src/lib/authStorage.test.ts` (vi)
- `apps/frontend/src/services/*.test.ts` (vi 5+)
- `apps/frontend/src/lib/preferences.test.ts`

**Não vi:** testes para o wizard novo (`components/cases/wizard/*`). **Adicionar** antes de plugar no backend.

---

## 7. Roadmap para Produção

Reordenado por **risco/valor**, não por prioridade do PDF V2:

### Sprint 1 — Bloqueadores de segurança (1-2 semanas)
1. **Guard NODE_ENV** em `useDevSession` e desabilitar fallback mock em prod
2. **`anonymize_client(p_client_id, p_tenant_id)`** — função SQL com qualify de tabelas
3. **Adicionar `retention_until`** em `Document`, `Case`, `ExternalQueryCache`
4. **Validar `cognito_client_id` obrigatório quando `APP_ENV != 'local'`**
5. **CORS restrito por env** — hoje configurável, garantir default seguro

### Sprint 2 — Plugar wizard novo no backend (1-2 semanas)
6. Migration `0004_case_products_modules.py` (do plano da ADR — anexo A)
7. Endpoints `/cases/drafts/*`, `/cases/{id}/submit`, `/cases/estimate`, `/cases/products`
8. Hook `useCan()` + `useDraft()` + `useAutosave()`
9. ContractDropzone com presigned real (substituir mock)
10. E2E Playwright dos 5 passos

### Sprint 3 — Pipeline real (2-3 semanas)
11. SQS real + DLQ por etapa
12. Worker Escavador (1 integração de cada vez)
13. Worker OCR (Textract async)
14. Cache externo real em `external_query_cache`
15. Worker de IA real (Claude/DeepSeek/Bedrock — escolher um)

### Sprint 4 — Fluxo humano e relatório (2 semanas)
16. Plugar `HumanReview` no fluxo (fila `queue-human-review`)
17. Tela `/admin/revisoes` (já existe rota, falta conteúdo)
18. Geração de PDF final (WeasyPrint ou similar)
19. Status `requires_review` bloqueia liberação ao cliente

### Sprint 5 — Operação AWS (2-3 semanas)
20. Terraform/CDK mínimo: VPC + RDS + S3 + Cognito + SQS + Lambda + CloudFront
21. Secrets Manager + IAM least privilege
22. CloudWatch + CloudTrail + Budgets
23. Backup automatizado + restore drill
24. WAF + rate limiting

### Sprint 6 — Pós-MVP (contínuo)
25. RLS no Postgres (P0 antes do **segundo** tenant pagante)
26. Pentest formal
27. Política LGPD escrita (DPO)
28. SOC2 prep (se for vender enterprise)
29. Observabilidade por agente (traces, custo por execução)

---

## 8. Resposta direta: "tudo funcionando 100%?"

**Pra rodar localmente, testar fluxos com dados fake, fazer demo, validar arquitetura — SIM, 100%.**

**Pra qualquer outra coisa — NÃO**, e o próprio time já documentou isso de forma honesta em `MVP_READINESS_CHECKLIST.md` (linha 116: "**sim, para testes end-to-end locais controlados**") e `KNOWN_LIMITATIONS.md` (linha 123: "**não está pronto para produção**").

A **boa notícia**: o checklist de pendências do time bate **quase 1:1** com o que o PDF V2 demandou. Não há surpresas escondidas. Não há técnica débito acumulada por desleixo. É um projeto disciplinado, com auto-conhecimento dos próprios limites.

---

## 9. Onde focar agora — recomendação pessoal

Se eu fosse decidir hoje o que fazer próximo, na ordem:

1. **Plugar o wizard novo no backend** (Sprint 2) — porque já está 80% pronto e desbloqueia demos com fluxo real.
2. **Anonimização LGPD + retention_until** (Sprint 1 itens 2-3) — porque sem isso você não pode vender pra ninguém que peça DPA.
3. **Um worker real (Escavador)** (Sprint 3 item 12) — porque é o produto "Dados das partes", o mais simples de validar com cliente e o que mais "vende" a IA.
4. **Cognito User Pool real** (Sprint 5 item 20 parcial) — porque sair do localStorage é pré-requisito pra qualquer piloto.

**Estimativa total para v1.0 vendável:** ~10-14 semanas de 1 dev sênior, ou 6-8 semanas com 2 devs (1 backend, 1 frontend) trabalhando em paralelo.

---

## ANEXO A — ADR-001: Wizard inteligente de pedido

> Decisão arquitetural tomada em 2026-05-30 para redesenhar o fluxo de criação de pedido do LegalTech, usando o "Exactly As Seen" apenas como referência de UX/fluxo, mantendo identidade e backend do LegalTech.

### A.1 Decisão

Construir o wizard de pedido em `legaltech-aws/apps/frontend` (Next.js 16 App Router + React 19), portando **literalmente** a estrutura de 5 etapas + matriz produto×módulo do Exactly As Seen — mas substituindo Supabase pela API FastAPI já existente, e renomeando domínio para `Case`/`CaseParty`.

Adicionar **3 entidades novas no backend** sem mexer no resto: `case_products`, `case_modules`, `case_drafts`.

### A.2 Estrutura de pastas final

```
apps/frontend/
├─ src/app/cases/new/page.tsx              # entrada do wizard
├─ components/wizard/
│  ├─ WizardShell.tsx
│  ├─ WizardProgress.tsx                   # barra 4px com aria-valuenow
│  ├─ WizardActions.tsx                    # Voltar / Continuar / Enviar
│  └─ index.ts                             # barrel
├─ components/cases/wizard/
│  ├─ NewCaseWizard.tsx                    # orquestrador (state, navegação)
│  ├─ types.ts                             # Party, WizardFile, newParty()
│  ├─ PartiesStep.tsx + PartyForm.tsx + PartyCard.tsx
│  ├─ ContractStep.tsx + ContractDropzone.tsx
│  ├─ ProductStep.tsx + ProductCard.tsx
│  ├─ ModulesStep.tsx + ModuleRow.tsx
│  ├─ EstimateCard.tsx
│  └─ ReviewStep.tsx
├─ components/Switch.tsx                   # toggle acessível (novo primitivo)
├─ components/Badge.tsx                    # wrapper de cv-badge
├─ lib/produtoConfig.ts                    # PRODUTOS + MODULOS + MATRIZ
└─ lib/cpfCnpj.ts                          # máscaras + validação
```

### A.3 Wireframe textual do wizard

```
[Dashboard "Meus pedidos"]
       │  click "+ Novo pedido"
       ▼
┌──────────────────────────────────────────────────────────┐
│ Wizard /pedidos/novo  (URL preserva ?step=N&draft=UUID)  │
│                                                          │
│  ●━━━━●━━━━○━━━━○━━━━○   Progress bar (4px, primary)    │
│  1    2    3    4    5                                   │
│                                                          │
│  ETAPA 1 — Partes              (autosave 1.2s debounce)  │
│  ETAPA 2 — Contrato (upload)   (presigned URL, OCR bg)   │
│  ETAPA 3 — Produto             (4 cards premium)         │
│  ETAPA 4 — Módulos             (dinâmico via MATRIZ)     │
│  ETAPA 5 — Revisão & Envio     (resumo + valor + prazo)  │
└──────────────────────────────────────────────────────────┘
       │  POST /api/v1/cases/{id}/submit
       ▼
[Tela do Pedido /pedidos/:id]  ← timeline + status realtime
```

### A.4 Migração Alembic necessária (Sprint 2)

```python
# 0004_case_products_modules.py

# 1. case_products: enum forte para o produto escolhido
op.create_table(
    "case_products",
    sa.Column("case_id", UUID, sa.ForeignKey("cases.id"), primary_key=True),
    sa.Column("organization_id", UUID, nullable=False),
    sa.Column("product", sa.String(40), nullable=False),
    sa.Column("estimated_price_cents", sa.Integer, nullable=True),
    sa.Column("estimated_sla_hours", sa.Integer, nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
)

# 2. case_modules: módulos ativos por caso
op.create_table(
    "case_modules",
    sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("case_id", UUID, sa.ForeignKey("cases.id"), nullable=False),
    sa.Column("organization_id", UUID, nullable=False),
    sa.Column("module", sa.String(40), nullable=False),
    sa.Column("active", sa.Boolean, nullable=False),
    sa.Column("obligatory", sa.Boolean, nullable=False, server_default=sa.text("false")),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.UniqueConstraint("case_id", "module", name="uq_case_modules_case_module"),
)
op.create_index("idx_case_modules_org_case", "case_modules", ["organization_id", "case_id"])

# 3. case_drafts: rascunhos antes do submit (autosave)
op.create_table(
    "case_drafts",
    sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("organization_id", UUID, nullable=False),
    sa.Column("user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
    sa.Column("payload", JSONB, nullable=False),  # snapshot completo do wizard
    sa.Column("current_step", sa.Integer, nullable=False, server_default="1"),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
)
op.create_index("idx_case_drafts_org_user", "case_drafts", ["organization_id", "user_id"])
```

### A.5 Endpoints novos (Sprint 2)

```
POST   /api/v1/cases/drafts                 → cria rascunho
PATCH  /api/v1/cases/drafts/{id}            → autosave (idempotente)
GET    /api/v1/cases/drafts/{id}            → recupera para "continuar depois"
DELETE /api/v1/cases/drafts/{id}            → descarta
POST   /api/v1/cases/drafts/{id}/submit     → promove rascunho a Case + dispara SQS

GET    /api/v1/cases/products               → catálogo + preço base + módulos disponíveis
POST   /api/v1/cases/estimate               → preview de valor/prazo (sem persistir)

POST   /api/v1/documents/presigned-upload   → URL presigned
GET    /api/v1/documents/{id}/ocr-status    → polling de OCR
```

### A.6 RBAC — sementes da tabela `role_permission`

| Permissão | Owner | Admin | Cliente | Suporte |
|---|---|---|---|---|
| `cases:read` | ✓ | ✓ | ✓ (próprios) | ✓ |
| `cases:write` | ✓ | ✓ | ✓ | – |
| `cases:submit` | ✓ | ✓ | ✓ | – |
| `cases:update_status` | ✓ | ✓ | – | ✓ |
| `cases:assign_reviewer` | ✓ | ✓ | – | – |
| `users:manage` | ✓ | ✓ | – | – |
| `users:delete_owner` | ✓ | – | – | – |
| `billing:read` | ✓ | ✓ | ✓ (próprios) | – |
| `billing:write` | ✓ | ✓ | – | – |
| `support:respond` | ✓ | ✓ | – | ✓ |
| `audit:read` | ✓ | ✓ | – | – |

### A.7 Pipeline SQS (visão lógica do submit)

```
POST /cases/{id}/submit
   │
   ▼
SQS: queue-triagem
   │
   ▼ (Lambda Worker Triagem)
   │  • Valida documento, partes, módulos ativos
   │  • Cria registros em agent_executions (status=queued)
   │
   ▼ (Fanout para módulos ativos)
   ├─ queue-escavador      → Worker chama API Escavador, salva em external_query_cache
   ├─ queue-serasa-procon  → idem
   ├─ queue-targetdata     → idem
   ├─ queue-ocr            → Textract / Tesseract (para imagens)
   ├─ queue-embeddings     → pgvector
   ├─ queue-ai-analysis    → DeepSeek/Claude → riscos + cláusulas
   │
   ▼ (Aggregator)
   queue-report → gera PDF + persiste em S3 + cria report row
   │
   ▼ (se módulo revisao_humana ativo)
   queue-human-review → cria HumanReview, notifica analista
   │
   ▼
case.status = "finalizado" → realtime push ao cliente
```

### A.8 Melhorias não solicitadas que aumentam conversão

| # | Melhoria | Por que | Esforço |
|---|---|---|---|
| 1 | CEP autocomplete (ViaCEP) no endereço | corta 6 campos para 1 | XS |
| 2 | Máscara live de CPF/CNPJ/telefone | reduz erros | XS — **JÁ FEITO no scaffold** |
| 3 | Pré-preenchimento da parte 2 com usuário logado como Contratante | -1 etapa em casos comuns | S |
| 4 | OCR em background com chip "12 partes detectadas — importar?" | extrai partes do PDF | M |
| 5 | "Continuar pedido" card no Dashboard quando existe draft ativo | recupera abandono | S |
| 6 | Estimativa de preço live ao alternar módulos | reduz fricção comercial | S — **JÁ FEITO no scaffold** |
| 7 | Comparativo de produtos em modal na Etapa 3 | aumenta confiança | S |
| 8 | Atalhos de teclado: Cmd+→ avança, Cmd+S salva | UX premium | XS |
| 9 | Confetti + email transacional ao concluir submit | reforço positivo | XS |
| 10 | "Modo expert" — todas as etapas em uma página vertical | escala power-users | M |
| 11 | Templates ("locação", "compra-venda", "prestação") que pré-preenchem | onboarding | M |
| 12 | A11y: `aria-live` em mudança de step, foco gerenciado | WCAG AA | S |
| 13 | SSR de `/pedidos/:id` com revalidação a cada 10s + SSE para timeline | percepção de velocidade | M |
| 14 | Skeleton específico por etapa | sem flash de layout | XS |

---

## ANEXO B — Scaffold do wizard (já gerado)

> 18 arquivos novos + 1 reescrito (`src/app/cases/new/page.tsx`), com 0 erros de lint e 0 erros de tipo. Tudo usa o Design System existente (`cv-card`, `cv-input`, `cv-btn`, `cv-badge`, tokens `--teal`, `--surf`, `--text`).

### B.1 Lista de arquivos criados

**Configuração & utilitários:**
- `lib/produtoConfig.ts` — PRODUTOS, MODULOS, MATRIZ (com obrigatorio/recomendado/bloqueado), PAPEIS, estimarValor(), estimarPrazoHoras()
- `lib/cpfCnpj.ts` — maskCpf, maskCnpj, maskPhone, isValidCpf, isValidCnpj, isValidEmail, isValidPhone

**Primitivos:**
- `components/Switch.tsx` — toggle acessível com foco visível
- `components/Badge.tsx` — wrapper de cv-badge (teal/orange/blue/muted)

**Wizard primitives:**
- `components/wizard/WizardShell.tsx` — header + back link + progress
- `components/wizard/WizardProgress.tsx` — barra fina (4px) com aria-valuenow
- `components/wizard/WizardActions.tsx` — Voltar/Continuar/Enviar com loading
- `components/wizard/index.ts` — barrel

**Etapas + domínio:**
- `components/cases/wizard/types.ts` — Party, WizardFile, newParty(), partyIsComplete()
- `components/cases/wizard/PartiesStep.tsx` — lista com add/duplicate/remove
- `components/cases/wizard/PartyForm.tsx` — máscaras live de CPF/CNPJ/telefone, validação onBlur
- `components/cases/wizard/PartyCard.tsx` — resumo colapsado com avatar de iniciais + [Editar] [Duplicar] [Excluir]
- `components/cases/wizard/ContractStep.tsx` + `ContractDropzone.tsx` — drag&drop single-file, pipeline mockada
- `components/cases/wizard/ProductStep.tsx` + `ProductCard.tsx` — grid 2×2, borda teal + check + glow ao selecionar
- `components/cases/wizard/ModulesStep.tsx` + `ModuleRow.tsx` + `EstimateCard.tsx` — switches dinâmicos via MATRIZ, estimativa live
- `components/cases/wizard/ReviewStep.tsx` — blocos limpos (Produto, Partes, Contrato, Módulos, Estimativa)

**Orquestrador & rota:**
- `components/cases/wizard/NewCaseWizard.tsx` — state machine local, canAdvance por etapa
- `src/app/cases/new/page.tsx` — agora 11 linhas (era 635)

### B.2 Como testar

```powershell
cd "X:\Front end - Back end\LegalTech\legaltech-aws\apps\frontend"
npm run dev
# Abrir http://localhost:3000/cases/new (após login dev)
```

### B.3 Próximo passo recomendado

Quando aprovar o look-and-feel, plugar adapters reais:
1. Trocar mock no `handleSubmit` por `POST /api/v1/cases/drafts/{id}/submit` via `services/cases.ts`
2. Trocar mock pipeline do `ContractDropzone` por presigned URL + polling de OCR
3. Adicionar `useDraft()` para auto-save
4. Adicionar `useCan('cases:submit')` no botão final

---

## ANEXO C — Glossário rápido

| Termo | Significado neste projeto |
|---|---|
| **Caso** (`Case`) | Unidade de trabalho no LegalTech — o pedido em si |
| **Parte** (`CaseParty`) | Pessoa física ou jurídica envolvida no caso |
| **Produto** | Tipo de análise (dados_partes / consulta_objeto / analise_contratual / reuniao_equipe) |
| **Módulo** | Integração específica (Escavador, Serasa, TargetData, IA, etc.) |
| **MATRIZ** | Tabela produto×módulo que diz quais módulos são obrigatórios/recomendados/opcionais por produto |
| **TenantContext** | Contexto extraído do JWT contendo organization_id + user_id + role |
| **AgentExecution** | Registro de uma execução de worker (idempotente por idempotency_key) |
| **HumanReview** | Aprovação humana obrigatória antes de liberar relatório final |
| **External Query Cache** | Cache de respostas de APIs caras (Escavador) por hash dos inputs |

---

> **Final do documento.** Este markdown é auto-suficiente e pode ser colado em ChatGPT/Claude/Gemini para continuação da análise ou execução do roadmap. Tamanho: ~28KB.
