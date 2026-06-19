# LegalTech API

Backend inicial em FastAPI para o projeto LegalTech AWS V2.

Esta entrega cria apenas a base da API:

- aplicacao FastAPI;
- endpoint `GET /health`;
- configuracao central com Pydantic Settings;
- estrutura inicial de banco com SQLAlchemy;
- configuracao Alembic com migrations incrementais;
- models iniciais do MVP com `organization_id` nas tabelas sensiveis;
- camada inicial de schemas, repositories e services para clients e cases;
- rotas CRUD iniciais para clients e cases em `/api/v1`;
- rotas iniciais de metadados de documents em `/api/v1`;
- rota `GET /api/v1/me` para validar JWT e retornar a sessao autenticada sem expor claims completas;
- estrutura JWT dev local e Cognito/JWKS para `Authorization: Bearer <jwt>`;
- RBAC consultando `roles_permissions`;
- matriz base de permissoes por papel e seed interno de `roles_permissions`;
- audit_log avancado com sanitizacao LGPD para eventos sensiveis;
- rotas administrativas somente leitura para consulta de audit_log;
- upload local/mock de documents para desenvolvimento;
- abstracao de storage de documents com modo `local` e modo `s3`;
- geracao preparada de URL temporaria de download para documents;
- normalizacao local de documents para Markdown antes do worker gerar chunks;
- base local/mock de document_chunks e document_embeddings, sem IA externa;
- fila local/mock para processamento de documents e worker inicial local;
- README com comandos locais.

Nao foram implementados OCR real, IA real, RAG real, AWS SQS real, Lambda, agentes completos ou APIs externas.
O modo S3 esta preparado para ambiente futuro AWS ou LocalStack, mas os testes nao exigem AWS real.
As rotas sensiveis exigem JWT validado pelo provider configurado em `AUTH_PROVIDER` e permissao registrada em `roles_permissions`.

## Requisitos

- Python 3.12+
- Docker Desktop ou Docker Engine com Docker Compose
- PostgreSQL local ou remoto para migrations
- Extensoes PostgreSQL `uuid-ossp` e `vector` disponiveis no banco

## Configuracao local

Crie um ambiente virtual dentro de `legaltech-aws/apps/api`:

```bash
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

O arquivo `apps/api/.env.example.local` contem variaveis ficticias para o PostgreSQL local do `docker-compose.yml`.
Para a matriz completa de variaveis e ambientes, consulte `docs/ENVIRONMENT_VARIABLES.md`.

Exemplo local, sem versionar segredos:

```env
PROJECT_NAME=legaltech
ENVIRONMENT=local
APP_ENV=local
APP_NAME=legaltech-api
APP_VERSION=0.1.0
ENABLE_DOCS=true
LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://192.168.0.102:3000
AUTH_PROVIDER=dev_jwt
DATABASE_URL=postgresql+psycopg://legaltech:legaltech_dev@localhost:5432/legaltech
AWS_REGION=sa-east-1
AWS_ACCOUNT_ID=000000000000
AWS_PROFILE=legaltech-local
AWS_ENDPOINT_URL=
COGNITO_REGION=sa-east-1
COGNITO_USER_POOL_ID=
COGNITO_CLIENT_ID=
COGNITO_ISSUER=
COGNITO_JWKS_URL=
COGNITO_ORGANIZATION_CLAIM=custom:organization_id
COGNITO_ROLE_CLAIM=custom:role
COGNITO_TOKEN_USE=id
DEV_JWT_ENABLED=true
DEV_JWT_SECRET=fictitious-local-dev-secret-32-bytes-minimum
DEV_JWT_ISSUER=legaltech-local-dev
DEV_JWT_AUDIENCE=legaltech-local-api
LOCAL_UPLOAD_ROOT=storage/local_uploads
MAX_UPLOAD_SIZE_BYTES=10485760
STORAGE_BACKEND=local
S3_DOCUMENTS_BUCKET=legaltech-local-documents-placeholder
PRESIGNED_URL_EXPIRES_SECONDS=900
LOCAL_PROCESSING_MAX_TEXT_CHARS=50000
DOCUMENT_PROCESSING_MAX_ATTEMPTS=3
QUEUE_BACKEND=local
LOCAL_QUEUE_PATH=storage/local_queue/document_processing.jsonl
SQS_DOCUMENT_PROCESSING_QUEUE_URL=
SQS_TRIAGE_QUEUE_URL=
SQS_EXTERNAL_COLLECTION_QUEUE_URL=
SQS_CONTRACT_ANALYSIS_QUEUE_URL=
SQS_COMPLIANCE_QUEUE_URL=
SQS_REPORT_QUEUE_URL=
SECRETS_EXTERNAL_APIS_NAME=legaltech/local/external-apis
OPENAI_API_SECRET_NAME=legaltech/local/openai
```

Para usar o fluxo local completo, copie o exemplo para `.env` dentro de `apps/api`. O arquivo `.env` segue ignorado pelo Git.

## PostgreSQL local com Docker

Na raiz do repositorio, suba o PostgreSQL local:

```bash
docker compose up -d postgres
```

O compose usa:

```text
Banco: legaltech
Usuario: legaltech
Senha: legaltech_dev
Porta: 5432
Imagem: pgvector/pgvector:pg16
Volume: legaltech_postgres_data
```

As credenciais acima sao apenas ficticias para desenvolvimento local. Nao use esses valores em producao.

Verificar saude do banco:

```bash
docker compose ps
docker compose exec postgres pg_isready -U legaltech -d legaltech
```

Confirmar extensoes disponiveis:

```bash
docker compose exec postgres psql -U legaltech -d legaltech -c "SELECT extname FROM pg_extension WHERE extname IN ('uuid-ossp', 'vector') ORDER BY extname;"
```

## Rodar localmente

```bash
uvicorn src.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Validar token/sessao local:

