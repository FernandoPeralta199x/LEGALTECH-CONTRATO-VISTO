# ADR-0001: Autenticação de produção (LegalTech / HOPE / Contrato Visto)

**Status:** Accepted
**Date:** 2026-06-23
**Deciders:** Fernando Peralta (owner)
**Relacionados:** AUTH-04, AUTH-05, AUTH-07, AUTH-02, AUTH-03, TENANT-01/02, C-01, C-02

## Contexto

Hoje a validação de token já é dual e gateada (`src/core/auth.py`):
- `CognitoJWTVerifier` (RS256 via JWKS) e `LocalDevJWTVerifier` (HS256).
- `dev_jwt` só ativa com `auth_provider=dev_jwt` E `app_env=local` E `dev_jwt_enabled` (default `False`).
- O backend é a autoridade: resolve `user_id`, `organization_id` e `role` a partir das claims.

Lacuna central (C-01): o Cognito está integrado apenas para **validar** token. Os endpoints
`login/register/verify_email` emitem **dev_jwt** (HS256) em qualquer ambiente — não existe
um fluxo real de *login de produção*. Em prod (`auth_provider=cognito`), esse dev_jwt seria
rejeitado pelo verificador. Consequência: a UI parece "logar", mas não há autenticação real fora de local.

Forças em jogo: segurança (LGPD, isolamento multi-tenant), responsabilidade sobre credenciais,
tempo de implementação, e a exigência do plano de não guardar token real em `localStorage`.

## Decisão

Adotar **AWS Cognito como IdP de produção** com **Opção A — Hosted UI (OIDC Authorization Code + PKCE)**.

O frontend redireciona para a Hosted UI do Cognito, que cuida de login/cadastro/senha/MFA/recuperação.
O backend troca o `code`, valida o JWT (verificador já implementado), resolve o usuário interno e emite
um **cookie de sessão HttpOnly/Secure/SameSite**. O backend permanece autoridade de RBAC, tenant e audit_log.
Os endpoints de login/registro/senha locais ficam **bloqueados fora de `local`** (gate `AUTH-07`),
retornando erro controlado (nunca 500). Nenhum token real é guardado em `localStorage`.

**Justificativa (escolha A sobre B):** na Opção A o nosso backend nunca recebe a senha, eliminando uma
classe inteira de risco e responsabilidade (LGPD, log acidental, hashing, lockout). MFA, política de senha
e recuperação vêm prontos. OIDC Authorization Code + PKCE é o padrão de mercado e reduz código custom e
superfície de ataque. O custo único de UX (Hosted UI) é mitigado por customização/branding.

## Opções consideradas

### Opção A — Cognito Hosted UI (OIDC Authorization Code + PKCE) [ESCOLHIDA]
O Cognito cuida de login/cadastro/senha/MFA; o backend troca o `code`, valida o JWT e emite o cookie de sessão.

| Dimensão | Avaliação |
|---|---|
| Complexidade | Baixa–Média |
| Custo | Baixo (Cognito gerenciado) |
| Escalabilidade | Alta (gerenciado pela AWS) |
| Familiaridade do time | Média |
| Responsabilidade s/ credenciais | Nenhuma no nosso backend |

**Prós:** sem manuseio de senha no nosso código; MFA/reset/políticas prontos; padrão OIDC; menor superfície de ataque.
**Cons:** UX de login passa pela Hosted UI (customização limitada); ajuste do fluxo de callback no frontend.

### Opção B — Login proxied pelo backend (Cognito `InitiateAuth` / SRP via SDK)
Mantém a UI de login atual; o backend chama o Cognito (USER_PASSWORD_AUTH/SRP), recebe os tokens e seta o cookie HttpOnly.

| Dimensão | Avaliação |
|---|---|
| Complexidade | Média–Alta |
| Custo | Baixo |
| Escalabilidade | Alta |
| Familiaridade do time | Média |
| Responsabilidade s/ credenciais | Parcial (senha trafega pelo nosso backend) |

**Prós:** preserva a UI/UX de login atual; sessão centralizada no cookie; controle do fluxo.
**Cons:** mais código no backend; senha passa pela nossa camada; precisa app client secret no Secrets Manager; hardening/rate-limit extra.

### Opção C — Auth próprio (Argon2id + JWT/refresh próprios) — rejeitada
**Cons:** assume toda a responsabilidade de credenciais/MFA/rotação; maior risco LGPD e de implementação. Contradiz a direção do plano.

### Opção D — IdP terceiro (Auth0/Clerk/Entra) — rejeitada para v1
**Cons:** novo fornecedor/custo; AWS já é o alvo de infra. Reavaliar só se Cognito limitar UX.

## Análise de trade-off

A e B mantêm o Cognito como fonte de verdade de credenciais (menor risco que C/D). A diferença é
**onde a senha é digitada**: na Hosted UI (A, nosso backend nunca vê senha) ou na nossa UI com proxy
(B, senha passa pelo backend). A é mais segura e tem menos código; B preserva a UX atual ao custo de
mais responsabilidade e hardening. Ambas convergem para o mesmo estado final: cookie HttpOnly +
backend validando JWT + RBAC/tenant no backend. A foi escolhida pelo menor risco e menor superfície.

## Consequências

**Fica mais fácil:** remover o `dev_jwt` de qualquer ambiente não-local; eliminar token em `localStorage`;
MFA e políticas de senha; auditar login real.
**Fica mais difícil:** o fluxo de callback/sessão no frontend muda; provisionar Cognito (pool, client,
domínio, claims `custom:organization_id`/`custom:role`) e Secrets Manager; migrar usuários locais existentes.
**A revisitar:** mapeamento de claims -> tenant/role; verificação de `aud` no `CognitoJWTVerifier`
(hoje `verify_aud=False`); substituir PBKDF2 (se restar qualquer auth local).

## Action items
1. [x] Decidir Opção A ou B -> **Opção A**.
2. [ ] `AUTH-07` — gate de ambiente: `dev_jwt` impossível fora de `local`; endpoints locais retornam erro controlado (não 500).
3. [ ] `AUTH-04` — separar fisicamente o caminho dev_jwt do caminho de produção.
4. [ ] Provisionar Cognito (user pool, app client, domínio Hosted UI, claims `custom:organization_id`/`custom:role`).
5. [ ] Fluxo OIDC Authorization Code + PKCE no frontend; callback no backend; cookie HttpOnly/Secure/SameSite; remover token de `localStorage` (`FRONT-03`).
6. [ ] `AUTH-03`/`TENANT-01` — tenant por convite/aprovação/claim Cognito (fim do `get_default_organization_id`).
7. [ ] Endurecer `CognitoJWTVerifier` (`aud`); definir destino do PBKDF2 (`AUTH-05`).
8. [ ] `SEC-02` — rate limiting nos endpoints de auth.
