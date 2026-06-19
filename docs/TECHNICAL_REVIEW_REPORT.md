# Revisao Tecnica Geral - LegalTech AWS V2

## Objetivo

Este relatorio consolida a revisao tecnica do estado atual do projeto antes de
testes end-to-end e deploy controlado. A revisao cobre backend, frontend,
seguranca/LGPD, variaveis de ambiente, documentacao, estrutura de pastas,
normalizacao Markdown, workers locais e preparacao para AWS.

Escopo aplicado:

- Sem deploy real.
- Sem recursos AWS reais.
- Sem credenciais reais.
- Sem APIs externas reais.
- Sem IA, OCR ou RAG real.
- Sem refatoracao ampla.
- Sem alteracao da migration `0003_doc_md_norm`.

## Visao geral do estado atual

O projeto esta em bom estado para a fase de MVP tecnico local. A arquitetura
esta separada em API FastAPI, frontend Next.js, banco PostgreSQL/Alembic,
workers locais, storage local/mock, adaptadores futuros de S3/SQS e
documentacao de AWS. O foco de seguranca multi-tenant, RBAC, auditoria e LGPD
esta presente desde a base.

Atualizacao Tarefa 29.0: a edicao de clientes foi conectada no frontend usando
o endpoint `PATCH /api/v1/clients/{client_id}` ja existente, e a aba Partes do
caso passou a usar API MVP local com `GET`, `POST` e `PATCH` em
`/api/v1/cases/{case_id}/parties`.

Status geral: **aprovado com atencoes para E2E local e producao futura**.

## Resumo por area

| Area | Status | Observacao |
| --- | --- | --- |
| Backend FastAPI | Aprovado | Modulos organizados por routers, services, repositories, schemas e models. |
| Frontend Next.js | Aprovado com atencao | Telas integradas usam services reais com fallback; `npm audit` apontou vulnerabilidade transitiva moderada. |
| Banco/migrations | Aprovado | Alembic possui `0001`, `0002` e `0003_doc_md_norm`; revision curta corrigida. |
| Normalizacao Markdown | Aprovado | TXT, MD, DOCX e PDF textual suportados; OCR real fora do escopo. |
| Workers/filas locais | Aprovado | Job carrega IDs, worker revalida tenant/case/document e usa Markdown preferencial. |
| Seguranca/LGPD | Aprovado com atencao | Sanitizacao de audit_log existe; revisao final de logs reais ainda depende de E2E. |
| Ambientes/env | Aprovado | Exemplos ficticios e validacao local existem. CORS foi adicionado para E2E local. |
| AWS/deploy | Atencao | Planejamento pronto; falta IaC, recursos reais, IAM, Cognito real e observabilidade. |

## Backend

Status: **aprovado**.

Pontos verificados:

- `src/main.py` registra routers de health, clients, cases, documents,
  document_processing e audit.
- `src/core/auth.py`, `tenant.py`, `rbac.py`, `cognito.py` e `jwks.py` separam
  dev JWT, Cognito mockado/futuro, TenantContext e RBAC.
- Rotas sensiveis usam `TenantContext` e permissoes via `roles_permissions`.
- Services e repositories filtram entidades sensiveis por `organization_id`.
- Schemas rejeitam campos autoritativos como `organization_id` nos payloads de
  frontend quando aplicavel.
- `audit_log` sanitiza metadata sensivel e registra eventos de clients, cases,
  documents, processamento, worker e RBAC negado.
- Upload local/mock valida extensao e tamanho, calcula hash e salva em pasta
  ignorada pelo Git.
- Storage abstrato possui modo local e modo S3 preparado, sem exigir AWS real.
- CORS configuravel foi adicionado para permitir E2E local entre frontend
  `localhost:3000` e API `127.0.0.1:8000`.

Atencoes:

- `AUTH_PROVIDER=dev_jwt` e `DEV_JWT_ENABLED=true` continuam permitidos somente
  para `APP_ENV=local`.
- O backend ainda nao possui login real Cognito, convite de usuarios, refresh
  token, administracao de usuarios ou Hosted UI.
- Revisao de CORS para staging/prod deve restringir origens ao dominio real do
  frontend.

## Banco e migrations

Status: **aprovado**.

Pontos verificados:

- Alembic esta organizado em `apps/api/alembic`.
- Migrations atuais:
  - `0001_initial_models.py`
  - `0002_remaining_mvp_models.py`
  - `0003_doc_md_norm.py`
- `0003_doc_md_norm` mantem `down_revision = "0002_remaining_mvp_models"`.
- A revision curta evita estouro de `alembic_version.version_num VARCHAR(32)`.
- Campos de normalizacao em `documents` existem no model e na migration:
  - `conversion_status`
  - `normalized_markdown_storage_key`
  - `normalized_markdown_sha256`
  - `normalized_markdown_size_bytes`
  - `conversion_error_summary`
  - `converted_at`