```bash
curl http://127.0.0.1:8000/api/v1/me \
  -H "Authorization: Bearer $TOKEN"
```

Essa rota valida o JWT no backend e retorna apenas `id`, `email`, `organization_id` e `role`.
Ela nao retorna claims completas, token, segredo nem payload sensivel.

Resposta esperada:

```json
{
  "success": true,
  "data": {
    "status": "ok",
    "service": "legaltech-api"
  }
}
```

Rotas iniciais de clients:

```text
GET    /api/v1/clients
POST   /api/v1/clients
GET    /api/v1/clients/{client_id}
PATCH  /api/v1/clients/{client_id}
```

Rotas iniciais de cases:

```text
GET    /api/v1/cases
POST   /api/v1/cases
GET    /api/v1/cases/{case_id}
PATCH  /api/v1/cases/{case_id}
```

Rotas iniciais de documents:

```text
GET    /api/v1/documents
POST   /api/v1/documents
POST   /api/v1/documents/upload
GET    /api/v1/documents/{document_id}/download-url
POST   /api/v1/documents/{document_id}/process-local
POST   /api/v1/documents/{document_id}/enqueue-processing
GET    /api/v1/documents/{document_id}/chunks
GET    /api/v1/documents/{document_id}
PATCH  /api/v1/documents/{document_id}
```

O endpoint `/api/v1/documents/upload` continua funcionando em modo local/mock por padrao. Com `STORAGE_BACKEND=s3`, o backend fica preparado para usar S3 compativel via boto3.
O processamento local cria chunks e embeddings fake/deterministicos para desenvolvimento a partir de Markdown normalizado quando o arquivo local estiver disponivel. Ele nao chama OpenAI, Claude, AWS Bedrock ou qualquer IA externa, e nao implementa OCR nem RAG real.
A fila local/mock permite enfileirar processamento de documents sem AWS real. O worker local consome jobs com IDs e revalida tenant/case/document no banco antes de chamar o processamento local.

Importante: `organization_id` e `user_id` nao fazem parte dos payloads. Eles sao derivados das claims do JWT validado.
As rotas reais usam `DATABASE_URL`; para chamadas locais fora dos testes, aplique as migrations em um PostgreSQL disponivel e cadastre permissoes em `roles_permissions`.

Header esperado:

```text
Authorization: Bearer <jwt>
```

## Autenticacao: dev_jwt e Cognito

O backend suporta dois providers de autenticacao por configuracao:

```env
AUTH_PROVIDER=dev_jwt
```

Use somente em `APP_ENV=local`, com `DEV_JWT_ENABLED=true`, para smoke tests e desenvolvimento local sem Cognito real. Tokens dev usam segredo ficticio local e nao devem existir em producao.

```env
AUTH_PROVIDER=cognito
```

Prepara validacao de JWT do AWS Cognito. Neste modo o backend valida assinatura via JWKS, `iss`, `aud` ou `client_id`, `exp`, `token_use` e algoritmo `RS256`. Tokens `alg=none`, tokens dev/HS256, issuer invalido, audience invalida, expirados ou sem claim de tenant sao rejeitados.

