# Secure Logging

Use este checklist para revisar logs e erros.

## Não logar

- JWT completo;
- segredo;
- senha;
- API key;
- conteúdo integral de contrato;
- payload sensível;
- CPF/CNPJ;
- dados pessoais desnecessários;
- stack trace para usuário final.

## Garantir

- logs locais ficam em pasta ignorada;
- erros técnicos ficam no backend/log local;
- usuário recebe mensagem amigável;
- documentação não contém token real;
- console do front-end não imprime dados sensíveis.
