import assert from "node:assert/strict";
import test from "node:test";

import * as authService from "./auth";
import type { DevSession } from "../types/auth";

function makeJwt(payload: Record<string, unknown>): string {
  const encode = (value: Record<string, unknown>) =>
    Buffer.from(JSON.stringify(value)).toString("base64url");

  return `${encode({ alg: "HS256", typ: "JWT" })}.${encode(payload)}.signature`;
}

test("buildDevSession rejects tokens that do not carry dev auth claims", () => {
  assert.throws(
    () =>
      authService.buildDevSession({
        role: "admin",
        token: makeJwt({
          email: "dev.local@example.test",
          exp: Math.floor(Date.now() / 1000) + 60,
          iat: Math.floor(Date.now() / 1000),
          sub: "22222222-2222-4222-8222-222222222222"
        })
      }),
    /JWT dev invalido/
  );
});

test("validateDevTokenWithBackend validates the pasted token through /api/v1/me", async () => {
  const validate = (
    authService as typeof authService & {
      validateDevTokenWithBackend?: (token: string) => Promise<DevSession>;
    }
  ).validateDevTokenWithBackend;

  assert.equal(typeof validate, "function");

  const token = makeJwt({
    aud: "legaltech-local-api",
    email: "dev.local@example.test",
    exp: Math.floor(Date.now() / 1000) + 60,
    iat: Math.floor(Date.now() / 1000),
    iss: "legaltech-local-dev",
    sub: "22222222-2222-4222-8222-222222222222",
    token_use: "dev",
    "custom:organization_id": "11111111-1111-4111-8111-111111111111",
    "custom:role": "admin"
  });

  let capturedAuthorization = "";
  let capturedUrl = "";
  globalThis.fetch = (async (url, init) => {
    capturedUrl = String(url);
    capturedAuthorization = new Headers(init?.headers).get("Authorization") ?? "";

    return Response.json({
      success: true,
      data: {
        id: "22222222-2222-4222-8222-222222222222",
        email: "dev.local@example.test",
        organization_id: "11111111-1111-4111-8111-111111111111",
        role: "admin"
      }
    });
  }) as typeof fetch;

  const session = await validate!(token);

  assert.equal(capturedUrl, "http://127.0.0.1:8000/api/v1/me");
  assert.equal(capturedAuthorization, `Bearer ${token}`);
  assert.equal(session.token, token);
  assert.equal(session.role, "admin");
  assert.equal(session.organizationId, "11111111-1111-4111-8111-111111111111");
  assert.equal(session.source, "pasted");
});