Politica por ambiente:

```text
local    AUTH_PROVIDER=dev_jwt   DEV_JWT_ENABLED=true
dev      AUTH_PROVIDER=cognito   DEV_JWT_ENABLED=false
staging  AUTH_PROVIDER=cognito   DEV_JWT_ENABLED=false
prod     AUTH_PROVIDER=cognito   DEV_JWT_ENABLED=false
```

O caminho Cognito esta preparado para AWS futura, mas este projeto nao cria User Pool, App Client ou JWKS real nesta etapa.

Variaveis Cognito esperadas, com valores ficticios em exemplos:

```env
COGNITO_REGION=sa-east-1
COGNITO_USER_POOL_ID=sa-east-1_EXAMPLE
COGNITO_CLIENT_ID=example-client-id
COGNITO_ISSUER=https://cognito-idp.sa-east-1.amazonaws.com/sa-east-1_EXAMPLE
COGNITO_JWKS_URL=https://cognito-idp.sa-east-1.amazonaws.com/sa-east-1_EXAMPLE/.well-known/jwks.json
COGNITO_ORGANIZATION_CLAIM=custom:organization_id
COGNITO_ROLE_CLAIM=custom:role
COGNITO_TOKEN_USE=id
```

## Configuracao AWS futura

Esta API reconhece variaveis de preparacao para AWS sem exigir recursos reais:

```env
STORAGE_BACKEND=s3
S3_DOCUMENTS_BUCKET=legaltech-staging-documents
QUEUE_BACKEND=sqs
SQS_DOCUMENT_PROCESSING_QUEUE_URL=https://sqs.sa-east-1.amazonaws.com/000000000000/legaltech-staging-document-processing
SECRETS_EXTERNAL_APIS_NAME=legaltech/staging/external-apis
OPENAI_API_SECRET_NAME=legaltech/staging/openai
```

Use apenas nomes logicos de secrets no `.env`; valores reais devem ficar em Secrets Manager ou mecanismo equivalente. Antes de qualquer deploy futuro, siga:

```powershell
python ..\..\scripts\validate_env.py --env-file ..\..\.env.example --environment local --target backend
python ..\..\scripts\check_project_security.py ..\..
```

`COGNITO_ISSUER` e `COGNITO_JWKS_URL` podem ficar vazios quando `COGNITO_REGION` e `COGNITO_USER_POOL_ID` forem suficientes para derivar os valores. Em testes, a API usa JWKS mockado em memoria e nao chama AWS real.

Claims esperadas por padrao:

```text
sub
email
custom:organization_id
custom:role
token_use=id
aud=<COGNITO_CLIENT_ID>
```

`COGNITO_ORGANIZATION_CLAIM`, `COGNITO_ROLE_CLAIM` e `COGNITO_TOKEN_USE` podem ser ajustados via `.env`.

Permissoes usadas pelas rotas atuais:

```text
clients:read
clients:write
cases:read
cases:write
documents:read
documents:write
documents:upload
documents:download
documents:process
document_chunks:read
audit:read
```

Se a organizacao local ja tiver sido populada antes desta permissao existir, rode novamente o seed interno de `roles_permissions`. O seed e idempotente e adiciona apenas permissoes faltantes.

Papeis base preparados no seed interno:

```text
owner
admin
analyst
client
support
```

Operacoes de leitura e escrita em `clients` e `cases` registram eventos via `AuditLogService`.
Operacoes de leitura e escrita em `documents` tambem registram eventos via `AuditLogService`.

Rotas administrativas de auditoria:

```text
GET /api/v1/audit
GET /api/v1/audit/{audit_id}
```

Essas rotas exigem `audit:read`, filtram sempre pelo `organization_id` do JWT e nao permitem criar, alterar ou apagar registros de auditoria.

## Auditoria e LGPD

O modulo `src/modules/audit` padroniza actions, repository, service, schemas e rotas somente leitura. Eventos de auditoria sao append-only no comportamento da aplicacao e registram metadados tecnicos seguros:

```text
organization_id
user_id
action
entity_type
entity_id
ip_address
user_agent
metadata
created_at
```

Actions sensiveis atuais:

```text
clients.create
clients.update
clients.read
cases.create
cases.update
cases.read
documents.create
documents.update
documents.upload
documents.download_url
documents.process_requested
documents.process_started
documents.process_completed
documents.process_failed
documents.conversion_started
documents.conversion_completed
documents.conversion_failed
documents.conversion_requires_ocr
agent_execution.created
agent_execution.started
agent_execution.completed
agent_execution.failed
agent_execution.skipped
rbac.denied
```

