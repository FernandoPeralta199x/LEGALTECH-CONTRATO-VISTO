# Threat Modeling

Use este checklist para pensar em abuso do sistema.

## Avaliar ameaças

- acesso indevido a documentos;
- vazamento de JWT;
- vazamento de contrato;
- CORS permissivo;
- upload inseguro;
- fallback/mock escondendo erro real;
- erro técnico expondo detalhes internos;
- arquivos temporários versionados;
- `NEXT_PUBLIC_*` expondo informação indevida;
- `organization_id` vindo do front-end como fonte de verdade;
- autenticação visual confundida com autorização real.

## Classificação

Classificar riscos em:

- Crítico;
- Alto;
- Médio;
- Baixo.

## Entrega

Para cada risco, informar:

- descrição;
- impacto;
- evidência;
- recomendação;
- prioridade.
