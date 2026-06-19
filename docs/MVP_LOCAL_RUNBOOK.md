# Runbook Local do MVP - LegalTech AWS V2

Este runbook descreve como subir e validar o MVP local com dados ficticios.
Ele nao cria recursos AWS reais e nao deve ser usado com dados pessoais ou documentos reais.

## 1. Pre-requisitos

- Docker Desktop ou Docker Engine com Compose.
- Python 3.12+.
- Node.js compativel com o frontend.
- Dependencias ja instaladas em:
  - `apps/api/.venv`
  - `apps/frontend/node_modules`

## 2. Arquivos locais de ambiente

Na raiz do projeto:

```powershell
cd legaltech-aws
Copy-Item apps\api\.env.example.local apps\api\.env
Copy-Item apps\frontend\.env.example apps\frontend\.env.local
```

Os arquivos `.env` e `.env.local` sao locais e ignorados pelo Git.
Nao coloque segredos reais nesses arquivos.

## 3. Subir PostgreSQL local

```powershell
cd legaltech-aws
docker compose up -d postgres
docker compose ps
docker compose exec postgres pg_isready -U legaltech -d legaltech
```

Validar porta e extensoes:

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 5432
docker compose exec postgres psql -U legaltech -d legaltech -c "SELECT extname FROM pg_extension WHERE extname IN ('uuid-ossp', 'vector') ORDER BY extname;"
```

## 4. Aplicar migrations

```powershell
cd legaltech-aws\apps\api
$env:DATABASE_URL="postgresql+psycopg://legaltech:legaltech_dev@localhost:5432/legaltech"
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current
```

Resultado esperado:

```text
0003_doc_md_norm (head)
```

## 5. Seed tecnico ficticio

```powershell
cd legaltech-aws
Get-Content database\local\seed_example_organization.sql | docker compose exec -T postgres psql -U legaltech -d legaltech
```

Popular permissoes base:

```powershell
cd legaltech-aws\apps\api
$env:DATABASE_URL="postgresql+psycopg://legaltech:legaltech_dev@localhost:5432/legaltech"
.\.venv\Scripts\python.exe -m src.modules.admin.seed_roles_permissions `
  --organization-id 11111111-1111-4111-8111-111111111111 `
  --actor-user-id 22222222-2222-4222-8222-222222222222
```

## 6. Gerar JWT dev

```powershell
cd legaltech-aws\apps\api
$env:APP_ENV="local"
$env:AUTH_PROVIDER="dev_jwt"
$env:DEV_JWT_ENABLED="true"
$env:DEV_JWT_SECRET="fictitious-local-dev-secret-32-bytes-minimum"
$TOKEN = .\.venv\Scripts\python.exe -m src.modules.admin.dev_jwt `
  --organization-id 11111111-1111-4111-8111-111111111111 `
  --user-id 22222222-2222-4222-8222-222222222222 `
  --email dev.local@example.test `
  --role admin
```

Use esse token apenas localmente.
Nao cole tokens reais no frontend.

## 7. Subir FastAPI local

Logs recomendados:

```powershell
cd legaltech-aws
New-Item -ItemType Directory -Force -Path .local\e2e-logs | Out-Null
```

Em um terminal:

```powershell
cd legaltech-aws\apps\api
$env:DATABASE_URL="postgresql+psycopg://legaltech:legaltech_dev@localhost:5432/legaltech"
$env:APP_ENV="local"
$env:AUTH_PROVIDER="dev_jwt"
$env:DEV_JWT_ENABLED="true"
$env:DEV_JWT_SECRET="fictitious-local-dev-secret-32-bytes-minimum"
$env:CORS_ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000,http://192.168.0.102:3000"
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Para teste no celular na mesma rede, use `--host 0.0.0.0 --port 8000` e
valide `http://192.168.0.102:8000/health`.

## 8. Subir frontend local

Em outro terminal:

