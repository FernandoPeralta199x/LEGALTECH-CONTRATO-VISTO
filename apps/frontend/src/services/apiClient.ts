import { getStoredToken } from "../lib/authStorage";
import type { ApiError, ApiErrorResponse, ApiResponse, ApiSuccessResponse } from "../../types/api";
import { SOURCE_MODE_VALUES, type SourceMode } from "../../types";

const DEFAULT_API_PORT = "8000";
const LOCAL_API_FALLBACK_HOST = "127.0.0.1";

const DEFAULT_API_TIMEOUT_MS = 30_000;

function normalizeBaseUrl(url: string): string {
  return url.trim().replace(/\/+$/, "");
}

function isLoopbackHost(hostname: string | undefined): boolean {
  if (!hostname) {
    return false;
  }

  return ["127.0.0.1", "localhost", "::1", "[::1]"].includes(hostname);
}

function getRuntimeLocation():
  | { hostname?: string; protocol?: string }
  | null {
  if (typeof window !== "undefined" && window.location) {
    return window.location;
  }

  if ("location" in globalThis) {
    return globalThis.location as { hostname?: string; protocol?: string };
  }

  return null;
}

function rewriteLoopbackForLanAccess(
  configuredBaseUrl: string,
  runtimeLocation: { hostname?: string } | null
): string {
  const browserHost = runtimeLocation?.hostname?.trim();
  if (!browserHost || browserHost === "0.0.0.0" || isLoopbackHost(browserHost)) {
    return normalizeBaseUrl(configuredBaseUrl);
  }

  try {
    const parsedUrl = new URL(configuredBaseUrl);
    if (!isLoopbackHost(parsedUrl.hostname)) {
      return normalizeBaseUrl(configuredBaseUrl);
    }

    parsedUrl.hostname = browserHost;
    return normalizeBaseUrl(parsedUrl.toString());
  } catch {
    return normalizeBaseUrl(configuredBaseUrl);
  }
}

export function resolveApiBaseUrl(): string {
  const runtimeLocation = getRuntimeLocation();
  const configuredBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (configuredBaseUrl) {
    return rewriteLoopbackForLanAccess(configuredBaseUrl, runtimeLocation);
  }

  const hostname = runtimeLocation?.hostname?.trim();
  if (hostname && hostname !== "0.0.0.0") {
    const protocol = runtimeLocation?.protocol === "https:" ? "https:" : "http:";
    return `${protocol}//${hostname}:${DEFAULT_API_PORT}`;
  }

  return `http://${LOCAL_API_FALLBACK_HOST}:${DEFAULT_API_PORT}`;
}

export const apiBaseUrl = resolveApiBaseUrl();

type ApiClientOptions = RequestInit & {
  token?: string;
  timeoutMs?: number;
};

function createTimeoutSignal(timeoutMs: number): AbortSignal {
  if (typeof AbortController === "undefined") {
    return undefined as unknown as AbortSignal;
  }
  const controller = new AbortController();
  const setTimeoutFn =
    typeof window !== "undefined" ? window.setTimeout.bind(window) : globalThis.setTimeout.bind(globalThis);
  const clearTimeoutFn =
    typeof window !== "undefined" ? window.clearTimeout.bind(window) : globalThis.clearTimeout.bind(globalThis);
  const id = setTimeoutFn(() => controller.abort(), timeoutMs) as ReturnType<typeof setTimeout>;
  const signal = controller.signal;
  signal.addEventListener("abort", () => clearTimeoutFn(id), { once: true });
  return signal;
}

function mergeSignals(
  userSignal: AbortSignal | undefined,
  timeoutSignal: AbortSignal
): AbortSignal {
  if (!userSignal) return timeoutSignal;

  if (typeof AbortController === "undefined") {
    return timeoutSignal;
  }

  const controller = new AbortController();
  const abort = () => controller.abort();

  userSignal.addEventListener("abort", abort, { once: true });
  timeoutSignal.addEventListener("abort", abort, { once: true });

  return controller.signal;
}

function normalizeApiError(error: ApiError | undefined, status: number): ApiError {
  if (
    error &&
    typeof error.code === "string" &&
    typeof error.message === "string"
  ) {
    return error;
  }

  return {
    code: "HTTP_ERROR",
    details: {},
    message: `Erro HTTP ${status}.`
  };
}

function isSourceMode(value: unknown): value is SourceMode {
  return (
    typeof value === "string" &&
    (SOURCE_MODE_VALUES as readonly string[]).includes(value)
  );
}