O `AuditLogService` sanitiza `metadata` antes de persistir, mascarando ou removendo valores como CPF/CNPJ completo, JWT, `Authorization: Bearer`, senha, token, chave API, segredo, texto integral de contrato/documento e conteudo bruto. Use apenas IDs tecnicos, status, `job_id`, `case_id`, `document_id`, provider logico e erros resumidos.

Consultar auditoria localmente:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/audit?action=documents.upload&page=1&page_size=20" `
  -Method Get `
  -Headers @{ Authorization = "Bearer $TOKEN" }
```

Filtros disponiveis:

```text
action
entity_type
entity_id
user_id
date_from
date_to
page
page_size
```

## Documents storage e download URL

As rotas de documents cadastram metadados no banco e usam uma camada abstrata de storage. Por padrao, `STORAGE_BACKEND=local` salva arquivos em `apps/api/storage/local_uploads/`.

A pasta `apps/api/storage/local_uploads/` e ignorada pelo Git. Nao coloque documentos reais ou sensiveis ali.

Configuracao local/mock:

```env
STORAGE_BACKEND=local
LOCAL_UPLOAD_ROOT=storage/local_uploads
MAX_UPLOAD_SIZE_BYTES=10485760
PRESIGNED_URL_EXPIRES_SECONDS=900
```

Configuracao futura S3 ou LocalStack, com valores ficticios:

```env
STORAGE_BACKEND=s3
S3_DOCUMENTS_BUCKET=legaltech-dev-documents
AWS_REGION=sa-east-1
AWS_ENDPOINT_URL=http://localhost:4566
PRESIGNED_URL_EXPIRES_SECONDS=900
```

Nao coloque `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` ou credenciais reais em arquivos versionados. Em AWS real, use IAM role, Secrets Manager, SSM ou configuracao segura do ambiente.

Criar document metadata:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "case-uuid",
    "filename": "contrato.pdf",
    "content_type": "application/pdf",
    "size_bytes": 1024000,
    "file_hash": "sha256-opcional",
    "metadata": {
      "source": "metadata_only"
    }
  }'
```

Listar documents:

```bash
curl "http://127.0.0.1:8000/api/v1/documents?case_id=case-uuid" \
  -H "Authorization: Bearer $TOKEN"
```

Atualizar metadados:

```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/documents/document-uuid \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "uploaded",
    "metadata": {
      "review": "pending"
    }
  }'
```

Campos como `organization_id`, `uploaded_by`, `storage_bucket` e `storage_key` nao sao aceitos no payload. O `organization_id` vem do JWT e os campos de storage permanecem internos, definidos pela camada de storage configurada no backend.

Upload local/mock de documento:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "case_id=case-uuid" \
  -F "metadata={\"source\":\"local_mock\"}" \
  -F "file=@./contrato-exemplo.pdf;type=application/pdf"
```

PowerShell usando `curl.exe`:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/documents/upload" `
  -H "Authorization: Bearer $TOKEN" `
  -F "case_id=case-uuid" `
  -F "metadata={""source"":""local_mock""}" `
  -F "file=@.\contrato-exemplo.pdf;type=application/pdf"
```

Extensoes permitidas no storage local/mock:

```text
.pdf
.docx
.txt
.md
```

O limite padrao e `10485760` bytes e pode ser ajustado por `MAX_UPLOAD_SIZE_BYTES` no `.env` local. `LOCAL_UPLOAD_ROOT` deve apontar para uma pasta local de desenvolvimento, por padrao `storage/local_uploads`.

Gerar URL temporaria de download:

```bash
curl http://127.0.0.1:8000/api/v1/documents/document-uuid/download-url \
  -H "Authorization: Bearer $TOKEN"
```

Resposta esperada:

```json
{
  "success": true,
  "data": {
    "url": "https://s3-presigned-url-ou-url-local-mock",
    "expires_in_seconds": 900,
    "method": "GET"
  },
  "message": "URL temporaria gerada com sucesso."
}
```

A resposta publica nao inclui `storage_key`, bucket nem caminho local interno. O backend valida `document_id` pelo `organization_id` do JWT antes de gerar a URL e registra `audit_log` com a acao `documents.download_url`.

## Normalizacao local para Markdown

