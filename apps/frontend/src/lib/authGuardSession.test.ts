import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

const frontendRoot = process.cwd();

function readFrontendFile(pathFromFrontendRoot: string): string {
  return readFileSync(join(frontendRoot, pathFromFrontendRoot), "utf8");
}

test("useDevSessionState exposes an explicit loading hydration state", () => {
  const source = readFrontendFile("src/lib/useDevSession.ts");

  assert.match(source, /\|\s*"loading"/);
  assert.match(source, /let hydrationReady = false/);
  assert.match(source, /queueMicrotask/);
  assert.match(source, /const hydrated = useSyncExternalStore\(/);
  assert.match(source, /if \(!hydrated\) \{[\s\S]*status:\s*"loading"/);
});

test("useDevSessionState only clears invalid sessions after hydration", () => {
  const source = readFrontendFile("src/lib/useDevSession.ts");

  assert.match(source, /if \(hydrated && invalidReason\) \{[\s\S]*clearStoredSession\(\)/);
  assert.doesNotMatch(source, /return getStoredSession\(\)/);
});

test("AuthGuard waits for loading before redirecting or rendering restricted state", () => {
  const source = readFrontendFile("components/AuthGuard.tsx");
  const loadingIndex = source.indexOf('status === "loading"');
  const redirectIndex = source.indexOf("router.replace");
  const effectIndex = source.indexOf("useEffect(");

  assert.ok(source.includes("useDevSessionState"));
  assert.ok(loadingIndex >= 0);
  assert.ok(effectIndex >= 0);
  assert.ok(redirectIndex > effectIndex);
  assert.ok(loadingIndex > redirectIndex);
  assert.doesNotMatch(source.slice(loadingIndex), /clearStoredSession|notifySessionChanged/);
});
