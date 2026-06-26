# ADR-0003: Endurecimento da autenticacao local (hash, auditoria de seguranca, rate-limit)

**Status:** Proposed
**Date:** 2026-06-25
**Deciders:** Fernando Peralta (owner)
**Relacionados:** AUTH-05, M-08, SEC-02, ADR-0001 (Cognito e o alvo de producao)

## Context

O caminho de auth local/self-registration existe e funciona, mas com fraquezas para um padrao profissional:

- **Hash:** PBKDF2-HMAC-SHA256 com 100k iteracoes (abaixo do OWASP atual de ~600k), comentado como "NOT for production". Formato `pbkdf2_sha256$salt$digest` nao guarda o numero de iteracoes, impossibilitando subir o custo sem quebrar hashes antigos.
- **Politica:** 8 a 16 caracteres. O teto de 16 contraria o NIST 800-63B (comprimento e o fator dominante; passphrases proibidas). Sem denylist de senhas vazadas.
- **Rate-limit:** janela fixa em memoria, so por IP -> brute-force distribuido contra uma conta passa; confia em `request.client.host` (atras de ALB/CloudFront o IP real esta no X-Forwarded-For).
- **Auditoria (M-08):** nenhum evento de auth gera `audit_log`. Register/verify/login/falha/lockout nao deixam trilha (lacuna de forense e LGPD).

Forca contraria: producao usa Cognito (ADR-0001), que faz hashing e parte do rate-limit. Logo, sobre-investir no hash local e desperdicio; o valor duravel esta em auditoria + rate-limit, que importam com qualquer provider.

Restricao de verificacao: cada incremento e validado pela suite (baseline 214 verde); sem migration nesta entrega.

## Decision

Quatro mudancas, cada uma um diff isolado, na ordem de maior valor de seguranca provider-agnostico primeiro:

1. **M-08 - Canal de auditoria de seguranca.** Organizacao-sistema sentinela (UUID reservado, seed idempotente) para eventos de auth pre-org (register, verify, falha de login por e-mail inexistente). Emitir `audit_log` em register, verify-email, login OK, login falho e estouro de rate-limit, via `AuditLogService.record_event`, sanitizando PII (nunca senha/token; e-mail mascarado; sem CPF). Reusa a infra existente, sem migration.
2. **SEC-02 fatia 2 - Rate-limit por conta + XFF seguro.** Somar chave por e-mail a chave por IP. Lockout suave (conta apenas falhas; backoff temporario em vez de bloqueio rigido). Resolver IP real do X-Forwarded-For apenas sob flag `trusted_proxy_enabled=false` por padrao. Mantem o Protocol RateLimitStore (troca por Redis/ElastiCache documentada).
3. **AUTH-05.1 - Abstracao PasswordHasher + custo OWASP + re-hash transparente.** Strategy com versao/parametros embutidos no hash (`pbkdf2_sha256$600000$salt$digest`); PBKDF2-600k default sem dependencia nova; re-hash no login quando o hash for de parametro antigo. Argon2id pluggable como follow-up (exige aprovar argon2-cffi).
4. **AUTH-05.2 - Politica NIST.** min 12, max 128, denylist offline de senhas comuns/vazadas; complexidade leve mantida. Mensagens claras no frontend.

## Options Considered

### Decisao A - Algoritmo de hash
| Dimensao | PBKDF2-600k (stdlib) [escolhida agora] | Argon2id (argon2-cffi) | Manter 100k |
|---|---|---|---|
| Seguranca | Boa (OWASP-aceitavel) | Otima (memory-hard) | Insuficiente |
| Dependencia | Nenhuma | Pacote novo (aprovacao) | Nenhuma |
| Custo de troca futura | 1 linha (via abstracao) | - | Alto (formato sem versao) |

Escolha: abstracao + PBKDF2-600k agora; Argon2id vira swap trivial quando o pacote for aprovado. Cognito reduz a urgencia.

### Decisao B - Auditoria de eventos pre-org
| Opcao | Captura pre-org | Migration | Veredito |
|---|---|---|---|
| A) Org-sistema sentinela [escolhida] | Sim | Nao | Pipeline unico, sem schema |
| B) Coluna organization_id nullable | Sim | Sim | Polui schema por caso de borda |
| C) Auditar so pos-org (login) | Nao | Nao | Perde register/verify = onde mora o abuso |

### Decisao C - Rate-limit por conta
Lockout rigido por conta cria vetor de DoS (atacante bloqueia a vitima). Lockout suave (backoff por falhas) escolhido.

## Trade-off Analysis

O eixo central e seguranca duravel vs. esforco dado que Cognito e o destino. Por isso priorizamos auditoria e rate-limit (valem em qualquer provider) e tratamos hash/politica como endurecimento do caminho local com arquitetura a prova de futuro (versao no hash, abstracao, re-hash) em vez de forca bruta de algoritmo.

## Consequences

Fica mais facil: forense de auth (trilha completa sanitizada); subir o custo do hash no futuro; trocar para Argon2id ou Redis sem reescrita.
Fica mais dificil: testes precisam semear a org-sistema; o login passa a ter um passo de re-hash condicional.
A revisitar: rate-limit distribuido (Redis) e Argon2id quando for para staging/prod multi-instancia.

## Action Items (cada item = 1 diff, TDD)

1. [ ] M-08 - org-sentinela + emissao de audit_log sanitizado nos 5 eventos
2. [ ] SEC-02 f2 - chave por conta + backoff suave + XFF sob flag
3. [ ] AUTH-05.1 - PasswordHasher + PBKDF2-600k + re-hash no login
4. [ ] AUTH-05.2 - politica NIST (min 12 / max 128 / denylist) + UX do frontend

## Estrategia de testes

- M-08: evento emitido com payload sem senha/token, e-mail mascarado; org-sentinela usada quando user sem org; idempotencia do seed.
- SEC-02: 6 falhas/conta de IPs distintos -> 429; IP legitimo nao afetado por terceiros; XFF ignorado quando trusted_proxy_enabled=false.
- AUTH-05.1: hash antigo (100k) ainda valida; login re-hasheia para 600k; round-trip 600k; compare_digest constante.
- AUTH-05.2: rejeita <12 e senha em denylist; aceita passphrase de 40 chars.
- Gate: suite completa (214 baseline) verde + py_compile antes de cada commit.
