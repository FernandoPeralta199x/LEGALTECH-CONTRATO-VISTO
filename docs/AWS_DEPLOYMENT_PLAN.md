# Plano De Deploy AWS

Este plano descreve a implantacao futura do LegalTech AWS V2. Ele nao cria
recursos e nao substitui revisao de arquitetura, seguranca e custos.

## Objetivo

Implantar a plataforma com isolamento por ambiente, dados sensiveis protegidos,
autenticacao Cognito, banco PostgreSQL, armazenamento privado de documentos e
filas/worker para processamento assincrono.

## Recursos Planejados

### Cognito User Pool

- User Pool por ambiente.
- App client sem client secret no frontend.
- Claims confiaveis para `organization_id` e papel/grupo.
- Validacao de `issuer`, `audience/client_id`, `token_use`, `exp` e `RS256`.

### RDS PostgreSQL

- Instancia/cluster privado em VPC.
- Extensoes `uuid-ossp` e `pgvector`.
- Backups automaticos.
- Snapshots antes de migrations sensiveis.
- Security groups restritivos.

### S3 Privado

- Bucket por ambiente para documentos.
- Block Public Access habilitado.
- Criptografia em repouso.
- Upload/download via presigned URL.
- Lifecycle e retencao conforme politica futura.

### SQS

- Filas por fluxo:
  - document processing
  - triage
  - external collection
  - contract analysis
  - compliance
  - reports
- Jobs com apenas IDs e metadados minimos.
- Dead-letter queue futura.

### Workers Ou Lambda

- Processamento assincrono com revalidacao de tenant/case/document.
- Idempotencia por `job_id`.
- `agent_executions` e `audit_log` atualizados por estado.
- Sem conteudo sensivel completo no payload da fila.

### Frontend Hosting

- Hosting estatico/gerenciado por ambiente.
- `NEXT_PUBLIC_*` sem secrets.
- Cognito Hosted UI ou fluxo equivalente em tarefa futura.

### Secrets Manager

- Guardar secrets reais de APIs externas somente em Secrets Manager.
- Aplicacao referencia apenas nomes logicos, por exemplo
  `SECRETS_EXTERNAL_APIS_NAME`.

### CloudWatch

- Logs estruturados e sanitizados.
- Retencao por ambiente.
- Alarmes para erros, latencia, filas e workers.

### IAM

- Roles por servico.
- Permissoes minimas para Cognito, RDS, S3, SQS, Secrets Manager e logs.
- Sem usuario IAM com access key hardcoded em aplicacao.

### Rede

- VPC com subnets privadas para banco e workers.
- Security groups restritivos.
- Acesso administrativo controlado.

## Ordem Recomendada

1. Confirmar variaveis e checklist de seguranca.
2. Criar recursos de rede e IAM com minimo privilegio.
3. Provisionar RDS privado e aplicar migrations em ambiente vazio.
4. Provisionar Cognito e validar tokens mockados/reais de ambiente.
5. Criar bucket S3 privado e testar presigned URL.
6. Criar filas SQS e worker sem dados sensiveis no payload.
7. Configurar API com `AUTH_PROVIDER=cognito`.
8. Publicar frontend com `NEXT_PUBLIC_API_BASE_URL` do ambiente.
9. Habilitar observabilidade, alarmes e backups.
10. Executar testes, smoke tests e revisao de LGPD antes de abrir uso real.

## Validacoes Antes Do Primeiro Deploy

- Backend: testes, compileall e pip check.
- Frontend: test, typecheck, lint e build.
- Migrations em banco equivalente.
- `scripts/validate_env.py` para ambiente alvo.
- `scripts/check_project_security.py`.
- Revisao manual de `.env` real fora do Git.
- Revisao de IAM.
- Revisao de logs e auditabilidade.

## Fora Do Escopo Desta Etapa

- Terraform/CDK completo.
- Criacao real de Cognito, RDS, S3, SQS, Lambda ou CloudFront.
- Deploy real.
- Credenciais AWS reais.
- OCR, IA, RAG ou APIs externas reais.
- Login Cognito real no frontend.

## Rollback Futuro

Antes de deploy real, documentar:

- versao anterior da API e frontend;
- estrategia de rollback de migrations;
- snapshot do banco;
- reversao de variaveis;
- parada segura de workers;
- responsavel por aprovacao.
