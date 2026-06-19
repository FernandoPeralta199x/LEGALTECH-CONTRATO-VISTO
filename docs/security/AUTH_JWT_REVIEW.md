# Auth/JWT Review

Use este checklist para revisar autenticação dev e JWT.

## Garantir

- sem JWT não acessa rota protegida;
- JWT inválido bloqueia;
- JWT válido entra;
- logout remove token/sessão;
- `Authorization: Bearer` é enviado;
- front-end não gera JWT;
- front-end não contém segredo;
- JWT completo não aparece na UI;
- JWT completo não aparece no console;
- JWT completo não aparece em logs;
- JWT completo não aparece em erro;
- erro de autenticação não vaza detalhe sensível;
- `organization_id` vem do token/back-end, não do front-end.

## Proibido nesta revisão

- implementar Cognito real;
- trocar arquitetura de autenticação sem necessidade;
- quebrar login dev aprovado.
