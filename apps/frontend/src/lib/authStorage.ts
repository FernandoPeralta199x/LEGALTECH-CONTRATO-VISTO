import type { DevSession } from "../types/auth";
import { DEV_ROLES } from "../types/auth";
import { LOCAL_CASES_STORAGE_KEY } from "./localCases";
import { LOCAL_CLIENTS_STORAGE_KEY } from "./localClients";

export const AUTH_STORAGE_KEY = "legaltech.dev.session.v1";
export const AUTH_SESSION_CHANGED_EVENT = "legaltech-dev-session-changed";

export type StoredSessionInvalidReason =
  | "expired"
  | "invalid_json"
  | "invalid_shape";

export type StoredSessionRead = {
  invalidReason: StoredSessionInvalidReason | null;
  session: DevSession | null;
};

function getBrowserStorage(): Storage | null {
  if (typeof globalThis === "undefined" || !("localStorage" in globalThis)) {
    return null;
  }

  return globalThis.localStorage;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isJwtLike(value: unknown): value is string {
  if (typeof value !== "string") {
    return false;
  }

  const parts = value.split(".");
  return parts.length === 3 && parts.every((part) => part.length > 0);
}

function isDevSession(value: unknown): value is DevSession {
  if (!isObject(value)) {
    return false;
  }

  return (
    typeof value.email === "string" &&
    typeof value.issuedAt === "string" &&
    typeof value.organizationId === "string" &&
    typeof value.role === "string" &&
    DEV_ROLES.includes(value.role as DevSession["role"]) &&
    value.source === "pasted" &&
    isJwtLike(value.token) &&
    typeof value.userId === "string"
  );
}

function notifySessionChanged(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.dispatchEvent(new Event(AUTH_SESSION_CHANGED_EVENT));
}

export function saveStoredSession(session: DevSession): void {
  const storage = getBrowserStorage();
  if (!storage) {
    return;
  }

  storage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
  notifySessionChanged();
}

export function readStoredSessionValue(rawValue: string | null): StoredSessionRead {
  if (!rawValue) {
    return { invalidReason: null, session: null };
  }

  try {
    const parsed = JSON.parse(rawValue) as unknown;
    if (!isDevSession(parsed)) {
      return { invalidReason: "invalid_shape", session: null };
    }

    if (parsed.expiresAt && new Date(parsed.expiresAt).getTime() <= Date.now()) {
      return { invalidReason: "expired", session: null };
    }

    return { invalidReason: null, session: parsed };
  } catch {
    return { invalidReason: "invalid_json", session: null };
  }
}

export function readStoredSession(): StoredSessionRead {
  const storage = getBrowserStorage();
  if (!storage) {
    return { invalidReason: null, session: null };
  }

  return readStoredSessionValue(storage.getItem(AUTH_STORAGE_KEY));
}

export function getStoredSession(): DevSession | null {
  return readStoredSession().session;
}

export function getStoredToken(): string | null {
  return readStoredSession().session?.token ?? null;
}

export function clearStoredSession(): void {
  const storage = getBrowserStorage();
  if (!storage) {
    return;
  }

  const hadStoredSession = storage.getItem(AUTH_STORAGE_KEY) !== null;
  storage.removeItem(AUTH_STORAGE_KEY);
  storage.removeItem(LOCAL_CASES_STORAGE_KEY);
  storage.removeItem(LOCAL_CLIENTS_STORAGE_KEY);
  if (hadStoredSession) {
    notifySessionChanged();
  }
}
