import { ApiClientError, ApiNetworkError } from "../services/apiClient";

const isDev = process.env.NODE_ENV !== "production";

export function errorMessage(
  error: unknown,
  fallback = "Não foi possível carregar os dados."
): string {
  if (error instanceof ApiNetworkError) {
    return isDev
      ? "API local indisponível. Verifique se o Docker Compose está rodando postgres + api em 127.0.0.1:8000 e se o JWT dev foi colado no login."
      : "Serviço temporariamente indisponível.";
  }

  if (error instanceof ApiClientError) {
    if (error.status === 401 || error.status === 403) {
      return isDev
        ? "Sessão dev inválida ou sem permissão. Gere um novo JWT dev e faça login novamente."
        : "Sem autorização.";
    }

    if (error.status === 500) {
      return isDev
        ? "Erro interno da API local. Verifique os logs com: docker compose logs --tail 100 api"
        : "Erro interno do servidor.";
    }

    return isDev ? `${error.code}: ${error.message}` : "Erro ao comunicar com o servidor.";
  }

  if (error instanceof Error) {
    return isDev ? error.message : fallback;
  }

  return fallback;
}