Antes de gerar chunks pelo worker local, o backend tenta converter o arquivo original para Markdown padronizado e salvar o resultado no storage local/mock. Esse Markdown e a entrada preferencial para chunks e embeddings fake.

Formatos suportados nesta etapa:

```text
.txt   texto simples normalizado
.md    Markdown existente normalizado
.docx  paragrafos e tabelas simples extraidos para Markdown
.pdf   apenas PDF com texto extraivel
```

PDF escaneado ou arquivo sem texto extraivel nao passa por OCR nesta etapa. Nesses casos, o backend marca `conversion_status=requires_ocr`, registra auditoria segura e o worker falha de forma controlada para evitar chunks vazios.

Campos de normalizacao em `documents`:

```text
conversion_status
normalized_markdown_storage_key
normalized_markdown_sha256
normalized_markdown_size_bytes
conversion_error_summary
converted_at
```

Status de conversao:

```text
pending
converting
converted
failed
requires_ocr
```

O caminho interno `normalized_markdown_storage_key` nao deve ser exposto em respostas publicas. As respostas de documents exibem apenas metadados seguros, como status, hash, tamanho e erro resumido.

Eventos de auditoria da normalizacao:

```text
documents.conversion_started
documents.conversion_completed
documents.conversion_failed
documents.conversion_requires_ocr
```

Os eventos registram apenas IDs, extensao, status, tamanho, hash e codigo de erro seguro. O conteudo integral do Markdown, contrato, CPF/CNPJ, token ou paths locais internos nao sao registrados em `audit_log`.

## Document processing local/mock

O processamento local serve apenas para preparar a base de `document_chunks` e `document_embeddings`. Ele recebe texto simples enviado pela API ou Markdown normalizado pelo worker local, divide em chunks e gera embeddings fake/deterministicos de 1536 dimensoes. Nao ha chamada para OpenAI, Claude, Bedrock, OCR, RAG real, AWS SQS real ou Lambda.

Configuracao:

```env
LOCAL_PROCESSING_MAX_TEXT_CHARS=50000
DOCUMENT_PROCESSING_MAX_ATTEMPTS=3
QUEUE_BACKEND=local
LOCAL_QUEUE_PATH=storage/local_queue/document_processing.jsonl
```

Processar texto local/mock:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents/document-uuid/process-local \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Texto ficticio para processamento local em chunks.",
    "chunk_size_chars": 1200,
    "chunk_overlap_chars": 120,
    "metadata": {
      "source": "local_mock"
    }
  }'
```

PowerShell:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/documents/document-uuid/process-local" `
  -Method Post `
  -Headers @{ Authorization = "Bearer $TOKEN" } `
  -ContentType "application/json" `
  -Body (@{
    text = "Texto ficticio para processamento local em chunks."
    chunk_size_chars = 1200
    chunk_overlap_chars = 120
    metadata = @{ source = "local_mock" }
  } | ConvertTo-Json)
```

Listar chunks do documento:

```bash
curl http://127.0.0.1:8000/api/v1/documents/document-uuid/chunks \
  -H "Authorization: Bearer $TOKEN"
```

Regras importantes:

- `organization_id` nunca e aceito no payload;
- o documento e buscado pelo `organization_id` do JWT;
- `documents:process` protege o processamento local;
- `document_chunks:read` protege a leitura de chunks;
- o `audit_log` registra contagens e metadados tecnicos, sem registrar o texto integral do documento.

## Fila local/mock e worker

O endpoint de enqueue publica um job local/mock com apenas IDs:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents/document-uuid/enqueue-processing \
  -H "Authorization: Bearer $TOKEN"
```

PowerShell:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/documents/document-uuid/enqueue-processing" `
  -Method Post `
  -Headers @{ Authorization = "Bearer $TOKEN" }
```

Resposta esperada:

```json
{
  "success": true,
  "data": {
    "job_id": "job-uuid",
    "status": "queued",
    "queue_backend": "local",
    "document_id": "document-uuid"
  },
  "message": "Processamento de documento enfileirado com sucesso."
}
```

Rodar o worker local uma vez, a partir de `legaltech-aws/apps/api`:

```powershell
$env:PYTHONPATH=".;..\.."
.\.venv\Scripts\python.exe ..\..\workers\document_processing\worker.py --once
```

Ou por modulo, a partir de `legaltech-aws`:

```powershell
$env:PYTHONPATH="apps/api;."
apps\api\.venv\Scripts\python.exe -m workers.document_processing.worker --once
```

