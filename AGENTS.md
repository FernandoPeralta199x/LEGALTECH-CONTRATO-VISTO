# AGENTS.md — LegalTech AWS V2

## Papel do Codex

Atue como engenheiro de software sênior full stack, arquiteto de software e revisor técnico.

Este projeto é uma plataforma LegalTech/SaaS para análise jurídica, due diligence, consulta de partes/objetos, análise contratual e geração de relatórios.

## Stack obrigatória

- Frontend: Next.js + TypeScript
- Backend: FastAPI + Python
- ORM: SQLAlchemy
- Migrations: Alembic
- Banco: PostgreSQL
- Vetorial/RAG: pgvector no PostgreSQL
- Arquivos: Amazon S3 privado
- Filas: AWS SQS
- Workers: AWS Lambda
- Auth: Cognito/JWT/RBAC/Tenant
- Deploy futuro: AWS
- Observabilidade: CloudWatch, CloudTrail e AWS Budgets

## Estrutura esperada

legaltech-aws/
├── apps/
│   ├── frontend/
│   └── api/
├── workers/
├── infra/
├── database/
├── docs/
├── README.md
└── .env.example

## Regras obrigatórias

1. Nunca colocar chaves reais no código.
2. Nunca expor tokens no frontend.
3. Nunca confiar em organization_id enviado pelo frontend.
4. O organization_id deve vir do JWT ou vínculo interno do usuário.
5. Toda tabela sensível deve ter organization_id.
6. Toda rota sensível deve validar permissão.
7. Toda ação sensível deve gerar audit_log.
8. Upload deve usar presigned URL.
9. Arquivos devem ficar em S3 privado.
10. Relatório jurídico final exige revisão humana.
11. Separar rotas, services, schemas, repositories e models.
12. Criar código legível, modular e testável.
13. Antes de alterar muitos arquivos, apresentar plano curto.
14. Após alterar código, informar arquivos modificados e como testar.
15. Não implementar APIs externas reais sem contrato/API key. Criar adapters e mocks.

## Ordem de implementação

1. Monorepo
2. Backend FastAPI
3. Banco PostgreSQL + Alembic
4. Models iniciais
5. Auth/JWT preparado
6. Tenant middleware
7. CRUD de clients e cases
8. Upload S3 com presigned URL
9. SQS adapter
10. Worker inicial de triagem
11. Frontend inicial
12. Audit log
13. Testes básicos
14. README

## Primeira entrega esperada

Criar a base programável do MVP:

- apps/api com FastAPI
- apps/frontend com Next.js + TypeScript
- database com migrations iniciais
- workers/triagem
- adapters S3 e SQS
- .env.example
- README com comandos locais

## Critério de pronto

Uma tarefa só está pronta quando:

- o código compila;
- os imports não estão quebrados;
- existe README ou instrução de execução;
- arquivos sensíveis não foram expostos;
- a estrutura segue a arquitetura do projeto;
- o Codex informa claramente o que foi alterado.

# AGENTS.md

## Regras Do Projeto

- Nunca confiar em `organization_id` vindo do frontend.
- Toda tabela sensivel deve ter `organization_id`.
- Toda acao sensivel deve gerar `audit_log`.
- Upload deve usar presigned URL.
- Arquivos devem ficar em S3 privado.
- Frontend nunca recebe chave de API externa.
- Backend deve validar autenticacao, tenant e permissao.
- Relatorio juridico final exige revisao humana.
- Separar rotas, services, schemas, repositories e models.

## Diretrizes De Arquitetura

- O frontend deve tratar `organization_id`, permissoes e identidade como informacoes derivadas da sessao autenticada, nunca como fonte de autoridade.
- O backend deve centralizar regras de autenticacao, tenant, RBAC e auditoria em camadas reutilizaveis.
- Integracoes externas devem ser encapsuladas em services/adapters, com interfaces testaveis e sem exposicao de credenciais ao cliente.
- Operacoes assincronas devem ser desenhadas para filas e workers desde o inicio, mesmo quando ainda nao implementadas.
- Documentos e resultados juridicos devem manter rastreabilidade, logs de auditoria e etapa obrigatoria de revisao humana.
