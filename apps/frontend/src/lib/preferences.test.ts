import assert from "node:assert/strict";
import test from "node:test";

import {
  DEFAULT_NOTIFICATION_CHANNELS,
  DEFAULT_THEME,
  getStoredNotificationPreferences,
  getStoredThemePreference,
  saveNotificationPreferences,
  saveThemePreference
} from "./preferences";

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

test("theme preference defaults to dark-first and persists valid choices", () => {
  storage.clear();

  assert.equal(DEFAULT_THEME, "dark");
  assert.equal(getStoredThemePreference(), "dark");

  saveThemePreference("light");

  assert.equal(getStoredThemePreference(), "light");
});

test("notification preferences persist channels and ignore malformed storage", () => {
  storage.clear();

  const preferences = getStoredNotificationPreferences();
  assert.deepEqual(preferences.new_case_created, DEFAULT_NOTIFICATION_CHANNELS);

  saveNotificationPreferences({
    ...preferences,
    agent_failed: { email: true, whatsapp: false }
  });

  assert.equal(getStoredNotificationPreferences().agent_failed.whatsapp, false);

  storage.setItem("legaltech.notification.preferences.v1", "{bad-json");

  assert.deepEqual(
    getStoredNotificationPreferences().analysis_completed,
    DEFAULT_NOTIFICATION_CHANNELS
  );
});