O worker:

- consome jobs de `apps/api/storage/local_queue/document_processing.jsonl`;
- revalida `organization_id`, `case_id` e `document_id` no banco antes de processar;
- registra e atualiza `agent_executions` com `queued`, `running`, `completed`, `failed`, `retrying` ou `skipped`;
- atualiza `documents.status` para `processing`, `processed` ou `failed`;
- evita duplicidade basica usando `agent_executions.job_id` concluido e chunks ja existentes;
- respeita `attempt` do job e o limite `DOCUMENT_PROCESSING_MAX_ATTEMPTS`;
- chama o processamento local com texto ficticio de desenvolvimento;
- registra `audit_log` de inicio, sucesso, falha ou skip;
- nao transporta nem registra conteudo integral do documento.

Payload interno do job local/mock:

```json
{
  "job_id": "job-uuid",
  "job_type": "document_processing",
  "agent_type": "document_processing_local",
  "organization_id": "organization-uuid",
  "case_id": "case-uuid",
  "document_id": "document-uuid",
  "attempt": 1,
  "requested_by": "user-uuid",
  "metadata": {
    "source": "api"
  },
  "created_at": "2026-05-24T00:00:00Z"
}
```

O payload acima nao deve conter texto integral, arquivo, contrato, CPF, token ou qualquer dado sensivel completo.

Configuracao futura SQS/LocalStack, com valores ficticios:

```env
QUEUE_BACKEND=sqs
SQS_DOCUMENT_PROCESSING_QUEUE_URL=http://localhost:4566/000000000000/legaltech-document-processing-queue
AWS_REGION=sa-east-1
AWS_ENDPOINT_URL=http://localhost:4566
```

Nao configure credenciais AWS reais em arquivos versionados. A implementacao SQS esta preparada para testes com client mockado ou LocalStack futuro.

## Seed interno de permissoes

O seed de `roles_permissions` e um comando administrativo interno, nao uma rota publica. Ele popula apenas permissoes faltantes para uma organizacao existente e registra auditoria quando cria novas permissoes.

Para testar localmente, aplique primeiro as migrations e crie a organizacao tecnica ficticia:

```bash
docker compose exec -T postgres psql -U legaltech -d legaltech < database/local/seed_example_organization.sql
```

No PowerShell, execute a partir da raiz do repositorio:

```powershell
Get-Content database\local\seed_example_organization.sql | docker compose exec -T postgres psql -U legaltech -d legaltech
```

Esse SQL cria apenas dados tecnicos ficticios:

```text
organization_id: 11111111-1111-4111-8111-111111111111
user_id:         22222222-2222-4222-8222-222222222222
email:           dev.local@example.test
role:            admin
```

Dry run, sem persistir:

```bash
python -m src.modules.admin.seed_roles_permissions \
  --organization-id 11111111-1111-4111-8111-111111111111 \
  --dry-run
```

Aplicar no banco configurado em `DATABASE_URL`:

```bash
python -m src.modules.admin.seed_roles_permissions \
  --organization-id 11111111-1111-4111-8111-111111111111
```

Registrar usuario interno responsavel pela auditoria, se existir na tabela `users`:

```bash
python -m src.modules.admin.seed_roles_permissions \
  --organization-id 11111111-1111-4111-8111-111111111111 \
  --actor-user-id 22222222-2222-4222-8222-222222222222
```

Use UUIDs reais apenas no ambiente local/dev apropriado. Nao coloque esses valores no codigo.

Conferir permissoes populadas no banco local:

```bash
docker compose exec postgres psql -U legaltech -d legaltech -c "SELECT role, COUNT(*) FROM roles_permissions WHERE organization_id = '11111111-1111-4111-8111-111111111111' GROUP BY role ORDER BY role;"
```

## JWT local de desenvolvimento

Para testar rotas reais localmente sem Cognito, habilite apenas em `APP_ENV=local`:

```env
AUTH_PROVIDER=dev_jwt
DEV_JWT_ENABLED=true
DEV_JWT_SECRET=fictitious-local-dev-secret-32-bytes-minimum
DEV_JWT_ISSUER=legaltech-local-dev
DEV_JWT_AUDIENCE=legaltech-local-api
```

O segredo acima e ficticio e serve apenas para desenvolvimento local. Nao reutilize em outro ambiente.

Gerar token local:

```bash
python -m src.modules.admin.dev_jwt \
  --organization-id 11111111-1111-4111-8111-111111111111 \
  --user-id 22222222-2222-4222-8222-222222222222 \
  --email dev.local@example.test \
  --role admin
```

