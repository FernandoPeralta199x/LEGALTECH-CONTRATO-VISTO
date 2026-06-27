"use client";

import { useEffect, useSyncExternalStore } from "react";

import {
  AUTH_SESSION_CHANGED_EVENT,
  AUTH_STORAGE_KEY,
  clearStoredSession,
  readStoredSessionValue,
  type StoredSessionInvalidReason
} from "./authStorage";
import type { DevSession } from "../types/auth";
import { isProduction } from "./runtimeEnv";

export type DevSessionStatus =
  | "authenticated"
  | "invalid"
  | "loading"
  | "unauthenticated";

export type DevSessionState = {
  invalidReason: StoredSessionInvalidReason | null;
  session: DevSession | null;
  status: DevSessionStatus;
};

const hydrationListeners = new Set<() => void>();
let hydrationReady = false;

function notifyHydrationReady(): void {
  hydrationReady = true;
  for (const listener of hydrationListeners) {
    listener();
  }
}

function subscribeHydration(listener: () => void): () => void {
  hydrationListeners.add(listener);
  if (!hydrationReady) {
    queueMicrotask(() => {
      if (!hydrationReady) {
        notifyHydrationReady();
      }
    });
  }

  return () => {
    hydrationListeners.delete(listener);
  };
}

function getHydrationSnapshot(): boolean {
  return hydrationReady;
}

function getServerHydrationSnapshot(): boolean {
  return false;
}

function subscribe(listener: () => void): () => void {
  window.addEventListener(AUTH_SESSION_CHANGED_EVENT, listener);
  window.addEventListener("storage", listener);

  return () => {
    window.removeEventListener(AUTH_SESSION_CHANGED_EVENT, listener);
    window.removeEventListener("storage", listener);
  };
}

function getSnapshot(): string {
  if (isProduction()) {
    throw new Error(
      "[useDevSession] localStorage session is not allowed in production. Use Cognito/httpOnly cookies."
    );
  }
  return window.localStorage.getItem(AUTH_STORAGE_KEY) ?? "";
}

function getServerSnapshot(): string {
  return "";
}

export function useDevSession(): DevSession | null {
  return useDevSessionState().session;
}

export function useDevSessionState(): DevSessionState {
  const snapshot = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const hydrated = useSyncExternalStore(
    subscribeHydration,
    getHydrationSnapshot,
    getServerHydrationSnapshot
  );
  const { invalidReason, session } = readStoredSessionValue(snapshot || null);

  useEffect(() => {
    if (hydrated && invalidReason) {
      clearStoredSession();
    }
  }, [hydrated, invalidReason]);

  if (!hydrated) {
    return {
      invalidReason: null,
      session,
      status: "loading"
    };
  }

  if (session) {
    return {
      invalidReason: null,
      session,
      status: "authenticated"
    };
  }

  return {
    invalidReason,
    session: null,
    status: invalidReason ? "invalid" : "unauthenticated"
  };
}
