# Contrato de API — LegalTech AWS V2

## 1. Objetivo

Este documento define as rotas iniciais da API do MVP LegalTech AWS V2.

Base URL sugerida:

```text
/api/v1
```

Formato padrão:

```text
JSON
```

Autenticação futura:

```text
Authorization: Bearer <jwt>
```

---

## 2. Padrão de resposta

### 2.1 Sucesso

```json
{
  "success": true,
  "data": {},
  "message": "Operação realizada com sucesso."
}
```

### 2.2 Erro

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dados inválidos.",
    "details": {}
  }
}
```

---

## 3. Códigos de erro recomendados

| Código | Uso |
|---|---|
| UNAUTHORIZED | Usuário não autenticado |
| FORBIDDEN | Usuário sem permissão |
| NOT_FOUND | Recurso não encontrado |
| VALIDATION_ERROR | Erro de validação |
| TENANT_REQUIRED | Organização não resolvida |
| CONFLICT | Conflito de estado |
| EXTERNAL_API_ERROR | Erro em API externa |
| JOB_ALREADY_RUNNING | Job já em execução |
| INTERNAL_ERROR | Erro interno |

---

## 4. Health

### GET `/health`

Verifica se a API está no ar.

Resposta:

```json
{
  "success": true,
  "data": {
    "status": "ok",
    "service": "legaltech-api"
  }
}
```

---

## 5. Usuário autenticado

### GET `/me`

Retorna dados do usuário autenticado.

Resposta:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "usuario@empresa.com",
    "name": "Nome do Usuário",
    "organization_id": "uuid",
    "role": "admin"
  }
}
```

---

## 6. Organizações

### GET `/organizations/current`

Retorna a organização atual do usuário.

### PATCH `/organizations/current`

Atualiza dados básicos da organização.

Body:

```json
{
  "name": "Empresa Exemplo",
  "document": "00000000000100"
}
```

---

## 7. Usuários

### GET `/users`

Lista usuários da organização.

### POST `/users/invite`

Convida usuário.

Body:

```json
{
  "email": "novo@empresa.com",
  "name": "Novo Usuário",
  "role": "analyst"
}
```

### PATCH `/users/{user_id}/role`

Altera perfil.

Body:

```json
{
  "role": "admin"
}
```

### PATCH `/users/{user_id}/deactivate`

Desativa usuário.

---

## 8. Clientes

### GET `/clients`

Lista clientes.

Query params:

```text
page
page_size
search
```

### POST `/clients`

Cria cliente.

Body:

```json
{
  "name": "Cliente Exemplo",
  "document": "00000000000",
  "email": "cliente@email.com",
  "phone": "+5548999999999",
  "metadata": {}
}
```

### GET `/clients/{client_id}`

Detalha cliente.

### PATCH `/clients/{client_id}`

Atualiza cliente.

---

## 9. Casos

### GET `/cases`

Lista casos.

Query params:

```text
status
case_type
client_id
page
page_size
```

### POST `/cases`

Cria caso.

Body:

```json
{
  "client_id": "uuid",
  "case_type": "contract_analysis",
  "priority": "normal",
  "metadata": {
    "product": "analise_contratual"
  }
}
```

### GET `/cases/{case_id}`

Detalha caso.

### PATCH `/cases/{case_id}`

Atualiza caso.

### POST `/cases/{case_id}/submit`

Envia caso para processamento.

### GET `/cases/{case_id}/timeline`

Retorna timeline do caso.

### GET `/cases/{case_id}/status`

Retorna status atual.

---

## 10. Partes do caso

### GET `/cases/{case_id}/parties`

Lista partes.

### POST `/cases/{case_id}/parties`

Adiciona parte.

Body:

```json
{
  "party_type": "cliente",
  "name": "Nome da Parte",
  "document": "00000000000",
  "email": "parte@example.test",
  "phone": "+5500000000000",
  "notes": "Observacao ficticia",
  "metadata": {}
}
```

### PATCH `/cases/{case_id}/parties/{party_id}`

Atualiza parte.

### DELETE `/cases/{case_id}/parties/{party_id}`

Futuro. Remocao logica ainda nao foi exposta no MVP local.

---

## 11. Documentos

### POST `/cases/{case_id}/documents/presigned-upload`

Solicita URL temporária para upload.

Body:

```json
{
  "filename": "contrato.pdf",
  "content_type": "application/pdf",
  "size_bytes": 1024000
}
```

Resposta:

```json
{
  "success": true,
  "data": {
    "document_id": "uuid",
    "upload_url": "https://s3-presigned-url",
    "storage_key": "organizations/org/cases/case/documents/file.pdf"
  }
}
```

### POST `/cases/{case_id}/documents/confirm-upload`

Confirma upload.

Body:

```json
{
  "document_id": "uuid",
  "hash": "sha256"
}
```

### GET `/cases/{case_id}/documents`

Lista documentos do caso.

### GET `/documents/{document_id}/download-url`

Gera URL temporária para download.

### DELETE `/documents/{document_id}`

Remove documento de forma lógica.

---

## 12. Agentes

### POST `/cases/{case_id}/agents/start`

Inicia processamento.

Body:

```json
{
  "start_from": "triagem"
}
```

### POST `/cases/{case_id}/agents/retry`

Reprocessa etapa.

Body:

```json
{
  "agent_type": "triagem",
  "job_id": "uuid"
}
```

### GET `/cases/{case_id}/agents/executions`

Lista execuções.

### GET `/agents/jobs/{job_id}`

Consulta job.

---

## 13. Relatórios

### GET `/cases/{case_id}/reports`

Lista relatórios do caso.

### GET `/reports/{report_id}`

Detalha relatório.

### GET `/reports/{report_id}/download-url`

Gera URL temporária para baixar relatório aprovado.

---

## 14. Revisão humana

### GET `/reviews/pending`

Lista revisões pendentes.

### POST `/reviews/{review_id}/approve`

Aprova minuta.

Body:

```json
{
  "notes": "Aprovado para envio."
}
```

### POST `/reviews/{review_id}/reject`

Rejeita minuta.

Body:

```json
{
  "reason": "Necessário ajustar análise da cláusula de rescisão."
}
```

### POST `/reviews/{review_id}/request-adjustment`

Solicita ajuste.

Body:

```json
{
  "instructions": "Revisar riscos relacionados ao objeto do contrato."
}
```

---

## 15. Auditoria

### GET `/audit`

Lista eventos de auditoria.

Permissão:

```text
admin ou owner
```

Query params:

```text
entity_type
entity_id
user_id
action
date_from
date_to
```

---

## 16. Conclusão

Este contrato deve evoluir junto com o backend.

Regra principal:

```text
Toda rota sensível deve validar autenticação, tenant, permissão e registrar auditoria quando necessário.
```
