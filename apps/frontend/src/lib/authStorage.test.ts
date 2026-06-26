import assert from "node:assert/strict";
import test from "node:test";

import {
  AUTH_SESSION_CHANGED_EVENT,
  AUTH_STORAGE_KEY,
  clearStoredSession,
  getStoredSession,
  readStoredSession,
  readStoredSessionValue,
  saveStoredSession
} from "./authStorage";
import type { DevSession } from "../types/auth";

class MemoryStorage {
  private values = new Map<string, string>();
  removeCalls = 0;

  clear() {
    this.values.clear();
    this.removeCalls = 0;
  }

  getItem(key: string) {
    return this.values.get(key) ?? null;
  }

  removeItem(key: string) {
    this.removeCalls += 1;
    this.values.delete(key);
  }

  setItem(key: string, value: string) {
    this.values.set(key, value);
  }
}

const storage = new MemoryStorage();
let sessionChangedEvents = 0;

Object.defineProperty(globalThis, "localStorage", {
  configurable: true,
  value: storage
});

Object.defineProperty(globalThis, "window", {
  configurable: true,
  value: {
    dispatchEvent(event: Event) {
      if (event.type === AUTH_SESSION_CHANGED_EVENT) {
        sessionChangedEvents += 1;
      }

      return true;
    }
  }
});

function resetStorage() {
  storage.clear();
  sessionChangedEvents = 0;
}

function makeSession(overrides: Partial<DevSession> = {}): DevSession {
  return {
    email: "dev.admin@example.test",
    issuedAt: "2026-05-24T12:00:00.000Z",
    organizationId: "11111111-1111-4111-8111-111111111111",
    role: "admin",
    source: "pasted",
    token: "header.payload.signature",
    userId: "22222222-2222-4222-8222-222222222222",
    ...overrides
  };
}

test("authStorage saves, reads and clears a dev session", () => {
  resetStorage();
  const session = makeSession();

  saveStoredSession(session);

  assert.deepEqual(getStoredSession(), session);
  assert.equal(sessionChangedEvents, 1);

  clearStoredSession();

  assert.equal(getStoredSession(), null);
  assert.equal(storage.removeCalls, 3);
  assert.equal(sessionChangedEvents, 2);
});

test("authStorage reads malformed payloads without clearing or notifying during read", () => {
  resetStorage();
  storage.setItem(AUTH_STORAGE_KEY, "{invalid-json");

  assert.equal(getStoredSession(), null);
  assert.deepEqual(readStoredSession(), {
    invalidReason: "invalid_json",
    session: null
  });
  assert.equal(storage.getItem(AUTH_STORAGE_KEY), "{invalid-json");
  assert.equal(storage.removeCalls, 0);
  assert.equal(sessionChangedEvents, 0);
});

test("authStorage reads invalid session shapes without clearing or notifying during read", () => {
  resetStorage();
  storage.setItem(
    AUTH_STORAGE_KEY,
    JSON.stringify({
      ...makeSession(),
      source: "local-placeholder"
    })
  );

  assert.equal(getStoredSession(), null);
  assert.deepEqual(readStoredSession(), {
    invalidReason: "invalid_shape",
    session: null
  });
  assert.equal(storage.removeCalls, 0);
  assert.equal(sessionChangedEvents, 0);
});

test("authStorage reads malformed stored tokens as invalid shape without clearing during read", () => {
  resetStorage();
  storage.setItem(
    AUTH_STORAGE_KEY,
    JSON.stringify({
      ...makeSession(),
      token: "invalid-token"
    })
  );

  assert.equal(getStoredSession(), null);
  assert.deepEqual(readStoredSession(), {
    invalidReason: "invalid_shape",
    session: null
  });
  assert.equal(storage.removeCalls, 0);
  assert.equal(sessionChangedEvents, 0);
});

test("authStorage reads expired sessions without clearing or notifying during read", () => {
  resetStorage();
  const expiredSession = makeSession({
    expiresAt: new Date(Date.now() - 60_000).toISOString()
  });
  storage.setItem(AUTH_STORAGE_KEY, JSON.stringify(expiredSession));

  assert.equal(getStoredSession(), null);
  assert.deepEqual(readStoredSession(), {
    invalidReason: "expired",
    session: null
  });
  assert.equal(storage.removeCalls, 0);
  assert.equal(sessionChangedEvents, 0);
});

test("authStorage readStoredSessionValue is a pure parser", () => {
  resetStorage();
  const session = makeSession();

  assert.deepEqual(readStoredSessionValue(JSON.stringify(session)), {
    invalidReason: null,
    session
  });
  assert.deepEqual(readStoredSessionValue("{invalid-json"), {
    invalidReason: "invalid_json",
    session: null
  });
  assert.equal(storage.removeCalls, 0);
  assert.equal(sessionChangedEvents, 0);
});
