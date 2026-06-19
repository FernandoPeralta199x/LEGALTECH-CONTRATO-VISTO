# AWS Futura

Esta pasta prepara a configuracao para uma implantacao futura em AWS.
Nenhum comando aqui deve criar recursos automaticamente nesta etapa.

## Recursos planejados

- Cognito User Pool para autenticacao.
- RDS PostgreSQL com extensoes `uuid-ossp` e `pgvector`.
- S3 privado para documentos.
- SQS para filas de processamento.
- Lambda ou workers gerenciados para processamento assincrono.
- CloudFront/S3 ou hosting gerenciado para o frontend.
- Secrets Manager para secrets de APIs externas.
- CloudWatch Logs para observabilidade.
- IAM roles com minimo privilegio.
- VPC, subnets e security groups para isolamento de rede.
- Backups, snapshots e retencao por ambiente.
- KMS para criptografia gerenciada quando aplicavel.

## Como usar os arquivos

1. Copie `env.example` para um arquivo local fora do Git, se precisar simular
   configuracao de ambiente.
2. Preencha valores reais apenas em ambiente seguro, nunca no repositorio.
3. Rode validacoes locais antes de qualquer deploy futuro:

```powershell
python scripts/validate_env.py --env-file infra/aws/env.example --environment staging --target aws
python scripts/check_project_security.py .
```

## Separacao por ambiente

Cada ambiente deve ter nomes e recursos isolados:

- `legaltech-dev-*`
- `legaltech-staging-*`
- `legaltech-prod-*`

Nao reutilize bancos, buckets, filas, user pools ou secrets entre ambientes.
