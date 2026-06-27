import { isProduction } from "../lib/runtimeEnv";
import { ApiNetworkError } from "./apiClient";

export type DataSource = "api" | "mock";

export type ServiceResult<T> = {
  data: T;
  fallbackReason?: string;
  source: DataSource;
};

export function isMockFallbackEnabled(): boolean {
  if (isProduction()) return false;
  return process.env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK === "true";
}

export function shouldUseMockFallback(error: unknown): boolean {
  return isMockFallbackEnabled() && error instanceof ApiNetworkError;
}

export function fallbackReason(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Backend indisponivel para desenvolvimento local.";
}
