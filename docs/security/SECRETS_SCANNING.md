# Secrets Scanning

Use este checklist para procurar segredos no repositório.

## Padrões suspeitos

Procurar:

- AWS_ACCESS_KEY
- AWS_SECRET
- AWS_SECRET_ACCESS_KEY
- SECRET
- PASSWORD
- TOKEN
- PRIVATE_KEY
- DEV_JWT_SECRET
- Bearer eyJ
- postgresql://
- mysql://
- mongodb://
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GOOGLE_API_KEY
- BEGIN PRIVATE KEY
- CPF
- CNPJ

## Arquivos críticos

Verificar:

- `.env`
- `.env.local`
- `.env.production`
- `.env.example`
- `.gitignore`
- docs
- tests
- mocks
- logs
- arquivos temporários

## Se encontrar segredo

1. Não mostrar valor completo.
2. Mascarar no relatório.
3. Substituir por placeholder.
4. Ajustar `.gitignore`.
5. Informar se pode ser necessário limpar histórico Git.
