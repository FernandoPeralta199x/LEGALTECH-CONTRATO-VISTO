/**
 * Fonte unica de verdade para deteccao de ambiente de runtime no frontend.
 * Centraliza a politica de seguranca para nao duplicar checagens de NODE_ENV
 * espalhadas pelo codigo (evita divergencia de regra entre arquivos).
 */

export function isProduction(): boolean {
  return process.env.NODE_ENV === "production";
}

/**
 * Politica unica do projeto: nenhuma sessao/token ou PII pode ser persistida
 * no storage do browser (localStorage/sessionStorage) em producao.
 * O caminho de producao e Cognito + cookie HttpOnly/Secure/SameSite.
 *
 * Fail-closed: lanca em producao. `context` identifica o chamador na mensagem.
 */
export function assertBrowserPersistDisallowedInProduction(context: string): void {
  if (isProduction()) {
    throw new Error(
      `[${context}] Persistir sessao/PII em storage do browser nao e permitido em producao. ` +
        "Use Cognito + cookie HttpOnly."
    );
  }
}
