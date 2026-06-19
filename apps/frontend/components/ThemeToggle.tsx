"use client";

import { Moon, Sun } from "lucide-react";

import { cn } from "@/lib/cn";
import {
  applyThemePreference,
  getStoredThemePreference,
  saveThemePreference
} from "@/src/lib/preferences";

type ThemeToggleProps = {
  className?: string;
};

export function ThemeToggle({ className }: ThemeToggleProps) {
  function toggleTheme() {
    const currentTheme = getStoredThemePreference();
    const nextTheme = currentTheme === "dark" ? "light" : "dark";
    saveThemePreference(nextTheme);
    applyThemePreference(nextTheme);
  }

  return (
    <button
      aria-label="Alternar tema"
      className={cn(
        "flex h-11 w-11 items-center justify-center rounded-lg border border-[var(--bd2)] bg-[var(--surf2)] text-[var(--text2)]",
        "transition hover:border-[var(--bd3)] hover:bg-[var(--surf3)] hover:text-[var(--teal)]",
        "focus-visible:outline-[var(--teal)]",
        className
      )}
      onClick={toggleTheme}
      type="button"
    >
      <Sun aria-hidden="true" className="cv-theme-icon-sun" size={17} />
      <Moon aria-hidden="true" className="cv-theme-icon-moon" size={17} />
    </button>
  );
}