- Existe indice `idx_documents_org_conversion_status`.
- O PostgreSQL local usa imagem `pgvector/pgvector:pg16` e init de extensoes.
- O modelo recomendado para o MVP e PostgreSQL unico com pgvector no mesmo
  banco; nao ha necessidade atual de banco vetorial separado.

Atencoes:

- RLS ainda nao foi implementado; o isolamento atual depende da camada de
  aplicacao.
- Antes de producao, migrations devem ser testadas em banco equivalente com
  snapshot/rollback documentado.

## Normalizacao Markdown

Status: **aprovado**.

Pontos verificados:

- Modulo `src/modules/document_normalization` possui converter, service,
  schemas e repository.
- Formatos suportados nesta etapa:
  - `.txt`
  - `.md`
  - `.docx`
  - `.pdf` com texto extraivel
- PDF sem texto extraivel levanta erro controlado `requires_ocr`, sem tentar
  OCR real.
- Markdown convertido e salvo em storage local/mock via `save_markdown`.
- O worker usa Markdown normalizado como entrada preferencial para chunks.
- Audit logs de conversao gravam IDs, status, extensao, tamanho e hash, sem
  conteudo integral.

Atencoes:

- DOCX suporta paragrafos e tabelas simples; elementos complexos ficam para
  tarefas futuras.
- PDF textual usa extracao simples; qualidade varia conforme o documento.
- OCR real, classificacao documental e RAG real permanecem fora do escopo.

## Workers e filas locais

Status: **aprovado**.

Pontos verificados:

- `src/modules/queues` possui fila local, schemas, publisher e cliente SQS
  preparado.
- `workers/document_processing/worker.py` consome jobs locais, revalida banco,
  controla `agent_executions`, idempotencia, retry e status de documentos.
- Payload de job transporta apenas IDs e metadados minimos.
- Worker registra audit_log para inicio, sucesso, falha e skip.
- Worker nao chama AWS SQS real, Lambda, OCR, IA, Bedrock, OpenAI, Claude ou
  APIs externas.

Atencoes:

- Nao ha DLQ real ainda.
- Nao ha concorrencia real de worker nem locking distribuido.
- SQS real e Lambda/worker gerenciado ficam para etapa de infraestrutura.

## Frontend

Status: **aprovado com atencao**.

Pontos verificados:

- Estrutura Next.js organizada em `src/app`, `components`, `src/services`,
  `types`, `lib` e reexports de compatibilidade.
- Telas existentes:
  - `/`
  - `/login`
  - `/dashboard`
  - `/clients`
  - `/cases`
  - `/cases/[id]`
  - `/documents`
- `src/services/apiClient.ts` usa `NEXT_PUBLIC_API_BASE_URL` e envia
  `Authorization: Bearer <token>` quando ha sessao dev.
- Services de clients, cases e documents usam API real com fallback mockado
  apenas para erro de rede.
- Erros de autorizacao, validacao e respostas do backend nao sao mascarados por
  fallback.
- Payloads de criacao nao enviam `organization_id` como fonte de autoridade.
- Componentes de loading, erro, vazio, formulario, notificacao e confirmacao
  estao presentes.
- `/clients` permite editar clientes ja cadastrados.
- `/cases/[id]` lista, cria e edita partes do caso via backend local.

Atencoes:

- Login e sessao local usam `localStorage` apenas para desenvolvimento.
- Login local exige JWT dev colado; sessoes placeholder antigas sao descartadas
  pelo armazenamento local.
- Cognito real no frontend, refresh token e Hosted UI ainda nao existem.
- Upload real de arquivo pelo frontend ainda nao foi implementado.
- `npm audit --omit=dev --audit-level=moderate` apontou 2 vulnerabilidades
  moderadas transitivas em `next -> postcss`. O npm indicou correcao apenas via
  `npm audit fix --force`, com mudanca quebravel, entao nao foi aplicada nesta
  revisao.

## Seguranca e LGPD

Status: **aprovado com atencao**.

Pontos verificados:

- `.env`, `.env.*`, credenciais, chaves privadas, `.venv`, `node_modules`,
  `.next`, `.npm-cache`, storage local e filas locais estao ignorados.
- `scripts/check_project_security.py` existe e procura padroes comuns de
  secrets e artefatos inseguros.
- Exemplos de env usam valores ficticios.
- JWT dev esta documentado como proibido fora de local.
- `AUTH_PROVIDER=cognito` esta documentado como caminho para AWS.
- S3 privado e presigned URL estao documentados.
- `audit_log` sanitiza metadata sensivel.
- Jobs e logs evitam conteudo integral de documento.

Atencoes:

- A revisao nao substitui pentest, revisao juridica LGPD ou hardening cloud.
- Em producao sera necessario configurar CORS restrito, WAF, rate limiting,
  observabilidade, IAM minimo privilegio e politicas de retencao.

## Ambientes e variaveis

Status: **aprovado**.

Pontos verificados:

- `.env.example`, `apps/api/.env.example.local`,
  `apps/frontend/.env.example` e `infra/aws/env.example` existem.
