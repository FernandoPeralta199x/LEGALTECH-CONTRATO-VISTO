# LegalTech Frontend

Frontend inicial em Next.js + TypeScript para o projeto LegalTech AWS V2.

Esta entrega cria a base visual e estrutural do app web, com login/JWT local de desenvolvimento, integracao inicial das telas de `clients`, `cases` e `documents` com o backend FastAPI real e refinamentos de UX para loading, erro, vazio, formularios e feedback visual. Ainda nao ha Cognito real, refresh token, cadastro real de usuario, upload real em S3, OCR, IA/RAG ou APIs externas.

## Stack

- Next.js
- React
- TypeScript
- Tailwind CSS
- lucide-react para icones

## Configuracao local

Crie o arquivo `.env.local` a partir do exemplo:

```powershell
Copy-Item .env.example .env.local
```

Variaveis publicas usadas nesta etapa:

```env
NEXT_PUBLIC_APP_NAME=LegalTech AWS V2
NEXT_PUBLIC_APP_ENV=local
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK=true
```

Para teste em celular na mesma rede, suba a API em `0.0.0.0:8000`, o
frontend em `0.0.0.0:3000` e use:

```env
NEXT_PUBLIC_API_BASE_URL=http://192.168.0.102:8000
```

Atenção: variáveis NEXT_PUBLIC_* são expostas no navegador. Nunca coloque secrets, tokens, senhas ou dados sensíveis nelas.

`NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK=true` permite que as telas integradas usem dados ficticios locais quando o backend nao estiver rodando. Para validar falhas reais de API/autorizacao sem fallback, use:

```env
NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK=false
```

Para `staging` e `prod`, use `NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK=false` e a URL publica da API do ambiente. O frontend nao deve receber client secret Cognito, chaves AWS, tokens permanentes ou secrets de APIs externas.

Referencia completa de ambientes:

```text
docs/ENVIRONMENT_VARIABLES.md
docs/AWS_DEPLOYMENT_PLAN.md
docs/SECURITY_CHECKLIST_AWS.md
```

## Instalar e rodar

```powershell
cd legaltech-aws\apps\frontend
npm install
npm run dev
```

Abra:

```text
http://localhost:3000
```

## Rodar backend local

Para consumir a API real, suba o backend conforme o README de `apps/api`. Fluxo resumido:

```powershell
cd legaltech-aws
docker compose up -d postgres

cd apps\api
Copy-Item .env.example.local .env
$env:DATABASE_URL="postgresql+psycopg://legaltech:legaltech_dev@localhost:5432/legaltech"
alembic upgrade head

cd ..\..
Get-Content database\local\seed_example_organization.sql | docker compose exec -T postgres psql -U legaltech -d legaltech

cd apps\api
python -m src.modules.admin.seed_roles_permissions `
  --organization-id 11111111-1111-4111-8111-111111111111 `
  --actor-user-id 22222222-2222-4222-8222-222222222222

uvicorn src.main:app --reload
```

O backend local deve permitir CORS para `http://localhost:3000` ou
`http://127.0.0.1:3000` via `CORS_ALLOWED_ORIGINS`. Para teste mobile local,
inclua tambem `http://192.168.0.102:3000`.

Health check esperado:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Comandos de validacao

```powershell
npm run test
npm run typecheck
npm run lint
npm run build
```

## Estados de UX

As telas integradas usam componentes compartilhados para manter feedback consistente:

- `LoadingState`: carregamento com contexto e skeletons.
- `ErrorState`: falhas de carregamento com acao de tentar novamente.
- `EmptyState`: telas vazias com CTA claro.
- `FormField`, `TextInput`, `TextArea`, `SelectInput`: campos com erro, hint e estado disabled/loading.
- `Notification`: aviso inline para sucesso, erro, fallback e mensagens informativas.
- `ConfirmDialog`: confirmacao para acoes sensiveis, como enfileirar processamento.

Validacoes atuais:

- Clients: nome obrigatorio; documento opcional com validacao leve; e-mail opcional com formato basico.
- Cases: titulo obrigatorio; cliente vinculado obrigatorio; tipo e prioridade controlados.
- Documents: caso vinculado obrigatorio; nome obrigatorio; tipo, status e tamanho controlados; cria apenas metadata.
- Login: JWT dev e obrigatorio para acessar telas internas; e-mail e senha sao campos visual/dev e nao autenticam no backend local.

Quando `NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK=true`, falhas de rede/conexao exibem aviso de fallback local. Erros `401`, `403`, validacao e respostas de erro do backend continuam visiveis e nao sao mascarados por mock.

## Rotas iniciais

```text
/             Visao operacional inicial
/login        Login dev local
/dashboard    Resumo da operacao usando clients/cases/documents integraveis
/clients      Lista e cria clientes via backend real
/cases        Lista e cria casos via backend real
/cases/[id]   Detalhe do caso com abas e fallback controlado
/documents    Lista documentos, cria metadados, gera URL e enfileira processamento
/settings     Configuracoes locais de organizacao, seguranca, notificacoes e tema
```

As rotas `/dashboard`, `/clients`, `/cases` e `/documents` usam uma guarda visual local. Sem sessao salva, o app redireciona para `/login`.

## Login/JWT dev local

O login atual existe apenas para desenvolvimento local. Ele deixa claro que
e-mail e senha sao auxiliares visuais/dev; o acesso real ao MVP local depende do
JWT dev gerado pelo backend. Ele permite:

- selecionar papel dev: `owner`, `admin`, `analyst`, `client` ou `support`;
- colar um JWT dev gerado pelo backend;
- validar o JWT dev no backend via `GET /api/v1/me` antes de salvar a sessao;
- salvar a sessao em `localStorage` somente quando a API local aceitar o JWT dev;
- enviar `Authorization: Bearer <token>` automaticamente pelo `apiClient`;
- limpar a sessao pelo botao `Sair` no Header.

Gerar token dev pelo backend, a partir de `apps/api`:

```powershell
$TOKEN = python -m src.modules.admin.dev_jwt `
  --organization-id 11111111-1111-4111-8111-111111111111 `
  --user-id 22222222-2222-4222-8222-222222222222 `
  --email dev.local@example.test `
  --role admin
```

Depois, cole o valor de `$TOKEN` no campo `JWT dev do backend` em `/login`.
Se o campo de token ficar vazio, o frontend mostra erro e nao redireciona para
as telas internas.

Importante:

- esse fluxo nao e producao;
- nao use Cognito real nesta tela;
- nao cole tokens reais de usuarios;
- nao coloque segredos no frontend;
- `NEXT_PUBLIC_*` e sempre publico no navegador;
- `organization_id` continua vindo do token/contexto autenticado, nunca de payloads enviados pela UI.

Labels de papeis exibidas no frontend:

```text
owner   = Proprietário
admin   = Administrador
analyst = Analista
client  = Cliente
support = Suporte
```

## Como testar telas manualmente

Com backend rodando e JWT dev colado:

1. Acesse `/login`, selecione um papel e cole o JWT dev.
2. Abra `/clients`, tente enviar o formulario vazio, depois crie um cliente ficticio.
3. Abra `/cases`, tente criar sem titulo ou sem cliente, depois crie um caso ficticio vinculado ao cliente.
4. Abra `/documents`, tente criar sem caso/nome/tamanho valido, depois crie um metadado ficticio.
5. Em `/documents`, gere URL temporaria e confirme o enfileiramento de processamento.
6. Abra `/dashboard` e `/cases/[id]` para validar loading, empty states, fallback e dados integraveis.

Com backend desligado e `NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK=true`, as mesmas telas devem mostrar aviso de fallback mockado. Com `NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK=false`, falhas de conexao devem aparecer como erro sem trocar para dados mockados.

## Estrutura

```text
apps/frontend/
+-- components/
|   +-- AppLayout.tsx
|   +-- Button.tsx
|   +-- Card.tsx
|   +-- ConfirmDialog.tsx
|   +-- EmptyState.tsx
|   +-- ErrorState.tsx
|   +-- FormField.tsx
|   +-- Header.tsx
|   +-- LoadingState.tsx
|   +-- Notification.tsx
|   +-- PageTitle.tsx
|   +-- Sidebar.tsx
|   +-- StatusBadge.tsx
|   +-- AuthGuard.tsx
+-- lib/
|   +-- cn.ts
|   +-- formatters.ts
|   +-- mockData.ts
+-- services/
|   +-- apiClient.ts
|   +-- cases.ts
|   +-- clients.ts
|   +-- documents.ts
+-- src/app/
|   +-- clients/page.tsx
|   +-- cases/page.tsx
|   +-- dashboard/page.tsx
|   +-- documents/page.tsx
|   +-- login/page.tsx
|   +-- globals.css
|   +-- layout.tsx
|   +-- page.tsx
+-- src/lib/
|   +-- authStorage.ts
|   +-- useDevSession.ts
|   +-- validation.ts
+-- src/services/
|   +-- apiClient.ts
|   +-- auth.ts
|   +-- cases.ts
|   +-- clients.ts
|   +-- documents.ts
|   +-- fallback.ts
+-- src/types/
|   +-- auth.ts
+-- types/
    +-- api.ts
    +-- domain.ts
    +-- index.ts
```

## Integracao com a API

O arquivo `src/services/apiClient.ts` usa `NEXT_PUBLIC_API_BASE_URL` e envia `Authorization: Bearer <token>` quando houver token dev salvo. O arquivo `services/apiClient.ts` permanece como reexport para compatibilidade.

Services integrados:

```text
src/services/clients.ts
src/services/cases.ts
src/services/documents.ts
```

Endpoints usados pelas telas:

```text
GET  /api/v1/clients
POST /api/v1/clients
GET  /api/v1/cases
POST /api/v1/cases
GET  /api/v1/cases/{case_id}
GET  /api/v1/documents
POST /api/v1/documents
GET  /api/v1/documents/{document_id}/download-url
POST /api/v1/documents/{document_id}/enqueue-processing
```

Fallback mockado:

- usado apenas quando a API fica indisponivel por falha de rede/conexao;
- nao mascara `401`, `403`, erros de validacao ou erros retornados pelo backend;
- continua usando apenas dados ficticios locais de `lib/mockData.ts`;
- pode ser desligado com `NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK=false`.

Ainda mockado nesta etapa:

- agentes ativos no dashboard;
- relatorios, revisoes, timeline e partes detalhadas do caso;
- upload real de arquivo no frontend;
- Cognito, refresh token, S3 real, OCR, IA/RAG e APIs externas.

Regras mantidas nesta base:

- nenhum `organization_id` e enviado como fonte de autoridade;
- nenhum segredo ou chave real fica no frontend;
- token salvo em `localStorage` apenas quando veio do JWT dev colado e permitido somente para desenvolvimento local;
- payloads de criacao enviam apenas campos aceitos pelo backend;
- fallback local usa dados mockados e ficticios;
- upload real, Cognito, S3 e IA/RAG ficam para etapas futuras.