```powershell
cd legaltech-aws\apps\frontend
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
$env:NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK="true"
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Para teste mobile:

```powershell
cd legaltech-aws\apps\frontend
$env:NEXT_PUBLIC_API_BASE_URL="http://192.168.0.102:8000"
$env:NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK="true"
npm run dev -- --hostname 0.0.0.0 --port 3000
```

Acesse:

```text
http://127.0.0.1:3000/login
```

Cole o JWT dev no campo `JWT dev do backend` para testar chamadas protegidas.
O frontend valida o token no backend via `GET /api/v1/me` antes de salvar a
sessao local. Sem token, token malformado, expirado ou recusado pela API, o
login mostra erro e nao redireciona para telas internas.

## 9. Upload local de documentos pelo frontend

A tela `/documents` permite upload funcional apenas no MVP local/dev.
O fluxo usa `POST /api/v1/documents/upload` com `multipart/form-data`, JWT dev
em `Authorization: Bearer` via `apiClient` e `case_id` selecionado na UI.
O `organization_id` vem do JWT/backend e nunca deve ser enviado pelo frontend.

Arquivos enviados localmente ficam em:

```text
apps/api/storage/local_uploads/
```

Essa pasta ja esta ignorada pelo Git em `.gitignore`. Nao use dados reais nos
uploads locais. Para limpeza manual, apague somente arquivos de desenvolvimento
nessa pasta com os servidores parados ou sem jobs em execucao.

Tipos aceitos no MVP local:

- PDF;
- PNG;
- JPG/JPEG;
- DOCX;
- TXT;
- MD.

Limite padrao: 10 MB por arquivo (`MAX_UPLOAD_SIZE_BYTES=10485760`).
S3 real, presigned upload completo, OCR e IA/RAG continuam fora desta etapa.

Fluxo manual:

```text
http://127.0.0.1:3000/documents
```

1. Entre com JWT dev.
2. Selecione um caso.
3. Selecione um arquivo ficticio pequeno.
4. Clique em Enviar documento.
5. Confirme que o documento aparece na lista.
6. Recarregue a pagina e confirme que ele continua listado.

## 10. Rodar E2E automatizado

Com PostgreSQL e FastAPI rodando:

```powershell
cd legaltech-aws
apps\api\.venv\Scripts\python.exe scripts\run_local_e2e.py
```

O script valida:

- `/health`
- 401 sem token
- 403 sem permissao
- rejeicao de `organization_id` no payload
- CRUD de clients
- CRUD de cases
- CRUD MVP de partes do caso via API
- metadata de document
- upload `.txt`, `.md` e `.docx` ficticios
- download URL local/mock
- enqueue de processamento
- worker local
- normalizacao Markdown
- chunks e embeddings fake
- idempotencia por `job_id`
- audit_log sem JWT completo ou conteudo integral do documento

## 11. Validacoes obrigatorias

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

Git:

```powershell
git diff --check
git status --short
```

## 12. Conferencias manuais uteis

Consultar `audit_log`:

```powershell
docker compose exec postgres psql -U legaltech -d legaltech -c "SELECT action, COUNT(*) FROM audit_log WHERE organization_id = '11111111-1111-4111-8111-111111111111' GROUP BY action ORDER BY action;"
```

Consultar documentos processados:

```powershell
docker compose exec postgres psql -U legaltech -d legaltech -c "SELECT id, status, conversion_status, normalized_markdown_sha256, normalized_markdown_size_bytes, converted_at FROM documents ORDER BY created_at DESC LIMIT 10;"
```

Consultar agent executions:

```powershell
docker compose exec postgres psql -U legaltech -d legaltech -c "SELECT job_id, agent_type, status, attempt, started_at, completed_at FROM agent_executions ORDER BY created_at DESC LIMIT 10;"
```

Consultar partes do caso:

```powershell
docker compose exec postgres psql -U legaltech -d legaltech -c "SELECT case_id, party_type, name, created_at FROM case_parties ORDER BY created_at DESC LIMIT 10;"
```

## 13. Encerrar servidores locais

Se os servidores foram iniciados em background, encontre os PIDs:

```powershell
netstat -ano | Select-String ":8000"
netstat -ano | Select-String ":3000"
```

Pare apenas os processos locais correspondentes ao FastAPI/Next.js:

```powershell
Stop-Process -Id <PID> -Force
```

O PostgreSQL local pode continuar rodando para desenvolvimento. Para parar:

```powershell
docker compose stop postgres
```

Para resetar dados locais, use apenas se quiser apagar o volume local:

```powershell
docker compose down -v
```

## 14. Regras de seguranca

- Nao usar dados reais.
- Nao usar tokens reais.
- Nao criar recursos AWS reais.
- Nao ativar Cognito/S3/SQS reais neste fluxo.
- Nao versionar `.env`, `.env.local`, `.local/`, storage local ou fila local.
- Nao confiar em `organization_id` vindo do frontend.
- Validar sempre audit_log, tenant e RBAC antes de usar o MVP com demos.
