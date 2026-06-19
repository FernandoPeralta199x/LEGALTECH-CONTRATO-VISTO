# Dependency Audit

Use este checklist para auditoria de dependências.

## Front-end

Executar:

```bash
cd apps/frontend
npm run test
npm run typecheck
npm run lint
npm run build
npm audit --audit-level=high
```

## Back-end

Executar:

```bash
cd apps/api
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall src tests
```

## Regras

- Não fazer upgrade major automaticamente.
- Corrigir somente se for seguro.
- Se não puder corrigir, documentar risco pendente.
- Não instalar ferramenta nova sem necessidade objetiva.
