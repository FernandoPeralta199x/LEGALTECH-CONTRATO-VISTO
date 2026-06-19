import {
  clearStoredSession,
  getStoredSession,
  saveStoredSession
} from "../lib/authStorage";
import type { DecodedDevJwt, DevLoginInput, DevRole, DevSession } from "../types/auth";
import { DEV_ROLES } from "../types/auth";
import { apiClient } from "./apiClient";

type BackendCurrentUser = {
  email: string;
  id: string;
  organization_id: string;
  role: string;
};

function base64UrlDecode(input: string): string {
  const normalized = input.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
  const binary = atob(padded);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));

  return new TextDecoder().decode(bytes);
}

export function isDevRole(value: string): value is DevRole {
  return DEV_ROLES.includes(value as DevRole);
}

export function decodeDevJwt(token: string): DecodedDevJwt | null {
  const parts = token.trim().split(".");
  if (parts.length !== 3 || !parts[1]) {
    return null;
  }

  try {
    return JSON.parse(base64UrlDecode(parts[1])) as DecodedDevJwt;
  } catch {
    return null;
  }
}

function requireDevJwtClaims(token: string): DecodedDevJwt {
  const decodedToken = decodeDevJwt(token);
  const role = decodedToken?.["custom:role"] ?? decodedToken?.role;
  const organizationId =
    decodedToken?.["custom:organization_id"] ?? decodedToken?.organization_id;

  if (
    !decodedToken ||
    decodedToken.token_use !== "dev" ||
    !decodedToken.sub ||
    !organizationId ||
    !role ||
    !isDevRole(role)
  ) {
    throw new Error("JWT dev invalido. Gere um token dev valido no backend.");
  }

  if (
    typeof decodedToken.exp === "number" &&
    decodedToken.exp <= Math.floor(Date.now() / 1000)
  ) {
    throw new Error("JWT dev expirado. Gere um novo token no backend.");
  }

  return decodedToken;
}

function requireDevRole(value: string): DevRole {
  if (!isDevRole(value)) {
    throw new Error("JWT dev invalido. Papel retornado pelo backend nao e permitido.");
  }

  return value;
}

export function buildDevSession(
  input: DevLoginInput,
  verifiedUser?: BackendCurrentUser
): DevSession {
  const providedToken = input.token?.trim();
  if (!providedToken) {
    throw new Error("JWT dev é obrigatório para criar sessão local.");
  }

  const token = providedToken;
  const decodedToken = requireDevJwtClaims(token);
  const decodedRole = decodedToken?.["custom:role"] ?? decodedToken?.role;
  const role = verifiedUser
    ? requireDevRole(verifiedUser.role)
    : decodedRole && isDevRole(decodedRole)
      ? decodedRole
      : input.role;
  const issuedAt = decodedToken?.iat
    ? new Date(decodedToken.iat * 1000).toISOString()
    : new Date().toISOString();
  const expiresAt = decodedToken?.exp
    ? new Date(decodedToken.exp * 1000).toISOString()
    : undefined;

  return {
    email: verifiedUser?.email ?? decodedToken.email ?? `dev.${role}@example.test`,
    expiresAt,
    issuedAt,
    organizationId:
      verifiedUser?.organization_id ??
      decodedToken["custom:organization_id"] ??
      decodedToken.organization_id ??
      "",
    role,
    source: "pasted",
    token,
    userId: verifiedUser?.id ?? decodedToken.sub ?? ""
  };
}

export async function validateDevTokenWithBackend(token: string): Promise<DevSession> {
  const decodedToken = requireDevJwtClaims(token);
  const response = await apiClient.get<BackendCurrentUser>("/api/v1/me", { token });
  return buildDevSession(
    {
      role:
        decodedToken["custom:role"] && isDevRole(decodedToken["custom:role"])
          ? decodedToken["custom:role"]
          : "client",
      token
    },
    response.data
  );
}

export async function saveDevSession(input: DevLoginInput): Promise<DevSession> {
  const session = await validateDevTokenWithBackend(input.token ?? "");
  saveStoredSession(session);
  return session;
}

export function getCurrentDevSession(): DevSession | null {
  return getStoredSession();
}

export function logoutDevSession(): void {
  clearStoredSession();
}
