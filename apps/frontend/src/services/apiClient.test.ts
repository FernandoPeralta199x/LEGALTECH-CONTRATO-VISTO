import assert from "node:assert/strict";
import test from "node:test";

import { clearStoredSession, saveStoredSession } from "../lib/authStorage";
import { ApiClientError, apiClient } from "./apiClient";

class MemoryStorage {
  private values = new Map<string, string>();

  clear() {
    this.values.clear();
  }

  getItem(key: string) {
    return this.values.get(key) ?? null;
  }

  removeItem(key: string) {
    this.values.delete(key);
  }

  setItem(key: string, value: string) {
    this.values.set(key, value);
  }
}

const storage = new MemoryStorage();
Object.defineProperty(globalThis, "localStorage", {
  configurable: true,
  value: storage
});

test("apiClient sends Authorization from the stored dev session", async () => {
  storage.clear();
  saveStoredSession({
    email: "dev.admin@example.test",
    issuedAt: "2026-05-24T12:00:00.000Z",
    organizationId: "11111111-1111-4111-8111-111111111111",
    role: "admin",
    source: "pasted",
    token: "stored.jwt.token",
    userId: "22222222-2222-4222-8222-222222222222"
  });

  let capturedUrl = "";
  let capturedAuthorization = "";

  globalThis.fetch = (async (url, init) => {
    capturedUrl = String(url);
    const headers = new Headers(init?.headers);
    capturedAuthorization = headers.get("Authorization") ?? "";

    return Response.json({ success: true, data: [] });
  }) as typeof fetch;

  await apiClient.get<unknown[]>("/api/v1/clients");

  assert.equal(capturedUrl, "http://127.0.0.1:8000/api/v1/clients");
  assert.equal(capturedAuthorization, "Bearer stored.jwt.token");

  clearStoredSession();
});

test("apiClient derives the API host from the browser host when no env URL is configured", async () => {
  storage.clear();
  const previousLocation = Object.getOwnPropertyDescriptor(globalThis, "location");

  Object.defineProperty(globalThis, "location", {
    configurable: true,
    value: new URL("http://192.168.0.102:3000/dashboard")
  });

  let capturedUrl = "";

  globalThis.fetch = (async (url) => {
    capturedUrl = String(url);

    return Response.json({ success: true, data: [] });
  }) as typeof fetch;

  try {
    await apiClient.get<unknown[]>("/api/v1/cases");

    assert.equal(capturedUrl, "http://192.168.0.102:8000/api/v1/cases");
  } finally {
    if (previousLocation) {
      Object.defineProperty(globalThis, "location", previousLocation);
    } else {
      Reflect.deleteProperty(globalThis, "location");
    }
  }
});

test("apiClient rewrites a loopback env URL when the frontend is opened from a LAN host", async () => {
  storage.clear();
  const previousBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  const previousLocation = Object.getOwnPropertyDescriptor(globalThis, "location");
  process.env.NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000";

  Object.defineProperty(globalThis, "location", {
    configurable: true,
    value: new URL("http://192.168.0.102:3000/cases")
  });

  let capturedUrl = "";

  globalThis.fetch = (async (url) => {
    capturedUrl = String(url);

    return Response.json({ success: true, data: [] });
  }) as typeof fetch;

  try {
    await apiClient.get<unknown[]>("/api/v1/documents");

    assert.equal(capturedUrl, "http://192.168.0.102:8000/api/v1/documents");
  } finally {
    if (previousBaseUrl === undefined) {
      Reflect.deleteProperty(process.env, "NEXT_PUBLIC_API_BASE_URL");
    } else {
      process.env.NEXT_PUBLIC_API_BASE_URL = previousBaseUrl;
    }

    if (previousLocation) {
      Object.defineProperty(globalThis, "location", previousLocation);
    } else {
      Reflect.deleteProperty(globalThis, "location");
    }
  }
});

test("apiClient handles non-standard error envelopes without undefined message access", async () => {
  storage.clear();

  globalThis.fetch = (async () =>
    Response.json({ detail: "Not Found" }, { status: 404 })) as typeof fetch;

  await assert.rejects(
    () => apiClient.get<unknown>("/api/v1/cases/case-local-missing"),
    (error) => {
      assert.equal(error instanceof ApiClientError, true);
      assert.equal((error as ApiClientError).code, "HTTP_ERROR");
      assert.equal((error as ApiClientError).message, "Erro HTTP 404.");
      return true;
    }
  );
});

test("apiClient preserves standard response envelope metadata", async () => {
  storage.clear();

  globalThis.fetch = (async () =>
    Response.json({
      success: true,
      data: { id: "case-1" },
      error: null,
      request_id: "req-standard",
      source_mode: "local",
      timestamp: "2026-06-11T10:00:00.000Z"
    })) as typeof fetch;

  const response = await apiClient.get<{ id: string }>("/api/v1/cases/case-1");

  assert.equal(response.data.id, "case-1");
  assert.equal(response.error, null);
  assert.equal(response.request_id, "req-standard");
  assert.equal(response.source_mode, "local");
});
