# Runbook — Autenticação de produção com Cognito (Opção A)

**Decisão de referência:** `docs/adr/ADR-0001-autenticacao-producao.md` (Accepted, Opção A — Hosted UI / OIDC Authorization Code + PKCE).
**Objetivo:** especificar, ponta a ponta, como ligar o Cognito como IdP de produção. Executável quando a infra AWS estiver disponível. Não cria recursos AWS por si só.

> Estado do código hoje: o backend **já valida** o JWT do Cognito (`src/core/cognito.py` — assinatura via JWKS, `issuer`, `token_use`, `client_id`/`aud`, claims `custom:organization_id`/`custom:role`). O `AUTH-07` desliga os endpoints de auth local fora de `local`. Falta: provisionar Cognito, o fluxo OIDC no frontend, o callback/sessão no backend e a sincronização Cognito→usuário interno (tenant).

---

## 1. Pré-requisitos
- Conta AWS com permissão para Cognito, e a região alvo (padrão do projeto: `sa-east-1`).
- Domínio do frontend (para callback OIDC) e do backend (API).
- Decisão de tipo de token a validar: **ID token** (padrão do projeto: `COGNITO_TOKEN_USE=id`) ou access token.

## 2. Provisionar o User Pool
1. Criar **User Pool**.
2. **Atributos customizados** (imutáveis após criação — definir agora):
   - `custom:organization_id` (string)
   - `custom:role` (string)
   Os nomes devem casar com `COGNITO_ORGANIZATION_CLAIM` e `COGNITO_ROLE_CLAIM` (defaults `custom:organization_id` / `custom:role`).
3. **Política de senha** e **MFA** (recomendado: MFA opcional/obrigatório conforme risco). O Cognito passa a ser dono de senha/reset/MFA — o backend não guarda senha.
4. **Verificação de e-mail**: ativar confirmação por e-mail (o Cognito envia e confirma).

## 3. Provisionar o App Client (OIDC + PKCE)
1. Criar **App client** público (sem client secret) para SPA, ou confidencial se o callback for trocado no backend.
2. Habilitar **Authorization Code Grant** + **PKCE**. Desabilitar implicit flow.
3. **Callback URLs**: `https://<frontend>/auth/callback`. **Sign-out URLs** conforme o app.
4. Scopes: `openid email profile`.
5. Anotar o **App client ID** → `COGNITO_CLIENT_ID`.

## 4. Hosted UI
1. Configurar **domínio do Cognito** (domínio gerenciado ou customizado) para a Hosted UI.
2. (Opcional) Branding/CSS para aproximar da identidade visual.
3. Proteger o domínio com **WAF + rate limiting** (camada do `SEC-02`).

## 5. Variáveis de ambiente do backend
Alinhadas a `apps/api/src/core/config.py`:

| Variável | Valor em produção | Observação |
|---|---|---|
| `APP_ENV` | `staging` / `production` | nunca `local` em prod |
| `AUTH_PROVIDER` | `cognito` | seleciona o `CognitoJWTVerifier` |
| `DEV_JWT_ENABLED` | `false` | obrigatório fora de `local` |
| `AWS_REGION` | ex. `sa-east-1` | |
| `COGNITO_REGION` | região do pool | default cai em `AWS_REGION` |
| `COGNITO_USER_POOL_ID` | id do pool | deriva `issuer`/`jwks_url` |
| `COGNITO_CLIENT_ID` | id do app client | **obrigatório** (valida audiência) |
| `COGNITO_ISSUER` | (opcional) override | default: `https://cognito-idp.<region>.amazonaws.com/<poolId>` |
| `COGNITO_JWKS_URL` | (opcional) override | default: `<issuer>/.well-known/jwks.json` |
| `COGNITO_ORGANIZATION_CLAIM` | `custom:organization_id` | tenant |
| `COGNITO_ROLE_CLAIM` | `custom:role` | RBAC |
| `COGNITO_TOKEN_USE` | `id` ou `access` | tem de casar com o token validado |

Segredos (se app client confidencial) → **Secrets Manager/SSM**, nunca versionados.

## 6. Fluxo OIDC (frontend + backend)
```
Frontend  -> redirect para Hosted UI (authorize, PKCE)
Cognito   -> login/cadastro/confirmacao/MFA
Cognito   -> redirect para /auth/callback?code=...
Frontend  -> envia code ao backend (ou troca direto com PKCE)
Backend   -> troca code por tokens (token endpoint)
Backend   -> valida JWT (CognitoJWTVerifier: assinatura/issuer/token_use/client_id)
Backend   -> resolve/cria usuario interno e aplica tenant/RBAC
Backend   -> seta cookie de sessao HttpOnly/Secure/SameSite
```
**Regras:** nenhum token real em `localStorage`; sessão por **cookie HttpOnly/Secure/SameSite**; o frontend não decide autorização.

## 7. Sincronização Cognito → usuário interno (tenant)
Conecta com o `AUTH-03`: o usuário que confirma e-mail nasce **sem tenant** (`pending_approval`). A organização é atribuída por um destes caminhos:
1. **Claim Cognito** `custom:organization_id` presente → backend vincula direto (onboarding empresarial controlado).
2. **Convite/aprovação** (`TENANT-01`) → admin atribui org e ativa (reusar `mark_email_verified`/`get_default_organization_id` que ficaram reservados no repositório).
O backend cria/atualiza o usuário interno na primeira autenticação válida (mapeando `sub` Cognito → `external_auth_id`).

## 8. Checklist de segurança
- [ ] `COGNITO_CLIENT_ID` **sempre** definido em prod (sem ele, a checagem de audiência é pulada).
- [ ] `DEV_JWT_ENABLED=false` e `AUTH_PROVIDER=cognito` fora de `local`.
- [ ] `token_use` validado (id/access) coerente com o que o frontend envia.
- [ ] Cookie de sessão HttpOnly/Secure/SameSite; sem token em `localStorage`.
- [ ] MFA habilitado; política de senha forte (no Cognito).
- [ ] Hosted UI atrás de WAF + rate limiting (`SEC-02`).
- [ ] Segredos em Secrets Manager/SSM, nunca versionados.

## 9. Validação em staging
1. Cadastro real via Hosted UI → confirmação por e-mail real.
2. Login real → backend valida JWT, seta cookie, aplica tenant/RBAC.
3. Tentar acessar dados de outro tenant → negado (isolamento).
4. `DEV_JWT_ENABLED=false`: endpoints de auth local respondem 404 (AUTH-07).
5. Token de app client diferente → rejeitado (audiência).

## 10. Rollback
- Manter `AUTH_PROVIDER` como flag de ambiente; reverter para o caminho anterior só em `local`.
- Como Cognito é gerenciado, rollback = repontar env vars / desabilitar o app client; nenhum dado de senha vive no backend.
