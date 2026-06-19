"use client";

import { useEffect } from "react";
import type { ReactNode } from "react";

import {
  applyThemePreference,
  getStoredThemePreference,
  THEME_STORAGE_KEY
} from "@/src/lib/preferences";

type ThemeProviderProps = {
  children: ReactNode;
};

export function ThemeProvider({ children }: ThemeProviderProps) {
  useEffect(() => {
    applyThemePreference(getStoredThemePreference());

    function handleStorage(event: StorageEvent) {
      if (event.key === THEME_STORAGE_KEY) {
        applyThemePreference(getStoredThemePreference());
      }
    }

    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  return <>{children}</>;
}