- `scripts/validate_env.py` valida backend, frontend e AWS futura.
- Ambientes documentados:
  - `local`
  - `dev`
  - `staging`
  - `prod`
- `CORS_ALLOWED_ORIGINS` foi adicionado aos exemplos e a validacao de backend.

Atencoes:

- Em staging/prod, `NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK=false` deve ser
  obrigatorio.
- Valores reais devem ficar em mecanismo seguro fora do Git.

## AWS e deploy

Status: **atencao**.

Pontos verificados:

- `infra/README.md`, `infra/aws/README.md`, `infra/aws/env.example` e
  `infra/aws/checklist-deploy.md` existem.
- `docs/AWS_DEPLOYMENT_PLAN.md` e `docs/SECURITY_CHECKLIST_AWS.md` documentam
  Cognito, RDS, S3 privado, SQS, workers/Lambda, Secrets Manager, CloudWatch,
  IAM, VPC, backups e KMS futuro.
- Nenhum recurso real AWS e criado nesta etapa.

Pendencias antes de deploy real:

- IaC com Terraform/CDK ou equivalente.
- Cognito User Pool e claims reais.
- RDS privado, backups e snapshots.
- Bucket S3 privado com criptografia, lifecycle e block public access.
- SQS real com DLQ.
- IAM minimo privilegio.
- Observabilidade CloudWatch/CloudTrail/Budgets.
- Plano de rollback validado.

## Correcoes aplicadas nesta revisao

- Adicionada configuracao `CORS_ALLOWED_ORIGINS` no backend.
- Registrado `CORSMiddleware` em `src/main.py` com origens configuraveis.
- Criado teste de preflight CORS local.
- Atualizados `.env.example`, `apps/api/.env.example.local`,
  `infra/aws/env.example`, `docs/ENVIRONMENT_VARIABLES.md`,
  `apps/api/README.md` e `apps/frontend/README.md`.
- Criados documentos de revisao, checklist MVP e limitacoes conhecidas.

## Validacoes executadas

Backend:

- `.venv\Scripts\python.exe -m unittest discover -s tests -v`: 129 testes OK.
- `.venv\Scripts\python.exe -m compileall src tests`: OK.
- `.venv\Scripts\python.exe -m pip check`: sem dependencias quebradas.
- `.venv\Scripts\alembic.exe upgrade head`: OK.
- `.venv\Scripts\alembic.exe current`: `0003_doc_md_norm (head)`.

Frontend:

- `npm run test`: 18 testes OK.
- `npm run typecheck`: OK.
- `npm run lint`: OK.
- `npm run build`: OK.
- `npm audit --omit=dev --audit-level=moderate`: encontrou 2 vulnerabilidades
  moderadas transitivas em `next -> postcss`; sem correcao segura automatica
  nesta etapa.

Scripts:

- `apps\api\.venv\Scripts\python.exe scripts\validate_env.py --env-file .env.example --environment local --target backend`: OK.
- `apps\api\.venv\Scripts\python.exe scripts\validate_env.py --env-file apps\frontend\.env.example --environment local --target frontend`: OK.
- `apps\api\.venv\Scripts\python.exe scripts\validate_env.py --env-file infra\aws\env.example --environment staging --target aws`: OK.
- `apps\api\.venv\Scripts\python.exe scripts\check_project_security.py`: OK.

## Limitacoes conhecidas

Ver tambem: `docs/KNOWN_LIMITATIONS.md`.

Principais limitacoes:

- Sem deploy real.
- Sem Cognito Hosted UI real.
- Sem S3/SQS/Lambda reais.
- Sem OCR real.
- Sem IA/RAG real.
- Sem APIs externas reais.
- Sem RLS no PostgreSQL.
- Sem upload real de arquivo no frontend.
- Sem fluxo completo de relatorios juridicos e revisao humana.

## Riscos antes de producao

- Misconfiguracao de auth/Cognito/claims pode comprometer tenant isolation.
- Origem CORS ampla em producao pode ampliar superficie de ataque.
- Vulnerabilidade transitiva moderada em `next -> postcss` precisa de upgrade
  controlado quando houver caminho sem quebra.
- Falta de IaC revisado pode gerar recursos AWS inconsistentes por ambiente.
- Falta de observabilidade e alertas dificulta resposta a incidentes.
- Falta de politica formal de retencao/anonimizacao LGPD.
- Falta de revisao humana implementada no fluxo final de relatorios.

## Proximos passos recomendados

1. Rodar Tarefa 27 com testes end-to-end locais usando backend, frontend,
   PostgreSQL Docker, seed, JWT dev e worker local.
2. Validar fluxo browser real de `/login`, `/clients`, `/cases`, `/documents`
   contra API local com CORS.
3. Criar smoke E2E de upload local/mock e processamento via worker.
4. Adicionar correlation/request id para cruzar API, fila local, worker e
   audit_log.
5. Planejar IaC minimo para ambiente `dev` sem dados reais.
6. Integrar a etapa de Partes do wizard `/cases/new` ao novo modulo
   `/api/v1/cases/{case_id}/parties`.
