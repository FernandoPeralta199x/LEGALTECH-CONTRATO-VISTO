# Infraestrutura

Esta pasta guarda a preparacao de infraestrutura do LegalTech AWS V2.

Nesta etapa nao ha deploy real, Terraform/CDK completo, recursos AWS reais ou
credenciais. O objetivo e documentar ambientes, variaveis, seguranca e o plano
para uma implantacao futura.

## Estrutura

```text
infra/
+-- README.md
+-- aws/
    +-- README.md
    +-- env.example
    +-- checklist-deploy.md
```

## Ambientes

- `local`: desenvolvimento com Docker/PostgreSQL, JWT dev e storage/fila local.
- `dev`: ambiente AWS de desenvolvimento, com Cognito e recursos isolados.
- `staging`: validacao antes de producao, com configuracao proxima de prod.
- `prod`: producao, com controles de seguranca, backup, observabilidade e IAM
  minimo privilegio.

## Regras

- Nao armazenar secrets reais nesta pasta.
- Nao versionar `.env` real.
- Nao usar `AUTH_PROVIDER=dev_jwt` fora de `local`.
- Nao publicar buckets S3.
- Nao expor documentos sem presigned URL.
- Nao aceitar `organization_id` vindo do frontend como fonte de verdade.

Leia tambem:

- `docs/ENVIRONMENT_VARIABLES.md`
- `docs/AWS_DEPLOYMENT_PLAN.md`
- `docs/SECURITY_CHECKLIST_AWS.md`
- `infra/aws/checklist-deploy.md`
