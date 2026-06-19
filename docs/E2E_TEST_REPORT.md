# Relatorio de Teste E2E Local - LegalTech AWS V2

Data da execucao: 2026-05-26  
Ambiente: Windows local, PowerShell, Docker PostgreSQL, FastAPI, Next.js  
Escopo: MVP local com dados ficticios, sem AWS real, sem Cognito real, sem S3/SQS real e sem IA externa.

## Resultado geral

Status: aprovado para MVP local controlado.

O fluxo end-to-end local validou PostgreSQL Docker, Alembic, seed interno de permissoes, JWT dev, RBAC, clients, cases, documents, upload local/mock, normalizacao Markdown, fila local, worker, `agent_executions`, chunks, embeddings fake e `audit_log`.

O projeto ainda nao esta pronto para producao ou deploy AWS real. Permanecem necessarias as etapas de infraestrutura AWS, Cognito real, S3/SQS reais, observabilidade, hardening LGPD, revisao visual em navegador real e remediacao planejada da vulnerabilidade transitiva moderada `next -> postcss` ja documentada na Tarefa 26.

## Pre-requisitos usados

- Docker/PostgreSQL local via `docker-compose.yml`.
- Banco `legaltech`, usuario ficticio `legaltech`, senha ficticia `legaltech_dev`.
- API com `.env` local criado a partir de `apps/api/.env.example.local`.
- Frontend com `.env.local` criado a partir de `apps/frontend/.env.example`.
- Dados tecnicos ficticios:
  - `organization_id=11111111-1111-4111-8111-111111111111`
  - `user_id=22222222-2222-4222-8222-222222222222`
  - `email=dev.local@example.test`

## Comandos executados

Infra local:

```powershell
docker compose up -d postgres
docker compose ps
docker compose exec postgres pg_isready -U legaltech -d legaltech
Test-NetConnection -ComputerName 127.0.0.1 -Port 5432
docker compose exec postgres psql -U legaltech -d legaltech -c "SELECT extname FROM pg_extension WHERE extname IN ('uuid-ossp', 'vector') ORDER BY extname;"
```

Migrations e seed:

```powershell
cd legaltech-aws\apps\api
$env:DATABASE_URL="postgresql+psycopg://legaltech:legaltech_dev@localhost:5432/legaltech"
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current

cd ..\..
Get-Content database\local\seed_example_organization.sql | docker compose exec -T postgres psql -U legaltech -d legaltech

cd apps\api
.\.venv\Scripts\python.exe -m src.modules.admin.seed_roles_permissions --organization-id 11111111-1111-4111-8111-111111111111 --actor-user-id 22222222-2222-4222-8222-222222222222
```

Servidores locais:

```powershell
# Logs locais em legaltech-aws\.local\e2e-logs\
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000
npm run dev -- --hostname 127.0.0.1 --port 3000
```

E2E automatizado:

```powershell
cd legaltech-aws
apps\api\.venv\Scripts\python.exe scripts\run_local_e2e.py
```

Backend:

```powershell
cd legaltech-aws\apps\api
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall src tests
.\.venv\Scripts\python.exe -m pip check
$env:DATABASE_URL="postgresql+psycopg://legaltech:legaltech_dev@localhost:5432/legaltech"
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current
```

Frontend:

```powershell
cd legaltech-aws\apps\frontend
npm run test
npm run typecheck
npm run lint
npm run build
```

Scripts:

```powershell
cd legaltech-aws
apps\api\.venv\Scripts\python.exe scripts\validate_env.py --env-file .env.example --environment local --target backend
apps\api\.venv\Scripts\python.exe scripts\validate_env.py --env-file apps\frontend\.env.example --environment local --target frontend
apps\api\.venv\Scripts\python.exe scripts\validate_env.py --env-file infra\aws\env.example --environment staging --target aws
apps\api\.venv\Scripts\python.exe scripts\check_project_security.py
```

Frontend HTTP:

```powershell
Invoke-WebRequest http://127.0.0.1:3000/login
Invoke-WebRequest http://127.0.0.1:3000/dashboard
Invoke-WebRequest http://127.0.0.1:3000/clients
Invoke-WebRequest http://127.0.0.1:3000/cases
Invoke-WebRequest http://127.0.0.1:3000/cases/0346b2a8-49ce-4e8e-9c00-8b1a27524291
Invoke-WebRequest http://127.0.0.1:3000/documents
```

Git:

```powershell
git diff --check
git status --short
```

## Resultados por modulo

### Infra local

- PostgreSQL Docker: aprovado.
- Porta 5432: acessivel.
- Health do container: aprovado.
- Extensoes `uuid-ossp` e `vector`: presentes.
- Alembic: `0003_doc_md_norm (head)`.

### Backend/API

- `GET /health`: aprovado.
- JWT dev local: aprovado.
- `Authorization: Bearer <token>`: aprovado.
- Erro 401 sem token em rota sensivel: aprovado.
- Erro 403 sem permissao: aprovado.
- RBAC com `roles_permissions`: aprovado.
- Payload com `organization_id` em `POST /api/v1/clients`: rejeitado com 422.

### Clients

- `POST /api/v1/clients`: aprovado.
- `GET /api/v1/clients`: aprovado.
- `GET /api/v1/clients/{client_id}`: aprovado.
- `PATCH /api/v1/clients/{client_id}`: aprovado.
- `organization_id` nao foi usado como fonte de verdade do frontend.

### Cases

