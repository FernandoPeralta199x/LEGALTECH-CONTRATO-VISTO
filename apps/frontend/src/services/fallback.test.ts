import assert from "node:assert/strict";
import test from "node:test";

import { isMockFallbackEnabled } from "./fallback";

// LGPD-01 / FRONT-03: PII e sessao so podem ir para localStorage no fallback
// mock de desenvolvimento. Em producao o fallback e desligado, garantindo que
// nenhuma PII/token seja persistida no browser.

test("LGPD/FRONT-03: mock fallback e desligado em producao (sem PII em localStorage)", () => {
  const prevEnv = process.env.NODE_ENV;
  const prevFlag = process.env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK;
  try {
    process.env.NODE_ENV = "production";
    process.env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK = "true";
    assert.equal(isMockFallbackEnabled(), false);
  } finally {
    process.env.NODE_ENV = prevEnv;
    process.env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK = prevFlag;
  }
});

test("FRONT-03: mock fallback exige opt-in explicito em desenvolvimento", () => {
  const prevEnv = process.env.NODE_ENV;
  const prevFlag = process.env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK;
  try {
    process.env.NODE_ENV = "development";
    process.env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK = "false";
    assert.equal(isMockFallbackEnabled(), false);
    process.env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK = "true";
    assert.equal(isMockFallbackEnabled(), true);
  } finally {
    process.env.NODE_ENV = prevEnv;
    process.env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK = prevFlag;
  }
});
