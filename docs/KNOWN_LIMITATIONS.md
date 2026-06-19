# Limitacoes Conhecidas - LegalTech AWS V2

Este documento lista limitacoes intencionais do estado atual do MVP tecnico.
Elas nao sao bugs necessariamente; sao fronteiras para tarefas futuras.

## Autenticacao e usuarios

- O login real com Cognito ainda nao foi implementado no frontend.
- Cognito no backend esta preparado e testado com JWKS mockado, mas ainda nao
  usa um User Pool real.
- JWT dev e permitido apenas localmente.
- A UI usa `localStorage` para sessao dev; isso nao e modelo de producao.
- A UI exige JWT dev colado para acessar telas internas; sessoes placeholder
  antigas sao descartadas.
- O login local valida o JWT no backend antes de salvar a sessao, mas a guarda
  visual do frontend nao substitui autorizacao real no backend.
- Nao ha refresh token real.
- Nao ha convite/cadastro real de usuarios.
- Nao ha administracao completa de usuarios/perfis.

## Multi-tenant e autorizacao

- O isolamento multi-tenant esta na camada de aplicacao, via `organization_id`
  em queries e services.
- Row Level Security no PostgreSQL ainda nao foi implementado.
- Claims reais de tenant/role em Cognito ainda precisam ser definidas e
  governadas em AWS.
- Administracao segura de `roles_permissions` ainda e comando interno/seed.

## Frontend

- Algumas areas ainda usam mock/fallback:
  - agentes ativos no dashboard;
  - relatorios;
  - revisoes humanas;
  - timeline completa;
  - upload real de arquivo.
- A aba Partes do detalhe do caso tem CRUD MVP local via API, mas o wizard de
  criacao de caso ainda nao persiste partes automaticamente apos criar o caso.
- O fallback mockado deve ficar desabilitado em staging/prod.
- A responsividade foi preparada, mas ainda precisa de validacao visual E2E em
  navegadores reais.
- `npm audit --audit-level=high` conclui sem vulnerabilidade alta bloqueante,
  mas reporta vulnerabilidade transitiva moderada em `next -> postcss`. O npm
  recomenda `audit fix --force`, que traz mudanca quebravel; por isso a
  correcao deve ser planejada em tarefa propria de upgrade de dependencias.

## Documentos e normalizacao

- Upload funcional pelo frontend existe apenas no MVP local/dev e grava
  arquivos ficticios em storage local ignorado pelo Git.
- Storage S3 esta preparado, mas nao conectado a bucket real.
- Presigned upload completo ainda nao esta implementado.
- Download real do arquivo local ainda nao foi exposto; a URL local/mock nao
  revela caminho absoluto nem storage key.
- Normalizacao Markdown suporta somente:
  - `.txt`
  - `.md`
  - `.docx` simples
  - `.pdf` com texto extraivel
- Upload local tambem aceita imagens `.png`, `.jpg` e `.jpeg` como anexos do
  caso, mas nao executa OCR nem extracao de texto nesta etapa.
- PDF escaneado ou sem texto fica como `requires_ocr`; OCR real esta fora do
  escopo atual.
- DOCX com elementos complexos, imagens, notas, cabecalhos/rodapes e tabelas
  sofisticadas pode perder estrutura.
- O Markdown convertido fica no storage local/mock ignorado pelo Git; nao deve
  ser commitado.
- Arquivos enviados no MVP local ficam em `apps/api/storage/local_uploads/` por
  padrao e nao devem conter dados reais.

## Processamento, IA e RAG

- Chunks e embeddings sao locais/mock.
- Embeddings sao fake/deterministicos.
- Nao ha OpenAI, Claude, Bedrock ou qualquer IA externa real.
- Nao ha RAG real.
- Nao ha analise juridica automatica real.
- Nao ha revisao humana implementada no fluxo final de relatorios.

## Filas e workers

- A fila local e JSONL em disco.
- SQS real ainda nao e usado.
- Nao ha DLQ real.
- Nao ha Lambda real.
- Nao ha locking distribuido para multiplos workers concorrentes.
- Retry e idempotencia sao basicos e suficientes apenas para desenvolvimento.

## Banco e migrations

- Migrations foram preparadas para PostgreSQL local.
- Rollback operacional real ainda precisa ser documentado por ambiente.
- Backups/snapshots reais ainda nao existem.
- RLS e politicas nativas de banco ficam para fase futura.
- A arquitetura do MVP usa PostgreSQL unico com pgvector no mesmo banco; nao ha
  banco vetorial separado.

## Seguranca, LGPD e operacao

- A sanitizacao de audit_log cobre padroes comuns, mas nao substitui revisao
  formal de seguranca/LGPD.
- Nao ha WAF, rate limiting, CloudWatch, CloudTrail ou alertas reais.
- Nao ha politica formal de retencao, anonimizacao ou exclusao de dados.
- Nao ha pentest.
- Nao ha secrets reais no repositorio; em AWS real, secrets devem ir para
  Secrets Manager/SSM ou mecanismo equivalente.

## AWS e deploy

- Nao ha Terraform/CDK completo.
- Nenhum recurso AWS real e criado.
- Nao ha Cognito User Pool real.
- Nao ha RDS privado real.
- Nao ha S3 privado real.
- Nao ha SQS real.
- Nao ha CloudFront/hosting real.
- Nao ha IAM minimo privilegio aplicado.
- Nao ha plano de custos/orcamento aplicado em AWS.

## Implicacao pratica

O projeto esta pronto para testes end-to-end locais controlados com dados
ficticios, mas ainda nao esta pronto para producao, dados reais ou deploy AWS
sem as etapas de infraestrutura, seguranca, LGPD e observabilidade.
