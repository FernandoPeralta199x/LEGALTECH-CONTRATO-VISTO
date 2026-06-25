# API Readiness — o que é real vs gated (para subir na AWS)

> Estado verificado contra PostgreSQL real. Atualizado após o hardening de API (M-01, M-05, A-02, gate fail-closed, C-03).
> Regra de ouro: com `APP_ENV` em `staging`/`prod`, a API **recusa subir** se configurada para servir dado falso (ver "Gate de ambiente").

## 1. Rotas REAIS e funcionais (DB-backed, prontas para AWS)

Todas com RBAC (`require_permission`) e filtro por `organization_id` em toda query.

| Grupo | Endpoints | Persistência | Observação |
|---|---|---|---|
| **Auth** | `/auth/register`, `/auth/verify-email`, `/auth/login`, `/auth/me` | PostgreSQL (`users`) | Envelope padronizado (A-02 corrigido). Local: `dev_jwt` (gated a `local`). Staging/prod: **exige `AUTH_PROVIDER=cognito`** (verifier RS256/JWKS fail-closed pronto). |
| **Clients** | CRUD de clientes | `clients` | |
| **Cases** | lista, agregado, criação | `cases` + sub-tabelas operacionais | Caminho F: agregado lê tudo do banco. |
| **Requests (pedidos)** | criar, listar, obter, `/case` | `requests` | M-01 corrigido (sem 500 com ≥2 pedidos). **Congela preço** (`total_price_cents` + `price_snapshot`) na criação (C-03). |
| **Case parties** | CRUD de partes | `operational_parties` | Documento mascarado (LGPD) na leitura. |
| **Documents (upload)** | upload, metadados, download | `operational_documents` + storage | Storage `local` por padrão; `s3` sob `STORAGE_BACKEND=s3` (adapter pronto + presigned). Upload com allowlist ext/MIME, anti path-traversal, limite de tamanho. |
| **Triage (plano)** | criar/ler plano de triagem | `triage_modules` | A **orquestração de execução** com providers reais é gated (ver seção 2). |
| **Provider results** | ler resultados | `provider_results` | Dados gravados pela execução (mock hoje). |
| **Reports (estrutura)** | gerar/ler/regenerar (estrutura) | `operational_reports` | Status/versão/estrutura reais; o **conteúdo de IA** é mock (seção 2). |
| **Timeline** | eventos do caso | `timeline_events` | Append-only. |
| **Pricing** | catálogo, estimate, config da org | `pricing_configs` | Dinheiro em centavos inteiros; audit em alteração de config. |
| **Audit** | trilha LGPD | `audit_log` | Sanitiza token/CPF/CNPJ/Bearer/JWT. |

## 2. Rotas GATED (mock — fail-closed em staging/prod)

Estes caminhos hoje retornam **dado fabricado** por padrão. O gate de ambiente **impede a API de subir** em `staging`/`prod` enquanto estiverem em `mock`, para **nunca servir dado jurídico falso**. Para funcionarem de verdade na AWS, exigem **integrações reais** (serviço externo + credenciais que você fornece) — projeto à parte.

| Domínio | Backend | O que falta para ser real |
|---|---|---|
| **Análise de IA de contrato** | `AI_ANALYSIS_BACKEND=mock` | Adapter real (OpenAI/Bedrock) + `AI_ANALYSIS_API_KEY`. |
| **OCR** | `OCR_BACKEND=mock` | AWS Textract (ou equivalente). |
| **Due diligence externa** | `ESCAVADOR/SERASA/CNJ_BACKEND=mock` | Contratos/chaves dos provedores. |
| **RAG / embeddings** | fake (SHA256 determinístico) | Embeddings reais + busca vetorial (pgvector já instalado). |
| **E-mail** | `EMAIL_BACKEND=mock` | SES (adapter pronto) — gate exige `ses` em staging/prod. |

## 3. Gate de ambiente (fail-closed)

`enforce_production_safety()` roda no boot (`create_app`). Com `APP_ENV` em `staging`/`prod`, **recusa subir** se:
- algum backend de dado jurídico em `mock` (ai_analysis, ocr, escavador, serasa, cnj);
- `EMAIL_BACKEND=mock`;
- `AUTH_PROVIDER != cognito`;
- `DEV_JWT_ENABLED=True`.

Além disso: `build_operational_repositories` **falha** se `db` ausente fora de `local`/`test` (M-06 — `_STORE` em memória nunca é fonte de verdade); e **docs/OpenAPI** só são expostos em `local`/`test` (M-07).

Em `local`/`test` nada disso é aplicado (desenvolvimento livre).

## 4. Pendente de infra (com você — a API não bloqueia)

IaC (Terraform/CDK), Dockerfile de produção (sem `--reload`, non-root), deploy do frontend, Secrets Manager, DLQ, WAF, CloudWatch, rate-limit distribuído (Redis). Ver `FINAL_CIRURGICO.md` seções 11 e 16.
