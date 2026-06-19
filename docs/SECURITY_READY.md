# Security Ready - Tarefa 29

## Status

Hardening local executado para o MVP LegalTech AWS / Contrato Visto.
O objetivo foi reduzir riscos antes de um deploy controlado futuro, sem criar
recursos AWS reais e sem declarar prontidao de producao.

Conclusao: Projeto reforcado para MVP local controlado, ainda nao production-ready.

## O Que Foi Verificado

- Estado Git antes da tarefa.
- Checklists em `docs/security/`.
- Frontend Next.js, API FastAPI, scripts, docs, exemplos de ambiente e testes.
- Auth dev JWT, tenant, RBAC, CORS, headers, logs, upload/storage local,
  fallback/mock, secrets, `.gitignore`, dependencias e artefatos locais.
- Pastas locais ignoradas como `.local/`, `.venv/`, `node_modules/`,
  `.next/`, storage local e filas locais.

## O Que Foi Corrigido

- Adicionado `GET /api/v1/me` para validar o JWT no backend e retornar somente
  dados minimos da sessao autenticada.
- O login local agora valida o JWT dev na API antes de salvar a sessao no
  navegador.
- Removida a geracao de JWT placeholder no frontend.
- `validateDevJwtForm` passou a exigir claims dev minimas antes da validacao
  remota.
- Adicionados headers HTTP defensivos no backend:
  `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options` e
  `Permissions-Policy`.
- Rotas `/api/v1/*` recebem `Cache-Control: no-store`.
- CORS local passou a incluir explicitamente `http://192.168.0.102:3000`.
- Wildcard `*` em `CORS_ALLOWED_ORIGINS` passou a ser rejeitado.
- `validate_env.py` passou a bloquear wildcard CORS e origens locais fora da
  lista permitida.
- Exemplos de ambiente e docs receberam aviso explicito sobre variaveis
  `NEXT_PUBLIC_*`.
- A tela `/documents` passou a enviar arquivos reais para o backend local via
  `multipart/form-data`, preservando `Authorization: Bearer` no `apiClient`.
- O upload local valida caso, tamanho, extensao e MIME basico, grava em
  `apps/api/storage/local_uploads/` e nao aceita `organization_id` vindo do
  frontend como fonte de autoridade.

## Limitacoes Do MVP Local

- JWT dev existe apenas para `APP_ENV=local`.
- A sessao dev ainda usa `localStorage`; isso nao e aceitavel como modelo final
  de producao.
- Cognito real, S3 real, SQS real, Lambda, OCR, IA/RAG e APIs externas reais
  seguem fora do escopo.
- Upload real no frontend existe apenas para MVP local/dev; presigned upload
  completo para S3 ainda nao esta pronto.
- RLS no PostgreSQL, WAF, rate limiting, observabilidade e politicas formais de
  retencao/LGPD permanecem pendentes.

## Nao Pronto Para Producao

- Nao ha infraestrutura AWS real provisionada.
- Nao ha Cognito User Pool real nem claims governadas em AWS.
- Nao ha IAM minimo privilegio, KMS, CloudWatch, CloudTrail, Budgets ou WAF.
- Nao ha pentest, revisao LGPD formal nem processo completo de resposta a
  incidentes.
- O fallback/mock do frontend deve estar desabilitado em staging/prod.

## Checklist Antes De Deploy Real

- [ ] Rotacionar qualquer segredo que tenha sido usado fora de cofre seguro.
- [ ] Garantir `.env` real fora do Git e fora de artefatos de build.
- [ ] Usar `AUTH_PROVIDER=cognito` e `DEV_JWT_ENABLED=false`.
- [ ] Definir dominio real e CORS restrito por ambiente.
- [ ] Desabilitar `NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK`.
- [ ] Validar headers, TLS, cookies/sessao e politica de cache no ambiente alvo.
- [ ] Rodar testes, lint, typecheck, build e auditoria de dependencias.
- [ ] Executar revisao humana de fluxos juridicos e LGPD.

## Checklist Antes De AWS

- [ ] Criar IaC revisado para Cognito, RDS, S3 privado, SQS, Lambda e rede.
- [ ] Usar Secrets Manager ou SSM para secrets reais.
- [ ] Aplicar IAM minimo privilegio.
- [ ] Bloquear acesso publico ao S3 e usar presigned URLs temporarias.
- [ ] Configurar CloudWatch, CloudTrail, AWS Budgets e alertas.
- [ ] Definir backups, snapshots, retencao, anonimizacao e rollback.

## Riscos Conhecidos

- Alto: configuracao incorreta de Cognito/claims pode quebrar isolamento por
  tenant.
- Alto: fallback/mock habilitado fora de local pode esconder falhas reais.
- Medio: `localStorage` para JWT dev e aceitavel apenas no MVP local.
- Medio: ausencia de RLS deixa isolamento dependente da aplicacao.
- Medio: `npm audit --audit-level=high` reportou vulnerabilidade moderada
  transitiva em `next -> postcss`; o `audit fix --force` sugerido e quebravel
  e deve ser tratado em tarefa propria de upgrade.
- Baixo: `.local/` contem perfis/logs de browser gerados localmente, ignorados
  pelo Git, mas nao deve ser compartilhado.

## Orientacoes De Secrets

- Nunca commitar `.env`, tokens, senhas, chaves privadas ou chaves AWS.
- Exemplos devem usar placeholders ficticios.
- Se um segredo real for encontrado, mascarar, remover, rotacionar fora do
  codigo e avaliar limpeza de historico Git.

## Orientacoes De CORS

- MVP local permite apenas:
  - `http://localhost:3000`
  - `http://127.0.0.1:3000`
  - `http://192.168.0.102:3000`
- O IP `192.168.0.102` e apenas para teste mobile local.
- CORS nao substitui autenticacao, tenant nem permissao.

## Orientacoes De JWT Dev

- JWT dev e permitido somente em `APP_ENV=local`.
- O frontend nao gera JWT.
- O frontend valida o JWT no backend antes de salvar sessao local.
- JWT completo nao deve aparecer em UI, console, logs ou docs.
- `organization_id` deve vir do token/backend, nunca do payload do frontend.

## Orientacoes De Logs

- Nao logar JWT completo, segredo, senha, API key, CPF/CNPJ, contrato inteiro
  ou payload sensivel.
- Logs locais devem ficar em pastas ignoradas.
- Erros tecnicos devem ficar em logs controlados; usuario deve receber mensagem
  amigavel.

## Documentos Sensiveis

- Nao usar dados reais no MVP local.
- Storage local fica em `apps/api/storage/local_uploads/`, pasta ignorada pelo
  Git. Limpe esses arquivos quando necessario e nao compartilhe artefatos
  locais.
- S3 futuro deve ser privado e acessado por presigned URL temporaria.
- Relatorios juridicos finais continuam exigindo revisao humana.

## Proximos Passos Recomendados

1. Planejar upgrade seguro de dependencias se auditoria apontar vulnerabilidade.
2. Implementar Cognito real em ambiente `dev` sem dados reais.
3. Criar IaC minimo com IAM restrito e observabilidade.
4. Adicionar validacao visual/manual mobile e desktop apos cada alteracao de UI.
5. Definir politica LGPD de retencao, anonimizacao e exclusao.
