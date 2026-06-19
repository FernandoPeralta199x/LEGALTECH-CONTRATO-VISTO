export type ThemePreference = "light" | "dark";

export type NotificationChannelPreference = {
  email: boolean;
  whatsapp: boolean;
};

export type NotificationPreferenceKey =
  | "new_case_created"
  | "analysis_completed"
  | "review_pending"
  | "report_approved"
  | "agent_failed";

export type NotificationPreferences = Record<
  NotificationPreferenceKey,
  NotificationChannelPreference
>;

export const DEFAULT_THEME: ThemePreference = "dark";
export const THEME_STORAGE_KEY = "legaltech.theme.preference.v1";
export const NOTIFICATION_STORAGE_KEY = "legaltech.notification.preferences.v1";

export const DEFAULT_NOTIFICATION_CHANNELS: NotificationChannelPreference = {
  email: true,
  whatsapp: false
};

export const DEFAULT_NOTIFICATION_PREFERENCES: NotificationPreferences = {
  agent_failed: DEFAULT_NOTIFICATION_CHANNELS,
  analysis_completed: DEFAULT_NOTIFICATION_CHANNELS,
  new_case_created: DEFAULT_NOTIFICATION_CHANNELS,
  report_approved: DEFAULT_NOTIFICATION_CHANNELS,
  review_pending: DEFAULT_NOTIFICATION_CHANNELS
};

function getBrowserStorage(): Storage | null {
  if (typeof globalThis === "undefined" || !("localStorage" in globalThis)) {
    return null;
  }

  return globalThis.localStorage;
}

function isThemePreference(value: string | null): value is ThemePreference {
  return value === "light" || value === "dark";
}

function cloneDefaultNotifications(): NotificationPreferences {
  return {
    agent_failed: { ...DEFAULT_NOTIFICATION_CHANNELS },
    analysis_completed: { ...DEFAULT_NOTIFICATION_CHANNELS },
    new_case_created: { ...DEFAULT_NOTIFICATION_CHANNELS },
    report_approved: { ...DEFAULT_NOTIFICATION_CHANNELS },
    review_pending: { ...DEFAULT_NOTIFICATION_CHANNELS }
  };
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function normalizeChannelPreference(
  value: unknown
): NotificationChannelPreference | null {
  if (!isObject(value)) {
    return null;
  }

  if (typeof value.email !== "boolean" || typeof value.whatsapp !== "boolean") {
    return null;
  }

  return {
    email: value.email,
    whatsapp: value.whatsapp
  };
}

export function getStoredThemePreference(): ThemePreference {
  const storage = getBrowserStorage();
  const storedTheme = storage?.getItem(THEME_STORAGE_KEY) ?? null;

  if (isThemePreference(storedTheme)) {
    return storedTheme;
  }

  if (
    typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-color-scheme: dark)").matches
  ) {
    return "dark";
  }

  return DEFAULT_THEME;
}

export function saveThemePreference(theme: ThemePreference): void {
  getBrowserStorage()?.setItem(THEME_STORAGE_KEY, theme);
}

export function applyThemePreference(theme: ThemePreference): void {
  if (typeof document === "undefined") {
    return;
  }

  document.documentElement.classList.toggle("dark", theme === "dark");
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
}

export function getStoredNotificationPreferences(): NotificationPreferences {
  const storage = getBrowserStorage();
  const defaults = cloneDefaultNotifications();
  const rawValue = storage?.getItem(NOTIFICATION_STORAGE_KEY);

  if (!rawValue) {
    return defaults;
  }

  try {
    const parsed = JSON.parse(rawValue) as unknown;
    if (!isObject(parsed)) {
      return defaults;
    }

    return (Object.keys(defaults) as NotificationPreferenceKey[]).reduce(
      (acc, key) => {
        acc[key] = normalizeChannelPreference(parsed[key]) ?? defaults[key];
        return acc;
      },
      {} as NotificationPreferences
    );
  } catch {
    return defaults;
  }
}

export function saveNotificationPreferences(
  preferences: NotificationPreferences
): void {
  getBrowserStorage()?.setItem(
    NOTIFICATION_STORAGE_KEY,
    JSON.stringify(preferences)
  );
}
