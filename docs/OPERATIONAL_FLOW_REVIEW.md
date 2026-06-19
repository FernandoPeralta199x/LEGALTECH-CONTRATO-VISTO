# Revisao do Fluxo Operacional - Tarefa 29.0

## Objetivo

Comparar o MVP local do LegalTech / Contrato Visto com o fluxo operacional
recomendado e registrar divergencias, evidencias e proximas tarefas sem criar
recursos AWS reais.

## Arquitetura De Banco Recomendada Para O MVP

Recomendacao: manter um unico PostgreSQL/RDS como banco operacional e vetorial
do MVP.

Status atual: alinhado.

Evidencias:

- `docker-compose.yml` usa a imagem `pgvector/pgvector:pg16`.
- `database/init/01_extensions.sql` cria `uuid-ossp` e `vector`.
- `apps/api/alembic/versions/0002_remaining_mvp_models.py` executa
  `CREATE EXTENSION IF NOT EXISTS vector`.
- `document_chunks` e `document_embeddings` ficam no mesmo schema do restante
  do dominio, com `organization_id`, `case_id` e indices.
- `apps/api/src/models/document_embedding.py` usa coluna `Vector(1536)`.

Decisao: nao criar banco vetorial separado no MVP. Isso reduz custo,
complexidade operacional e superficie de auditoria. Um banco vetorial separado
so deve ser reavaliado quando houver necessidade comprovada de escala,
latencia ou recursos ausentes no PostgreSQL com pgvector.

## Matriz Do Fluxo Operacional

| Etapa | Descricao | Status atual | Evidencia | Proxima tarefa recomendada |
| --- | --- | --- | --- | --- |
| 1 | Cliente cria caso no frontend autenticado | Parcial | `/cases`, `/cases/new`, `createCase`; wizard ainda tem trechos visuais | Integrar completamente `/cases/new` ao backend e Partes |
| 2 | Backend valida user, tenant e role pelo JWT e audita | Implementado | `security.py`, `tenant.py`, `rbac.py`, `audit_log` | Manter cobertura em novas rotas |
| 3 | Backend salva caso no PostgreSQL | Implementado | `cases` router/service/repository/model | Adicionar eventos de caso dedicados futuramente |
| 4 | Backend gera presigned URL para S3 privado | Parcial | Storage S3 adapter e download URL preparados | Implementar presigned upload real em tarefa AWS/dev |
| 5 | Cliente envia documentos ao S3 | Futuro AWS | Frontend ainda nao faz upload real; storage local existe | Criar fluxo upload frontend + presigned URL |
| 6 | Backend registra metadados de documento no PostgreSQL | Implementado local | `documents` router/service/model | Ligar confirmacao de upload real |
| 7 | Backend cria job na fila SQS de triagem | Mock/fallback local | Fila local JSONL e SQS adapter preparado | Criar fila de triagem real em ambiente dev sem dados reais |
| 8 | Agente de triagem valida produto/documentos/tipo | Parcial | Worker local de processamento documental | Separar worker de triagem por etapa |
| 9 | Coleta externa grava cache/evidencia no RDS | Documentado/parcial | `external_queries_cache` model/migration | Implementar adapters mockados antes de APIs reais |
| 10 | OCR/documental extrai texto e classifica documentos | Parcial | Normalizacao TXT/MD/DOCX/PDF textual; OCR fora do escopo | Implementar OCR mock/adapter e classificacao segura |
| 11 | Chunks e embeddings salvos no pgvector | Mock/local | `document_chunks`, `document_embeddings`, embeddings fake | Trocar embeddings fake por adapter real em fase futura |
| 12 | Agente contratual usa RAG | Ausente | Docs e modelos preparados, sem IA real | Criar RAG local controlado antes de IA externa |
| 13 | Compliance valida riscos/LGPD | Documentado | Docs LGPD e status de compliance no dominio | Implementar checklist de compliance sem IA real primeiro |
| 14 | Agente de relatorio gera minuta | Ausente/mock | `reports` model e mock frontend | Criar gerador de minuta controlado e auditavel |
| 15 | Analista humano revisa | Documentado/parcial | `human_reviews` model e docs | Implementar tela/rotas de revisao humana |
| 16 | Relatorio final salvo no S3 e liberado | Futuro AWS | `reports.storage_*`, S3 adapter | Implementar storage privado e presigned download final |
| 17 | audit_log, agent_executions e case_events registram etapas | Parcial | `audit_log` e `agent_executions` existem; `case_events` nao existe | Avaliar tabela `case_events` ou timeline derivada de audit/agents |

## Correcoes Funcionais Relacionadas

- A tela `/clients` passou a expor acao clara de edicao por card, usando
  `PATCH /api/v1/clients/{client_id}` ja existente.
- A aba Partes em `/cases/[id]` passou a usar endpoints reais de MVP local:
  `GET`, `POST` e `PATCH` em `/api/v1/cases/{case_id}/parties`.
- A tabela `case_parties` ja existia em migration; nao foi criada migration
  nova.

## Divergencias E Pendencias

- `/cases/new` ainda possui etapa visual de Partes e precisa ser integrada ao
  novo modulo de Partes apos criar o caso.
- `case_events` ainda nao existe; timeline continua mockada/derivada.
- S3, SQS, Lambda, Cognito real, APIs externas, OCR e IA/RAG reais continuam
  fora do escopo do MVP local.
- RLS no PostgreSQL segue pendente para hardening futuro.

## Conclusao

O MVP esta corretamente orientado para PostgreSQL unico com pgvector no mesmo
ambiente auditavel. O fluxo operacional recomendado esta parcialmente
implementado no backend local e documentado para evolucao controlada, sem
recursos AWS reais nesta tarefa.
