import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

type EmptyStateProps = {
  action?: ReactNode;
  className?: string;
  description: string;
  icon?: ReactNode;
  secondaryAction?: ReactNode;
  title: string;
  variant?: "compact" | "panel";
};

export function EmptyState({
  action,
  className,
  description,
  icon,
  secondaryAction,
  title,
  variant = "panel"
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border border-dashed border-[var(--bd2)] bg-[var(--surf2)] text-center",
        variant === "compact" ? "min-h-32 p-5" : "min-h-48 p-8",
        className
      )}
    >
      {icon && (
        <span className="mb-3 flex h-11 w-11 items-center justify-center rounded-lg border border-[var(--bd)] bg-[var(--surf)] text-[var(--teal)] shadow-sm">
          {icon}
        </span>
      )}
      <h2 className="text-sm font-semibold text-[var(--text)]">{title}</h2>
      <p className="mt-2 max-w-md text-xs leading-5 text-[var(--text2)]">{description}</p>
      {(action || secondaryAction) && (
        <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
          {action}
          {secondaryAction}
        </div>
      )}
    </div>
  );
}
