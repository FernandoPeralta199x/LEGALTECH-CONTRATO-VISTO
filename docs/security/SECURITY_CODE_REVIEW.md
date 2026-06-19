# Security Code Review

Use este checklist para revisar segurança geral do código.

## Procurar

- secrets versionados;
- tokens;
- JWT completo;
- senhas hardcoded;
- chaves AWS;
- API keys;
- URLs sensíveis;
- dados pessoais;
- CPF/CNPJ real;
- e-mails reais em massa;
- conteúdo real de contratos;
- `.env` versionado;
- logs versionados;
- mocks perigosos;
- fallback inseguro;
- CORS aberto;
- rotas protegidas sem autenticação;
- stack trace exibido ao usuário.

## Regras

- Nunca exibir segredo completo.
- Mascarar tokens e chaves.
- Substituir valores sensíveis por placeholders.
- Corrigir `.gitignore` quando necessário.
- Registrar risco e impacto.