- `POST /api/v1/cases`: aprovado.
- `GET /api/v1/cases`: aprovado.
- `GET /api/v1/cases/{case_id}`: aprovado.
- `PATCH /api/v1/cases/{case_id}`: aprovado.
- Caso ficou vinculado ao tenant do token/JWT dev.

### Documents

- Criacao de metadata: aprovado.
- Upload local/mock `.txt`: aprovado.
- Upload local/mock `.md`: aprovado.
- Upload local/mock `.docx` simples: aprovado.
- `GET /api/v1/documents`: aprovado.
- `GET /api/v1/documents/{document_id}/download-url`: aprovado.
- Storage local em `apps/api/storage/local_uploads/`: ignorado pelo Git.

### Normalizacao Markdown

- Worker normalizou `.txt` para Markdown: aprovado.
- Worker normalizou `.md` para Markdown: aprovado.
- Campos persistidos no documento processado:
  - `conversion_status=converted`
  - `normalized_markdown_storage_key`
  - `normalized_markdown_sha256`
  - `normalized_markdown_size_bytes`
  - `converted_at`
- Conteudo integral do Markdown nao apareceu em `audit_log`.

### Fila local e worker

- Enfileiramento por `POST /api/v1/documents/{document_id}/enqueue-processing`: aprovado.
- Worker local consumiu job: aprovado.
- `agent_executions` criado e concluido: aprovado.
- `documents.status=processed`: aprovado.
- Chunks criados: aprovado.
- Embeddings fake/deterministicos criados: aprovado.
- Idempotencia por `job_id` duplicado concluido: aprovado com `duplicate_completed`.

### Audit log

Eventos confirmados no E2E:

- `clients.create`
- `clients.update`
- `cases.create`
- `cases.update`
- `documents.create`
- `documents.upload`
- `documents.download_url`
- `documents.process_requested`
- `documents.conversion_started`
- `documents.conversion_completed`
- `documents.process_started`
- `documents.process_completed`
- `agent_execution.created`
- `agent_execution.started`
- `agent_execution.completed`
- `agent_execution.skipped`
- `rbac.denied`

O teste validou que o `audit_log` nao continha o JWT completo nem a frase de conteudo sensivel ficticio usada no arquivo de teste.

### Frontend

- Next.js dev server em `http://127.0.0.1:3000`: aprovado.
- `/login`: 200 e renderiza fluxo JWT dev/local.
- `/dashboard`: 200 e guarda visual sem sessao.
- `/clients`: 200 e guarda visual sem sessao.
- `/cases`: 200 e guarda visual sem sessao.
- `/cases/[id]`: 200 e guarda visual sem sessao.
- `/documents`: 200 e guarda visual sem sessao.
- `npm run test`: 18 testes passaram.
- `npm run typecheck`: aprovado.
- `npm run lint`: aprovado.
- `npm run build`: aprovado.

Observacao: o navegador embutido desta sessao retornou `Browser is not available: iab`. Por isso, a validacao visual interativa com clique/login colando JWT dev nao foi executada no browser in-app. A verificacao possivel nesta sessao foi feita por HTTP/HTML, testes unitarios de `authStorage`/`apiClient`/services e build.

### Seguranca e ambiente

- `validate_env.py` backend local: aprovado.
- `validate_env.py` frontend local: aprovado.
- `validate_env.py` AWS staging example: aprovado.
- `check_project_security.py`: aprovado sem evidencia bloqueante.
- Avisos esperados: `apps/api/.env` e `apps/frontend/.env.local` existem localmente e estao ignorados pelo Git.

## Problemas encontrados

1. `Start-Process` com logs em `C:\tmp\legaltech-api-e2e.out.log` falhou com `Access denied`.
   - Correcao: usar `legaltech-aws/.local/e2e-logs/`.
   - `.local/` foi adicionado ao `.gitignore`.

2. Processo FastAPI iniciado dentro do sandbox era encerrado apos o comando.
   - Correcao operacional: iniciar o servidor local em background fora do sandbox, com logs locais em `.local/e2e-logs/`.

3. Evento `rbac.denied` nao ficava persistido porque o `HTTPException(403)` disparava rollback da sessao.
   - Impacto: trilha LGPD/RBAC incompleta para negacoes.
   - Correcao: confirmar o audit event antes de retornar `403`.
   - Validacao: E2E e testes unitarios passaram.

4. Browser in-app indisponivel nesta sessao.
   - Impacto: nao houve validacao visual interativa com clique/preenchimento.
   - Mitigacao: HTTP/SSR, testes de frontend, typecheck, lint e build foram executados.

## Limitacoes

- Sem Cognito real.
- Sem S3/SQS reais.
- Sem AWS real.
- Sem OCR real.
- Sem IA/RAG real.
- Sem APIs externas.
- Fila local e JSONL em disco, adequada apenas para desenvolvimento.
- `localStorage` no frontend e apenas para JWT dev/local.
- Validacao visual interativa deve ser repetida em navegador real antes de demo operacional.
- Nao usar dados reais ate concluir hardening de seguranca, LGPD, infraestrutura e observabilidade.

## Conclusao

O MVP local esta aprovado para a Tarefa 27 e para testes controlados com dados ficticios.

O projeto nao esta pronto para producao nem para deploy AWS real. Antes disso, ainda sao necessarios Cognito real, infraestrutura AWS, IAM minimo privilegio, S3/SQS reais, observabilidade, backup, politica LGPD operacional, revisao visual em navegador real e correcao planejada das dependencias transitivas do frontend.
