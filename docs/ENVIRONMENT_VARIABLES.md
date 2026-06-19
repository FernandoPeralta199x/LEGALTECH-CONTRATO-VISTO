# Variaveis De Ambiente

Este documento organiza as variaveis do LegalTech AWS V2 por componente e por
ambiente. Todos os valores exibidos em exemplos sao ficticios.

## Ambientes

- `local`: usado em desenvolvimento com Docker/PostgreSQL, JWT dev, storage
  local e fila local.
- `dev`: ambiente AWS de desenvolvimento, com Cognito e recursos isolados.
- `staging`: validacao antes de producao, proximo de prod.
- `prod`: producao, sem JWT dev e com controles de seguranca completos.

Regra principal: secrets reais nunca devem entrar em `.env.example`, README,
docs, codigo ou testes.

## Backend/API

| Variavel | Obrigatoria | Ambientes | Observacao |
| --- | --- | --- | --- |
| `APP_ENV` | Sim | todos | `local`, `dev`, `staging` ou `prod`. |
| `APP_NAME` | Sim | todos | Nome logico da API. |
| `APP_VERSION` | Nao | todos | Versao exibida pela aplicacao. |
| `ENABLE_DOCS` | Nao | todos | Em producao, avaliar `false`. |
| `LOG_LEVEL` | Sim | todos | `INFO` por padrao. Nao usar logs com dados sensiveis. |
| `CORS_ALLOWED_ORIGINS` | Sim | todos | Lista separada por virgula. Use apenas origens conhecidas do frontend. |
| `DATABASE_URL` | Sim | todos | URL do PostgreSQL. Valor real deve ficar fora do Git. |
| `AUTH_PROVIDER` | Sim | todos | `dev_jwt` apenas local; `cognito` em AWS. |
| `DEV_JWT_ENABLED` | Sim | todos | `true` apenas com `APP_ENV=local`. |
| `DEV_JWT_SECRET` | Local | local | Segredo ficticio local. Proibido em staging/prod. |
| `DEV_JWT_ISSUER` | Local | local | Issuer local para tokens dev. |
| `DEV_JWT_AUDIENCE` | Local | local | Audience local para tokens dev. |
| `COGNITO_REGION` | AWS | dev/staging/prod | Regiao do User Pool. |
| `COGNITO_USER_POOL_ID` | AWS | dev/staging/prod | ID do User Pool. |
| `COGNITO_CLIENT_ID` | AWS | dev/staging/prod | App client sem secret no frontend. |
| `COGNITO_ISSUER` | AWS | dev/staging/prod | Pode ser derivado de regiao e pool. |
| `COGNITO_JWKS_URL` | AWS | dev/staging/prod | Pode ser derivado do issuer. |
| `COGNITO_ORGANIZATION_CLAIM` | Sim | todos | Claim confiavel de tenant. |
| `COGNITO_ROLE_CLAIM` | Sim | todos | Claim de papel/grupo. |
| `COGNITO_TOKEN_USE` | Sim | todos | `id` ou `access`, conforme estrategia. |
| `STORAGE_BACKEND` | Sim | todos | `local` ou `s3`. |
| `LOCAL_UPLOAD_ROOT` | Local | local | Pasta local ignorada pelo Git. |
| `MAX_UPLOAD_SIZE_BYTES` | Sim | todos | Limite de upload. |
| `S3_DOCUMENTS_BUCKET` | AWS | dev/staging/prod | Bucket privado. |
| `AWS_REGION` | Sim | todos | Regiao padrao AWS. |
| `AWS_ENDPOINT_URL` | Nao | local/dev | Usado para LocalStack ou compatibilidade. |
| `PRESIGNED_URL_EXPIRES_SECONDS` | Sim | todos | Expiracao de presigned URLs. |
| `QUEUE_BACKEND` | Sim | todos | `local` ou `sqs`. |
| `LOCAL_QUEUE_PATH` | Local | local | Fila local JSONL ignorada pelo Git. |
| `SQS_DOCUMENT_PROCESSING_QUEUE_URL` | AWS | dev/staging/prod | Fila de processamento de documentos. |
| `SQS_TRIAGE_QUEUE_URL` | Futuro | dev/staging/prod | Fila futura de triagem. |
| `SQS_EXTERNAL_COLLECTION_QUEUE_URL` | Futuro | dev/staging/prod | Fila futura de coleta externa. |
| `SQS_CONTRACT_ANALYSIS_QUEUE_URL` | Futuro | dev/staging/prod | Fila futura de analise contratual. |
| `SQS_COMPLIANCE_QUEUE_URL` | Futuro | dev/staging/prod | Fila futura de compliance. |
| `SQS_REPORT_QUEUE_URL` | Futuro | dev/staging/prod | Fila futura de relatorios. |
| `SECRETS_EXTERNAL_APIS_NAME` | Futuro | dev/staging/prod | Nome do secret, nao o valor. |
| `OPENAI_API_SECRET_NAME` | Futuro | dev/staging/prod | Nome do secret, nao a chave. |

