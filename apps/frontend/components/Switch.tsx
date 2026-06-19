"use client";

import { cn } from "@/lib/cn";

type SwitchProps = {
  checked: boolean;
  onCheckedChange: (value: boolean) => void;
  disabled?: boolean;
  label?: string;
  className?: string;
  id?: string;
};

export function Switch({
  checked,
  onCheckedChange,
  disabled,
  label,
  className,
  id
}: SwitchProps) {
  return (
    <button
      aria-checked={checked}
      aria-label={label}
      className={cn(
        "relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full",
        "transition-colors duration-[150ms] ease-smooth",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--teal)]",
        checked
          ? "bg-[var(--teal-d)] shadow-[0_0_0_3px_rgba(32,201,151,0.16)]"
          : "bg-[var(--surf3)]",
        disabled && "cursor-not-allowed opacity-50",
        className
      )}
      disabled={disabled}
      id={id}
      onClick={() => !disabled && onCheckedChange(!checked)}
      role="switch"
      type="button"
    >
      <span
        aria-hidden="true"
        className={cn(
          "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow",
          "transition duration-[180ms] ease-spring",
          checked ? "translate-x-5" : "translate-x-0.5"
        )}
      />
    </button>
  );
}
