# Checklist de Prontidao do MVP - LegalTech AWS V2

Este checklist resume a prontidao tecnica atual para seguir para testes
end-to-end locais e, depois, preparacao de deploy controlado.

## Backend

- [x] FastAPI inicial organizado.
- [x] Endpoint `GET /health`.
- [x] Routers de clients, cases, documents, document processing e audit
  registrados.
- [x] Settings centralizados por Pydantic.
- [x] Auth local dev JWT isolado por `APP_ENV=local`.
- [x] Cognito/JWKS preparado com testes mockados.
- [x] TenantContext derivado do token validado.
- [x] RBAC baseado em `roles_permissions`.
- [x] Audit log com sanitizacao LGPD.
- [x] CORS local/dev configuravel por `CORS_ALLOWED_ORIGINS`.
- [ ] Login Cognito real.
- [ ] Administracao real de usuarios e convites.
- [ ] Rate limiting/WAF/observabilidade real.

## Frontend

- [x] Next.js + TypeScript + Tailwind.
- [x] Login dev local.
- [x] Header/sidebar/layout.
- [x] Telas `/dashboard`, `/clients`, `/cases`, `/cases/[id]` e `/documents`.
- [x] Services integrados com API real e fallback mockado controlado.
- [x] `Authorization: Bearer <token>` enviado pelo apiClient quando ha token.
- [x] Loading, error, empty states, formularios e notificacoes.
- [ ] Resolver vulnerabilidade transitiva moderada `next -> postcss` quando
  houver caminho de upgrade seguro.
- [ ] Cognito Hosted UI real.
- [ ] Refresh token real.
- [ ] Upload real de arquivo pela UI.
- [ ] Fluxo completo de relatorios/revisao humana.

## Banco e migrations

- [x] SQLAlchemy models iniciais.
- [x] Alembic configurado.
- [x] Migration `0001_initial_models.py`.
- [x] Migration `0002_remaining_mvp_models.py`.
- [x] Migration `0003_doc_md_norm.py`.
- [x] `0003_doc_md_norm` com `down_revision = "0002_remaining_mvp_models"`.
- [x] Campos de normalizacao Markdown em `documents`.
- [x] Indices basicos por organizacao/status/caso.
- [ ] Row Level Security opcional.
- [ ] Estrategia formal de rollback de migrations.

## Documentos e storage

- [x] Metadados de documentos no banco.
- [x] Upload local/mock em pasta ignorada pelo Git.
- [x] Storage abstrato local/S3 preparado.
- [x] Presigned download URL preparado.
- [x] Nao expor caminho local interno em resposta publica.
- [ ] Bucket S3 real privado.
- [ ] Upload S3 real/presigned upload completo.
- [ ] Politicas reais de lifecycle/retencao.

## Normalizacao Markdown

- [x] TXT para Markdown.
- [x] MD normalizado.
- [x] DOCX simples para Markdown.
- [x] PDF textual para Markdown.
- [x] PDF sem texto marcado como `requires_ocr`.
- [x] Markdown convertido salvo em storage ignorado pelo Git.
- [x] Worker usa Markdown como entrada preferencial.
- [ ] OCR real.
- [ ] Parser avancado de tabelas/imagens/anexos complexos.

## Filas e workers

- [x] Fila local/mock JSONL.
- [x] Publisher local.
- [x] Cliente SQS preparado sem AWS real.
- [x] Worker local de processamento de documentos.
- [x] Revalidacao de tenant/case/document no worker.
- [x] `agent_executions` com queued/running/completed/failed/retrying/skipped.
- [x] Retry/idempotencia basicos.
- [ ] SQS real.
- [ ] DLQ real.
- [ ] Lambda/worker gerenciado.
- [ ] Concorrencia e locking distribuido.

## Seguranca e LGPD

- [x] `.gitignore` protege `.env`, caches, venv, node_modules e storage local.
- [x] Exemplos de env usam placeholders ficticios.
- [x] JWT dev proibido fora de local por configuracao/testes.
- [x] `organization_id` nao deve vir do frontend como fonte de verdade.
- [x] Audit log sanitiza tokens, documentos integrais e IDs sensiveis.
- [x] Jobs carregam apenas IDs e metadados minimos.
- [ ] Pentest/revisao de seguranca formal.
- [ ] Politica de retencao/anonimizacao LGPD.
- [ ] IAM minimo privilegio real.

## Ambiente e AWS futura

- [x] Docker Compose para PostgreSQL local.
- [x] `pgvector/pgvector:pg16`.
- [x] `docs/ENVIRONMENT_VARIABLES.md`.
- [x] `docs/AWS_DEPLOYMENT_PLAN.md`.
- [x] `docs/SECURITY_CHECKLIST_AWS.md`.
- [x] `infra/aws/env.example`.
- [x] `infra/aws/checklist-deploy.md`.
- [ ] Terraform/CDK/IaC real.
- [ ] Cognito/RDS/S3/SQS/Lambda/CloudFront reais.
- [ ] CloudWatch/CloudTrail/Budgets configurados.

## Pronto para Tarefa 27

Status recomendado: **sim, para testes end-to-end locais controlados**.

Condicoes para Tarefa 27:

- Usar PostgreSQL Docker local.
- Aplicar `alembic upgrade head`.
- Rodar seed de organizacao/permissoes ficticias.
- Gerar JWT dev pelo backend.
- Subir API e frontend local.
- Validar CORS entre frontend e API.
- Executar worker local com jobs de documentos.
- Usar apenas dados ficticios.

Nao esta pronto para producao ou deploy AWS real sem as pendencias de
infraestrutura, IAM, Cognito real, observabilidade, politicas LGPD e revisao de
seguranca formal.
