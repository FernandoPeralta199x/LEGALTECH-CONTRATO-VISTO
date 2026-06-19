# Schema de Banco de Dados — LegalTech AWS V2

## 1. Objetivo

Este documento define o schema inicial do banco PostgreSQL para o MVP LegalTech AWS V2.

Banco recomendado:

```text
Amazon RDS PostgreSQL
```

Extensão futura:

```text
pgvector
```

---

## 2. Regras obrigatórias

1. Toda tabela sensível deve ter `organization_id`.
2. Toda tabela importante deve ter `created_at`.
3. Toda tabela mutável deve ter `updated_at`.
4. Preferir exclusão lógica com `deleted_at`.
5. Nunca confiar em `organization_id` vindo do frontend.
6. Criar índices por `organization_id` e campos de busca frequente.
7. Registrar ações sensíveis em `audit_log`.

---

## 3. Extensões

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## 4. Tabelas obrigatórias do MVP

```text
organizations
users
roles_permissions
clients
case_parties
cases
documents
external_queries_cache
agent_executions
document_chunks
document_embeddings
human_reviews
reports
audit_log
```

---

## 5. organizations

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    document VARCHAR(32),
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP NULL
);
```

---

## 6. users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'client',
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    external_auth_id VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP NULL
);

CREATE UNIQUE INDEX idx_users_org_email ON users (organization_id, email);
CREATE INDEX idx_users_org_role ON users (organization_id, role);
```

---

## 7. roles_permissions

```sql
CREATE TABLE roles_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    role VARCHAR(50) NOT NULL,
    permission VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_roles_permissions_unique
ON roles_permissions (organization_id, role, permission);
```

---

## 8. clients

```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    document VARCHAR(32),
    email VARCHAR(255),
    phone VARCHAR(32),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_clients_org_name ON clients (organization_id, name);
CREATE INDEX idx_clients_org_document ON clients (organization_id, document);
```

---

## 9. cases

```sql
CREATE TABLE cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    client_id UUID NOT NULL REFERENCES clients(id),
    case_type VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
    created_by UUID NOT NULL REFERENCES users(id),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    submitted_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_cases_org_status ON cases (organization_id, status);
CREATE INDEX idx_cases_org_client ON cases (organization_id, client_id);
CREATE INDEX idx_cases_org_type ON cases (organization_id, case_type);
```

---

## 10. case_parties

```sql
CREATE TABLE case_parties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    case_id UUID NOT NULL REFERENCES cases(id),
    party_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    document VARCHAR(32),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_case_parties_org_case ON case_parties (organization_id, case_id);
CREATE INDEX idx_case_parties_org_document ON case_parties (organization_id, document);
```

---

## 11. documents

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    case_id UUID NOT NULL REFERENCES cases(id),
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(120) NOT NULL,
    size_bytes BIGINT NOT NULL,
    storage_bucket VARCHAR(255) NOT NULL,
    storage_key TEXT NOT NULL,
    file_hash VARCHAR(128),
    status VARCHAR(30) NOT NULL DEFAULT 'pending_upload',
    conversion_status VARCHAR(30) NOT NULL DEFAULT 'pending',
    normalized_markdown_storage_key TEXT,
    normalized_markdown_sha256 VARCHAR(128),
    normalized_markdown_size_bytes BIGINT,
    conversion_error_summary TEXT,
    converted_at TIMESTAMP NULL,
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMP NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_documents_org_case ON documents (organization_id, case_id);
CREATE INDEX idx_documents_org_status ON documents (organization_id, status);
CREATE INDEX idx_documents_org_conversion_status ON documents (organization_id, conversion_status);
```

---

## 12. external_queries_cache

```sql
CREATE TABLE external_queries_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    case_id UUID REFERENCES cases(id),
    provider VARCHAR(80) NOT NULL,
    query_hash VARCHAR(128) NOT NULL,
    request_payload JSONB NOT NULL,
    response_payload JSONB,
    normalized_payload JSONB,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    requested_by UUID REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_external_queries_cache_unique