function normalizeApiSuccess<T>(
  payload: ApiResponse<T> | { data: T } | unknown
): ApiSuccessResponse<T> {
  const raw = payload as Partial<ApiSuccessResponse<T>> & { data?: T };
  const message = raw.message;

  return {
    success: true,
    data: raw.data as T,
    error: null,
    request_id:
      typeof raw.request_id === "string" ? raw.request_id : "frontend-local",
    source_mode: isSourceMode(raw.source_mode) ? raw.source_mode : "real",
    timestamp:
      typeof raw.timestamp === "string"
        ? raw.timestamp
        : new Date().toISOString(),
    ...(typeof message === "string" ? { message } : {})
  };
}

export class ApiClientError extends Error {
  readonly code: string;
  readonly details?: Record<string, unknown>;
  readonly status: number;

  constructor(error: ApiError | undefined, status: number) {
    const normalizedError = normalizeApiError(error, status);

    super(normalizedError.message);
    this.name = "ApiClientError";
    this.code = normalizedError.code;
    this.details = normalizedError.details;
    this.status = status;
  }
}

export class ApiNetworkError extends Error {
  constructor(message = "API indisponivel.") {
    super(message);
    this.name = "ApiNetworkError";
  }
}

function buildUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${resolveApiBaseUrl()}${normalizedPath}`;
}

function shouldSetJsonContentType(body: BodyInit | null | undefined): boolean {
  return Boolean(body) && !(body instanceof FormData);
}

export async function apiRequest<T>(
  path: string,
  options: ApiClientOptions = {}
): Promise<ApiSuccessResponse<T>> {
  const { token, timeoutMs, signal: userSignal, headers, ...requestOptions } = options;
  const requestHeaders = new Headers(headers);
  const bearerToken = token ?? getStoredToken();

  if (
    !requestHeaders.has("Content-Type") &&
    shouldSetJsonContentType(requestOptions.body)
  ) {
    requestHeaders.set("Content-Type", "application/json");
  }
  if (bearerToken) {
    requestHeaders.set("Authorization", `Bearer ${bearerToken}`);
  }

  const effectiveTimeoutMs =
    typeof timeoutMs === "number" && timeoutMs > 0 ? timeoutMs : DEFAULT_API_TIMEOUT_MS;
  const timeoutSignal = createTimeoutSignal(effectiveTimeoutMs);
  const signal = mergeSignals(userSignal ?? undefined, timeoutSignal);

  let response: Response;
  try {
    response = await fetch(buildUrl(path), {
      ...requestOptions,
      headers: requestHeaders,
      signal
    });
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") {
      throw new ApiNetworkError("A API não respondeu dentro do tempo limite.");
    }
    throw new ApiNetworkError();
  } finally {
    timeoutSignal.dispatchEvent(new Event("abort"));
  }

  let payload: ApiResponse<T> | { data: T };
  try {
    payload = (await response.json()) as ApiResponse<T> | { data: T };
  } catch {
    throw new ApiClientError(
      {
        code: "INVALID_RESPONSE",
        message: "Resposta inválida da API.",
        details: {}
      },
      response.status
    );
  }

  const hasSuccessField = typeof (payload as ApiResponse<T>).success === "boolean";
  const rawData = (payload as { data?: T }).data;

  if (!response.ok || (hasSuccessField && !(payload as ApiResponse<T>).success)) {
    const error = hasSuccessField
      ? (payload as ApiErrorResponse).error
      : {
          code: "HTTP_ERROR",
          message: `Erro HTTP ${response.status}.`,
          details: {}
        };

    throw new ApiClientError(error, response.status);
  }

  if (!hasSuccessField && rawData !== undefined) {
    return normalizeApiSuccess({
      success: true,
      data: rawData,
      error: null,
      request_id: "frontend-local",
      source_mode: "real",
      timestamp: new Date().toISOString()
    });
  }

  return normalizeApiSuccess(payload);
}

export const apiClient = {
  get: <T>(path: string, options?: ApiClientOptions) =>
    apiRequest<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body: unknown, options?: ApiClientOptions) =>
    apiRequest<T>(path, {
      ...options,
      method: "POST",
      body: JSON.stringify(body)
    }),
  patch: <T>(path: string, body: unknown, options?: ApiClientOptions) =>
    apiRequest<T>(path, {
      ...options,
      method: "PATCH",
      body: JSON.stringify(body)
    }),
  put: <T>(path: string, body: unknown, options?: ApiClientOptions) =>
    apiRequest<T>(path, {
      ...options,
      method: "PUT",
      body: JSON.stringify(body)
    }),
  delete: <T>(path: string, options?: ApiClientOptions) =>
    apiRequest<T>(path, {
      ...options,
      method: "DELETE"
    }),
  postForm: <T>(path: string, body: FormData, options?: ApiClientOptions) =>
    apiRequest<T>(path, {
      ...options,
      method: "POST",
      body
    })
};
