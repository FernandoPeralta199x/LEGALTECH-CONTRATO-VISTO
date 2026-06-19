# Fluxo e Arquitetura para Programação — LegalTech AWS V2

## 1. Objetivo

Este documento transforma a arquitetura LegalTech AWS V2 em um plano prático para começar a programar.

A prioridade é construir uma base sólida antes de implementar agentes, RAG, APIs externas e relatórios finais.

---

## 2. Estrutura recomendada do repositório

```text
legaltech-aws/
├── apps/
│   ├── frontend/
│   └── api/
├── workers/
│   ├── triagem/
│   ├── coleta_externa/
│   ├── documental/
│   ├── embeddings/
│   ├── analise_contratual/
│   ├── compliance/
│   └── relatorio/
├── infra/
├── database/
├── docs/
│   ├── ARQUITETURA_LEGALTECH_AWS_V2.md
│   ├── FLUXO_E_ARQUITETURA_PROGRAMACAO.md
│   ├── SECURITY_LGPD.md
│   ├── API_CONTRACT.md
│   ├── DATABASE_SCHEMA.md
│   └── AGENT_WORKFLOW.md
├── AGENTS.md
├── .env.example
├── .gitignore
└── README.md
```

---

## 3. Fluxo funcional do cliente

```text
1. Cliente acessa o sistema.
2. Cliente faz login.
3. Cliente cria novo caso.
4. Cliente escolhe o produto.
5. Cliente preenche dados das partes.
6. Cliente informa dados do objeto.
7. Cliente envia contrato/documentos.
8. Sistema salva metadados no PostgreSQL.
9. Sistema salva arquivos no S3 privado.
10. Sistema cria job na SQS.
11. Cliente acompanha status.
12. Analista interno revisa.
13. Cliente recebe relatório final aprovado.
```

---

## 4. Produtos iniciais

| Produto | Descrição | Resultado |
|---|---|---|
| Dados das partes | Consulta e análise das partes contratantes | Relatório cadastral/jurídico |
| Consulta do objeto | Verificação do objeto do contrato | Relatório de risco do objeto |
| Análise contratual | Leitura e análise do contrato | Relatório de riscos e cláusulas |
| Reunião com equipe | Encaminhamento para advogado/equipe | Agendamento ou revisão humana |

---

## 5. Ordem correta de programação

### Fase 0 — Preparação

- criar monorepo;
- criar `AGENTS.md`;
- criar `.env.example`;
- criar `.gitignore`;
- criar `README.md`;
- criar estrutura de pastas;
- inicializar Git.

### Fase 1 — Backend base

- FastAPI;
- endpoint `/health`;
- configuração central;
- estrutura modular;
- conexão futura com banco;
- README da API.

### Fase 2 — Banco e models

- SQLAlchemy;
- Alembic;
- models iniciais;
- migrations;
- tabelas com `organization_id`;
- timestamps;
- índices.

Models iniciais:

```text
organizations
users
roles_permissions
clients
case_parties
cases
documents
agent_executions
audit_log
```

### Fase 3 — Autenticação e tenant

- estrutura Cognito/JWT;
- middleware de autenticação;
- resolução de organização;
- RBAC básico;
- proteção de rotas.

### Fase 4 — Casos e documentos

- CRUD de clientes;
- CRUD de casos;
- partes do caso;
- presigned upload;
- confirmação de upload;
- metadados do documento;
- timeline do caso.

### Fase 5 — SQS e worker inicial

- adapter SQS;
- payload padrão;
- worker de triagem;
- tabela `agent_executions`;
- controle de retry;
- DLQ futura.

### Fase 6 — Frontend inicial

- login placeholder;
- dashboard;
- criar caso;
- upload;
- status do caso;
- listagem de relatórios.

### Fase 7 — APIs externas

- adapters;
- mocks;
- cache;
- normalização de respostas;
- armazenamento de evidências.

### Fase 8 — RAG e relatórios

- extração de texto;
- chunks;
- embeddings;
- pgvector;
- análise contratual;
- compliance;
- minuta;
- revisão humana;
- relatório final.

---

## 6. Primeiros prompts para o Codex

### 6.1 Preparar estrutura

```text
Leia o AGENTS.md e prepare a estrutura inicial do projeto LegalTech AWS V2.

Crie apenas pastas e arquivos base:
apps/frontend, apps/api, workers, infra, database, docs, README.md, .env.example e .gitignore.

Não instale dependências.
Não implemente APIs externas.
Não coloque chaves reais.
```

### 6.2 Implementar backend FastAPI

```text
Implemente a base inicial do backend FastAPI em legaltech-aws/apps/api.

Criar:
- src/main.py
- src/core/config.py
- src/core/security.py
- src/core/tenant.py
- src/db/session.py
- src/modules/health/router.py
- requirements.txt
- README.md

Criar endpoint GET /health.
Não implementar banco completo ainda.
```

### 6.3 Implementar banco inicial

```text
Implemente SQLAlchemy + Alembic e os models iniciais:

organizations, users, clients, cases, documents, agent_executions e audit_log.

Toda tabela sensível deve ter organization_id.
Crie migrations.
Não usar dados reais.
```

---

## 7. Critério de pronto da base

A base inicial estará pronta quando:

- o repositório estiver organizado;
- Git estiver inicializado;
- backend rodar com `/health`;
- frontend tiver estrutura inicial;
- `.env.example` existir;
- não houver chaves reais;
- documentação estiver em `docs/`;
- Codex conseguir seguir `AGENTS.md`.

---

## 8. Conclusão

Não comece por IA, RAG ou APIs externas.

A ordem correta é:

```text
Estrutura → Backend → Banco → Auth/Tenant → Casos → Documentos → SQS → Workers → Frontend → APIs externas → RAG → Relatórios
```
