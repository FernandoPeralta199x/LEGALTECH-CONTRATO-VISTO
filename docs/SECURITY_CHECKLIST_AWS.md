# Checklist De Seguranca AWS

Checklist de seguranca para a preparacao e futura implantacao AWS do LegalTech
AWS V2.

## Secrets

- [ ] `.env` real fora do Git.
- [ ] `.env.example` apenas com placeholders ficticios.
- [ ] Nenhum access key, secret key, token, senha ou chave privada em docs.
- [ ] Secrets reais em Secrets Manager ou mecanismo equivalente.
- [ ] Frontend sem qualquer secret ou client secret.

## Autenticacao E Tenant

- [ ] `AUTH_PROVIDER=dev_jwt` somente local.
- [ ] `DEV_JWT_ENABLED=false` em `dev`, `staging` e `prod`.
- [ ] Cognito valida assinatura via JWKS e algoritmo `RS256`.
- [ ] Tokens `alg=none` rejeitados.
- [ ] `issuer`, `audience/client_id`, `exp` e `token_use` validados.
- [ ] `organization_id` vem de claim confiavel ou resolucao server-side.
- [ ] Frontend nunca envia `organization_id` como fonte de verdade.

## Dados Sensiveis E LGPD

- [ ] Logs nao registram CPF/CNPJ completo.
- [ ] Logs nao registram JWT, senha, chave API ou contratos inteiros.
- [ ] Metadata de auditoria sanitizada.
- [ ] `audit_log` append-only no comportamento da aplicacao.
- [ ] Acoes sensiveis registram `organization_id`, `user_id`, action e entidade.
- [ ] Relatorios juridicos finais seguem com revisao humana.

## Banco

- [ ] Tabelas sensiveis possuem `organization_id`.
- [ ] RDS em subnets privadas.
- [ ] Security group do banco restrito.
- [ ] Backups automaticos habilitados.
- [ ] Snapshots antes de migrations criticas.
- [ ] Credenciais do banco fora do codigo.

## S3

- [ ] Buckets privados por ambiente.
- [ ] Block Public Access habilitado.
- [ ] Criptografia em repouso habilitada.
- [ ] Upload/download via presigned URL.
- [ ] TTL de presigned URL curto e configuravel.
- [ ] Caminhos internos locais nao expostos em resposta publica.

## SQS E Workers

- [ ] Jobs carregam apenas IDs e metadados minimos.
- [ ] Worker revalida tenant/case/document antes de processar.
- [ ] Retry e idempotencia por `job_id`.
- [ ] Dead-letter queue planejada.
- [ ] `agent_executions` registra estados.
- [ ] Falhas registram erro resumido, sem conteudo sensivel completo.

## IAM

- [ ] Role da API com minimo acesso necessario.
- [ ] Role do worker separada da role da API.
- [ ] Permissoes S3 restritas ao bucket do ambiente.
- [ ] Permissoes SQS restritas as filas do ambiente.
- [ ] Permissoes Secrets Manager restritas aos secrets necessarios.
- [ ] Sem credenciais AWS permanentes em servidor/aplicacao.

## Observabilidade

- [ ] Logs estruturados e sanitizados.
- [ ] Retencao de logs definida.
- [ ] Alarmes de erro e latencia.
- [ ] Alarmes de fila acumulada.
- [ ] Health checks monitorados.

## Validacao Local

```powershell
python scripts/check_project_security.py .
python scripts/validate_env.py --env-file .env.example --environment local --target backend
python scripts/validate_env.py --env-file infra/aws/env.example --environment staging --target aws
```