ON external_queries_cache (organization_id, provider, query_hash);
```

---

## 13. agent_executions

```sql
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    case_id UUID NOT NULL REFERENCES cases(id),
    document_id UUID REFERENCES documents(id),
    job_id UUID NOT NULL,
    agent_type VARCHAR(80) NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'queued',
    attempt INTEGER NOT NULL DEFAULT 1,
    input_payload JSONB DEFAULT '{}'::jsonb,
    output_payload JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_agent_executions_job_id ON agent_executions (job_id);
CREATE INDEX idx_agent_executions_org_case ON agent_executions (organization_id, case_id);
CREATE INDEX idx_agent_executions_org_status ON agent_executions (organization_id, status);
```

---

## 14. document_chunks

```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    document_id UUID NOT NULL REFERENCES documents(id),
    case_id UUID NOT NULL REFERENCES cases(id),
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    page_number INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_document_chunks_org_case ON document_chunks (organization_id, case_id);
CREATE INDEX idx_document_chunks_document ON document_chunks (document_id);
```

---

## 15. document_embeddings

```sql
CREATE TABLE document_embeddings (
    id BIGSERIAL PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    document_id UUID NOT NULL REFERENCES documents(id),
    case_id UUID NOT NULL REFERENCES cases(id),
    chunk_id UUID REFERENCES document_chunks(id),
    segment_text TEXT NOT NULL,
    embedding vector(1536),
    segment_type VARCHAR(50),
    page_number INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_document_embeddings_org_case
ON document_embeddings (organization_id, case_id);

CREATE INDEX idx_document_embeddings_vector
ON document_embeddings
USING ivfflat (embedding vector_cosine_ops);
```

Observação:

A dimensão `1536` deve ser ajustada caso o modelo de embeddings utilizado tenha outra dimensão.

---

## 16. human_reviews

```sql
CREATE TABLE human_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    case_id UUID NOT NULL REFERENCES cases(id),
    report_id UUID,
    status VARCHAR(40) NOT NULL DEFAULT 'pending',
    assigned_to UUID REFERENCES users(id),
    reviewed_by UUID REFERENCES users(id),
    review_notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP NULL
);

CREATE INDEX idx_human_reviews_org_status ON human_reviews (organization_id, status);
```

---

## 17. reports

```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    case_id UUID NOT NULL REFERENCES cases(id),
    status VARCHAR(40) NOT NULL DEFAULT 'draft',
    version INTEGER NOT NULL DEFAULT 1,
    title VARCHAR(255),
    content_json JSONB DEFAULT '{}'::jsonb,
    storage_bucket VARCHAR(255),
    storage_key TEXT,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reports_org_case ON reports (organization_id, case_id);
CREATE INDEX idx_reports_org_status ON reports (organization_id, status);
```

---

## 18. audit_log

```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(80) NOT NULL,
    entity_id UUID,
    ip_address VARCHAR(64),
    user_agent TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_log_org_created ON audit_log (organization_id, created_at);
CREATE INDEX idx_audit_log_entity ON audit_log (entity_type, entity_id);
CREATE INDEX idx_audit_log_user ON audit_log (user_id);
```

---

## 19. Status recomendados

### cases.status

```text
draft
submitted
triage_pending
triage_failed
external_collection_pending
document_processing_pending
contract_analysis_pending
compliance_pending
report_draft_pending
human_review_pending
approved
delivered
failed
cancelled
```

### agent_executions.status

```text
queued
running
completed
failed
retrying
dead_letter
skipped
requires_human_review
```

### documents.status

```text
pending_upload
uploaded
processing
processed
failed
deleted
```

### documents.conversion_status

```text
pending
converting
converted
failed
requires_ocr
```

---

## 20. Conclusão

Este schema é a base mínima para o MVP.

A evolução natural será:

```text
schema inicial
→ RLS opcional
→ pgvector
→ auditoria avançada
→ retenção de dados
→ relatórios versionados
→ billing
```
