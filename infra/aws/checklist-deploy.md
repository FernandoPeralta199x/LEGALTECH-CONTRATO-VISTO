# Checklist Antes De Deploy AWS

Use este checklist antes de qualquer deploy futuro. Esta etapa nao executa
deploy e nao cria recursos reais.

## Ambiente

- [ ] `ENVIRONMENT` definido como `dev`, `staging` ou `prod`.
- [ ] Recursos isolados por ambiente.
- [ ] Nomes de banco, bucket, filas, secrets e user pool identificam o ambiente.
- [ ] `.env` real armazenado fora do Git.
- [ ] `scripts/validate_env.py` executado para o ambiente alvo.
- [ ] `scripts/check_project_security.py` sem achados bloqueantes.

## Autenticacao

- [ ] `AUTH_PROVIDER=cognito` em `dev`, `staging` e `prod`.
- [ ] `DEV_JWT_ENABLED=false` fora de `local`.
- [ ] Cognito valida `issuer`, `audience/client_id`, `token_use`, `exp` e `RS256`.
- [ ] Claims de tenant e role revisadas.
- [ ] Frontend sem client secret.

## Banco

- [ ] RDS PostgreSQL privado em VPC.
- [ ] Extensoes `uuid-ossp` e `vector` planejadas.
- [ ] Backups automaticos habilitados.
- [ ] Snapshots e retencao definidos.
- [ ] Credenciais armazenadas em Secrets Manager ou mecanismo equivalente.
- [ ] Security group permite acesso apenas dos servicos autorizados.

## Documentos

- [ ] Bucket S3 privado.
- [ ] Bloqueio de acesso publico habilitado.
- [ ] Download/upload apenas via presigned URL.
- [ ] Criptografia em repouso habilitada.
- [ ] Lifecycle/retencao definido.
- [ ] Logs nao expõem caminhos internos, tokens ou conteudo integral.

## Filas e workers

- [ ] SQS por fluxo planejado.
- [ ] Jobs transportam apenas IDs e metadados minimos.
- [ ] Workers revalidam tenant/case/document no banco.
- [ ] Dead-letter queue planejada.
- [ ] Retry e idempotencia documentados.

## Seguranca e LGPD

- [ ] IAM com minimo privilegio.
- [ ] Secrets reais fora de README, docs, codigo e testes.
- [ ] Logs sem CPF/CNPJ completo, JWT, senha, chave ou contrato integral.
- [ ] `audit_log` habilitado para acoes sensiveis.
- [ ] Separacao por `organization_id` preservada.
- [ ] Revisao humana mantida para relatorios juridicos finais.

## Observabilidade

- [ ] CloudWatch Logs por servico.
- [ ] Retencao de logs definida.
- [ ] Alarmes basicos planejados.
- [ ] Health checks definidos para API e workers.

## Validacoes finais

- [ ] Testes backend executados.
- [ ] Build frontend executado.
- [ ] Migrations testadas em banco equivalente.
- [ ] Rollback documentado.
- [ ] Responsavel por aprovacao identificado.
