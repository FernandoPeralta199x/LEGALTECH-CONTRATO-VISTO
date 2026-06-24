import assert from "node:assert/strict";
import test from "node:test";

import { isMockFallbackEnabled } from "./fallback";

// LGPD-01 / FRONT-03: PII e sessao so podem ir para localStorage no fallback
// mock de desenvolvimento. Em producao o fallback e desligado.
// process.env.NODE_ENV e read-only no tipo; usamos um cast mutavel para o teste.
const env = process.env as Record<string, string | undefined>;

test("LGPD/FRONT-03: mock fallback e desligado em producao (sem PII em localStorage)", () => {
  const prevEnv = env.NODE_ENV;
  const prevFlag = env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK;
  try {
    env.NODE_ENV = "production";
    env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK = "true";
    assert.equal(isMockFallbackEnabled(), false);
  } finally {
    env.NODE_ENV = prevEnv;
    env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK = prevFlag;
  }
});

test("FRONT-03: mock fallback exige opt-in explicito em desenvolvimento", () => {
  const prevEnv = env.NODE_ENV;
  const prevFlag = env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK;
  try {
    env.NODE_ENV = "development";
    env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK = "false";
    assert.equal(isMockFallbackEnabled(), false);
    env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK = "true";
    assert.equal(isMockFallbackEnabled(), true);
  } finally {
    env.NODE_ENV = prevEnv;
    env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK = prevFlag;
  }
});
