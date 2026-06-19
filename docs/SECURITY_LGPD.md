# Segurança e LGPD — LegalTech AWS V2

## 1. Objetivo

Este documento define as regras mínimas de segurança, privacidade, auditoria e LGPD para o desenvolvimento do MVP LegalTech AWS V2.

Como o sistema lida com contratos, dados pessoais, documentos, partes contratantes e análises jurídicas, segurança deve ser implementada desde o início.

---

## 2. Princípios obrigatórios

1. Minimização de dados.
2. Controle de acesso por usuário, perfil e organização.
3. Isolamento por tenant.
4. Auditoria de ações sensíveis.
5. Criptografia em trânsito e em repouso.
6. Segredos fora do código.
7. Logs sem exposição indevida de dados pessoais.
8. Revisão humana em relatório jurídico final.
9. Rastreabilidade de consultas externas.
10. Proteção contra acesso indevido a documentos.

---

## 3. Multi-tenant e isolamento de dados

Toda tabela sensível deve ter:

```sql
organization_id UUID NOT NULL
```

O backend nunca deve aceitar `organization_id` vindo diretamente do frontend como fonte de verdade.

Fluxo correto:

```text
JWT do usuário
→ backend valida token
→ backend identifica user_id
→ backend consulta vínculo user/organization
→ backend aplica organization_id internamente
→ query filtra por organization_id
```

Regra obrigatória:

```text
Nenhuma query sensível pode ser executada sem filtro de organization_id.
```

---

## 4. Autenticação

Recomendação inicial:

```text
Amazon Cognito + JWT
```

Requisitos:

- validar assinatura do token;
- validar expiração;
- validar audience/client_id;
- validar issuer;
- mapear usuário interno;
- mapear organização;
- mapear papel/permissão.

Rotas públicas permitidas no MVP:

```text
GET /health
POST /auth/callback futuro
```

Todo o restante deve exigir autenticação.

---

## 5. Autorização e RBAC

Perfis recomendados:

| Perfil | Permissões |
|---|---|
| owner | Controle total da organização |
| admin | Gerencia usuários, casos e configurações |
| analyst | Revisa casos e relatórios |
| client | Cria casos e visualiza seus relatórios |
| support | Suporte técnico limitado |

Regras:

- cliente não acessa casos de outro cliente;
- analista só acessa casos da própria organização;
- admin não acessa documentos de outro tenant;
- owner gerencia usuários da própria organização;
- toda alteração de permissão gera auditoria.

---

## 6. S3 privado

Documentos devem ficar em bucket privado.

Proibido:

```text
bucket público
URL permanente
chave AWS no frontend
download sem validação de permissão
```

Obrigatório:

```text
presigned URL temporária
validação de usuário
validação de organização
validação de permissão
validação de tipo e tamanho do arquivo
criptografia no bucket
```

---

## 7. Upload seguro

Antes de aceitar upload:

- validar extensão;
- validar MIME type;
- validar tamanho máximo;
- gerar hash;
- registrar metadados;
- associar ao caso;
- associar à organização;
- registrar auditoria.

Tipos iniciais permitidos:

```text
application/pdf
image/jpeg
image/png
application/vnd.openxmlformats-officedocument.wordprocessingml.document
```

---

## 8. Segredos e variáveis sensíveis

Nunca colocar no código:

- chaves de API;
- tokens;
- senha de banco;
- access key AWS;
- secret key AWS;
- chave OpenAI;
- credenciais de terceiros.

Usar:

```text
AWS Secrets Manager
AWS SSM Parameter Store
.env local somente para desenvolvimento
.env.example sem valores reais
```

---

## 9. Auditoria

A tabela `audit_log` deve registrar:

- login;
- criação de caso;
- alteração de caso;
- upload de documento;
- download de documento;
- consulta externa;
- execução de agente;
- aprovação de relatório;
- alteração de permissão;
- exclusão lógica de dados;
- tentativa de acesso negado.

Campos mínimos:

```text
id
organization_id
user_id
action
entity_type
entity_id
ip_address
user_agent
metadata
created_at
```

---

## 10. Logs

Logs técnicos devem evitar dados pessoais desnecessários.

Permitido:

```text
job_id
case_id
organization_id
status
tempo de execução
erro técnico
```

Evitar:

```text
CPF
RG
endereço
telefone
contrato completo
texto integral de documento
token
senha
chave de API
```

---

## 11. LGPD — bases e cuidados

O sistema deve permitir:

- rastrear finalidade de tratamento;
- registrar consentimento quando aplicável;
- justificar consulta externa;
- auditar acesso;
- excluir ou anonimizar dados quando necessário;
- restringir acesso por perfil;
- evitar retenção desnecessária.

Campos recomendados em entidades sensíveis:

```text
created_at
updated_at
deleted_at
created_by
updated_by
retention_until
```

---

## 12. APIs externas

Toda consulta externa deve registrar:

- provedor;
- endpoint lógico;
- parâmetros normalizados;
- hash da consulta;
- data/hora;
- usuário solicitante;
- caso relacionado;
- organização;
- resposta bruta quando permitido;
- resposta normalizada;
- status;
- erro, se houver.

Tabela sugerida:

```text
external_queries_cache
```

---

## 13. Revisão humana

Relatórios jurídicos não devem ser entregues automaticamente sem revisão.

Fluxo obrigatório:

```text
Agente gera minuta
→ Compliance valida riscos
→ Analista humano revisa
→ Analista aprova ou rejeita
→ Sistema libera relatório final
```

---

## 14. Checklist antes do deploy

- [ ] `.env` não está commitado.
- [ ] `.env.example` não possui segredos reais.
- [ ] S3 não está público.
- [ ] Rotas sensíveis exigem autenticação.
- [ ] Queries filtram por `organization_id`.
- [ ] `audit_log` está ativo.
- [ ] CORS está restrito.
- [ ] Upload valida tipo/tamanho.
- [ ] Secrets ficam no Secrets Manager ou SSM.
- [ ] CloudWatch está configurado.
- [ ] AWS Budgets está configurado.
- [ ] Revisão humana está exigida para relatório final.

---

## 15. Conclusão

Segurança e LGPD não devem ser adicionadas no final. Elas fazem parte da fundação do projeto.

A regra principal é:

```text
Nenhum dado sensível sem autenticação, autorização, tenant e auditoria.
```