PowerShell:

```powershell
$TOKEN = python -m src.modules.admin.dev_jwt `
  --organization-id 11111111-1111-4111-8111-111111111111 `
  --user-id 22222222-2222-4222-8222-222222222222 `
  --email dev.local@example.test `
  --role admin
```

As claims do token carregam `organization_id`, `user_id` e `role`. Nao envie `organization_id` nos payloads de frontend.

Para validar o caminho Cognito sem conta AWS real, rode os testes com JWKS mockado:

```bash
python -m unittest tests.test_cognito_auth -v
```

Esses testes geram uma chave RSA efemera em memoria, montam um JWKS ficticio, assinam tokens Cognito-like e validam issuer, audience/client_id, expiracao, algoritmo, tenant claim e RBAC. Nao ha chamada para AWS real.

## Smoke local de clients e cases

Fluxo end-to-end local:

```powershell
cd legaltech-aws
docker compose up -d postgres

cd apps\api
Copy-Item .env.example.local .env
$env:DATABASE_URL="postgresql+psycopg://legaltech:legaltech_dev@localhost:5432/legaltech"
alembic upgrade head

cd ..\..
Get-Content database\local\seed_example_organization.sql | docker compose exec -T postgres psql -U legaltech -d legaltech

cd apps\api
python -m src.modules.admin.seed_roles_permissions `
  --organization-id 11111111-1111-4111-8111-111111111111 `
  --actor-user-id 22222222-2222-4222-8222-222222222222

$TOKEN = python -m src.modules.admin.dev_jwt `
  --organization-id 11111111-1111-4111-8111-111111111111 `
  --user-id 22222222-2222-4222-8222-222222222222 `
  --email dev.local@example.test `
  --role admin

uvicorn src.main:app --reload
```

Em outro terminal, execute:

```powershell
cd legaltech-aws\apps\api
$TOKEN = python -m src.modules.admin.dev_jwt `
  --organization-id 11111111-1111-4111-8111-111111111111 `
  --user-id 22222222-2222-4222-8222-222222222222 `
  --email dev.local@example.test `
  --role admin

python -m src.modules.admin.smoke_clients_cases --token $TOKEN
```

O smoke executa:

```text
POST /api/v1/clients
GET  /api/v1/clients
POST /api/v1/cases
GET  /api/v1/cases
```

Exemplo curl:

```bash
TOKEN="$(python -m src.modules.admin.dev_jwt \
  --organization-id 11111111-1111-4111-8111-111111111111 \
  --user-id 22222222-2222-4222-8222-222222222222 \
  --email dev.local@example.test \
  --role admin)"

curl -X POST http://127.0.0.1:8000/api/v1/clients \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Cliente Local Exemplo","document":"00000000000","email":"cliente.local@example.test","phone":"+5500000000000","metadata":{"source":"local_curl"}}'

curl http://127.0.0.1:8000/api/v1/clients \
  -H "Authorization: Bearer $TOKEN"
```

Exemplo PowerShell:

```powershell
$Headers = @{ Authorization = "Bearer $TOKEN" }
$Client = Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/clients" `
  -Method Post `
  -Headers $Headers `
  -ContentType "application/json" `
  -Body (@{
    name = "Cliente Local Exemplo"
    document = "00000000000"
    email = "cliente.local@example.test"
    phone = "+5500000000000"
    metadata = @{ source = "local_powershell" }
  } | ConvertTo-Json)

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/clients" `
  -Method Get `
  -Headers $Headers

$Case = Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/cases" `
  -Method Post `
  -Headers $Headers `
  -ContentType "application/json" `
  -Body (@{
    client_id = $Client.data.id
    case_type = "contract_analysis"
    priority = "normal"
    metadata = @{ source = "local_powershell" }
  } | ConvertTo-Json)

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/cases" `
  -Method Get `
  -Headers $Headers
```

## Migrations

O Alembic esta configurado em `alembic.ini` e usa `DATABASE_URL` via Pydantic Settings.

Migrations existentes:

- `0001_initial_models.py`: organizations, users, clients, cases, documents, audit_log e agent_executions.
- `0002_remaining_mvp_models.py`: roles_permissions, case_parties, external_queries_cache, document_chunks, document_embeddings, human_reviews e reports.
- `0003_doc_md_norm.py`: campos nullable/seguros de normalizacao Markdown em documents.

Gerar uma nova revision a partir dos models:

```bash
alembic revision --autogenerate -m "descricao da mudanca"
```

Aplicar migrations no banco configurado:

```bash
alembic upgrade head
```

Ver migration atual:

```bash
alembic current
```

Gerar SQL sem aplicar no banco:

```bash
alembic upgrade head --sql
```

Fluxo completo para validar migrations no PostgreSQL local:

```bash
cd legaltech-aws/apps/api
export DATABASE_URL=postgresql+psycopg://legaltech:legaltech_dev@localhost:5432/legaltech
alembic upgrade head
alembic current
```

No PowerShell:

```powershell
cd legaltech-aws\apps\api
$env:DATABASE_URL="postgresql+psycopg://legaltech:legaltech_dev@localhost:5432/legaltech"
alembic upgrade head
alembic current
```

Para resetar apenas o banco local de desenvolvimento, remova o volume nomeado na raiz do repositorio:

```bash
docker compose down -v
```

## Testes

```bash
python -m unittest discover -s tests -v
```

Testar apenas as rotas de clients/cases:

```bash
python -m unittest tests.test_clients_cases_routes -v
```

Testar auth/RBAC e auditoria:

```bash
python -m unittest tests.test_cognito_auth -v
python -m unittest tests.test_audit_lgpd -v
python -m unittest tests.test_auth_rbac_audit -v
python -m unittest tests.test_roles_permissions -v
python -m unittest tests.test_admin_seed_roles_permissions -v
```

Testar documents:

```bash
python -m unittest tests.test_documents_storage tests.test_documents_layers tests.test_documents_routes -v
```

Testar document processing:

```bash
python -m unittest tests.test_document_processing_layers tests.test_document_processing_routes -v
```

Testar normalizacao Markdown:

```bash
python -m unittest tests.test_document_normalization -v
```

Testar fila local/mock e worker:

```bash
python -m unittest tests.test_document_processing_queue_worker -v
```

Esses testes usam services/verifiers mockados via `dependency_overrides`, entao nao exigem conexao com banco ou Cognito real.

## Estrutura

```text
src/
├── core/
│   ├── auth.py
│   ├── config.py
│   ├── cognito.py
│   ├── jwks.py
│   ├── logging.py
│   ├── rbac.py
│   ├── security.py
│   └── tenant.py
├── db/
│   ├── base.py
│   └── session.py
├── models/
│   ├── agent_execution.py
│   ├── audit_log.py
│   ├── case.py
│   ├── case_party.py
│   ├── client.py
│   ├── document.py
│   ├── document_chunk.py
│   ├── document_embedding.py
│   ├── external_query_cache.py
│   ├── human_review.py
│   ├── mixins.py
│   ├── organization.py
│   ├── report.py
│   ├── role_permission.py
│   ├── types.py
│   └── user.py
├── modules/
│   ├── admin/
│   │   ├── dev_jwt.py
│   │   ├── seed_roles_permissions.py
│   │   └── smoke_clients_cases.py
│   ├── audit/
│   │   ├── actions.py
│   │   ├── repository.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── service.py
│   ├── agent_executions/
│   │   ├── idempotency.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   └── service.py
│   ├── cases/
│   │   ├── repository.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── service.py
│   ├── clients/
│   │   ├── repository.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── service.py
│   ├── documents/
│   │   ├── repository.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   └── storage.py
│   ├── document_processing/
│   │   ├── chunker.py
│   │   ├── fake_embeddings.py
│   │   ├── repository.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── service.py
│   ├── document_normalization/
│   │   ├── converter.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   └── service.py
│   ├── queues/
│   │   ├── local_queue.py
│   │   ├── publisher.py
│   │   ├── schemas.py
│   │   └── sqs_client.py
│   ├── common/
│   │   ├── exceptions.py
│   │   ├── identifiers.py
│   │   └── responses.py
│   ├── health/
│   │   └── router.py
│   └── roles/
│       ├── permissions.py
│       ├── repository.py
│       └── service.py
└── main.py
```

## Proximos passos

1. Validar migrations contra um PostgreSQL local com `uuid-ossp` e `pgvector`.
2. Rodar o seed interno de `roles_permissions` para cada organizacao de desenvolvimento.
3. Mapear usuario interno a partir de `sub`/Cognito e tabela `users`.
4. Adicionar `request_id`/correlation id para cruzar API, fila local e worker.
5. Criar administracao segura para futuras alteracoes de permissoes, com aprovacao e auditoria.
