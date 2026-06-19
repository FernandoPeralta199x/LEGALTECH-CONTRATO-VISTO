# Secure Documentation

Use este checklist para documentação de segurança.

## Criar ou atualizar

- `docs/SECURITY_READY.md`
- `docs/KNOWN_LIMITATIONS.md`, se necessário
- `docs/MVP_LOCAL_RUNBOOK.md`, se necessário
- `docs/SECURITY_LGPD.md`, se necessário
- `README.md`, se necessário

## `SECURITY_READY.md` deve conter

- status do hardening local;
- o que foi verificado;
- o que foi corrigido;
- limitações do MVP local;
- o que ainda não está pronto para produção;
- checklist antes de deploy real;
- checklist antes de AWS;
- riscos conhecidos;
- orientações de secrets;
- orientações de CORS;
- orientações de JWT dev;
- orientações de logs;
- próximos passos recomendados.

## Regra final

Não declarar production-ready.

Usar conclusão:

“Projeto reforçado para MVP local controlado, ainda não production-ready.”
