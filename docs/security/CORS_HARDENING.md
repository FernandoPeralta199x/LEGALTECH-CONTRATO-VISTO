# CORS Hardening

Use este checklist para revisar CORS.

## Origens permitidas no MVP local

- http://localhost:3000
- http://127.0.0.1:3000
- http://192.168.0.102:3000

## Proibido

- wildcard `*` em ambiente que simule produção;
- liberar qualquer origem sem justificativa;
- deixar CORS de produção aberto.

## Documentar

- `192.168.0.102` é apenas para teste mobile local;
- produção deve ter domínio explícito;
- CORS não substitui autenticação.