Observacao de compatibilidade: a API tambem aceita
`PRESIGNED_URL_EXPIRES_IN_SECONDS` para preservar configuracoes locais antigas.
Preferir `PRESIGNED_URL_EXPIRES_SECONDS` em novos ambientes.

## Frontend

| Variavel | Obrigatoria | Ambientes | Observacao |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | Sim | todos | URL publica da API. |
| `NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK` | Sim | todos | `true` apenas para local/dev controlado. |
| `NEXT_PUBLIC_APP_ENV` | Sim | todos | Ambiente exibido/consumido pela UI. |
| `NEXT_PUBLIC_APP_NAME` | Sim | todos | Nome publico da aplicacao. |

Atenção: variáveis NEXT_PUBLIC_* são expostas no navegador. Nunca coloque secrets, tokens, senhas ou dados sensíveis nelas.

## AWS Futura

| Variavel | Obrigatoria | Ambientes | Observacao |
| --- | --- | --- | --- |
| `AWS_ACCOUNT_ID` | AWS | dev/staging/prod | Conta alvo. |
| `AWS_REGION` | AWS | dev/staging/prod | Regiao padrao. |
| `AWS_PROFILE` | Local operator | dev/staging/prod | Perfil local para operadores. |
| `PROJECT_NAME` | AWS | dev/staging/prod | Prefixo dos recursos. |
| `ENVIRONMENT` | AWS | dev/staging/prod | Ambiente alvo. |
| `DOMAIN_NAME` | Futuro | staging/prod | Dominio publico. |
| `ACM_CERTIFICATE_ARN` | Futuro | staging/prod | Certificado gerenciado. |
| `CLOUDFRONT_DISTRIBUTION_ID` | Futuro | staging/prod | Distribuicao do frontend. |

## Politicas Por Ambiente

### local

- `AUTH_PROVIDER=dev_jwt`
- `DEV_JWT_ENABLED=true`
- `CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://192.168.0.102:3000`
- `STORAGE_BACKEND=local`
- `QUEUE_BACKEND=local`
- PostgreSQL via Docker
- Sem AWS real

### dev

- `AUTH_PROVIDER=cognito`
- `DEV_JWT_ENABLED=false`
- Recursos AWS isolados de desenvolvimento
- Mock fallback do frontend permitido apenas se documentado

### staging

- `AUTH_PROVIDER=cognito`
- `DEV_JWT_ENABLED=false`
- Configuracao proxima de producao
- Mock fallback desabilitado
- Dados reais somente se aprovados e minimizados

### prod

- `AUTH_PROVIDER=cognito`
- `DEV_JWT_ENABLED=false`
- S3 privado
- Secrets Manager
- Logs sanitizados
- Backups e monitoramento habilitados
- Nenhum mock ou segredo ficticio operacional

## Validacao Local

```powershell
python scripts/validate_env.py --env-file .env.example --environment local --target backend
python scripts/validate_env.py --env-file apps/frontend/.env.example --environment local --target frontend
python scripts/validate_env.py --env-file infra/aws/env.example --environment staging --target aws
python scripts/check_project_security.py .
```
