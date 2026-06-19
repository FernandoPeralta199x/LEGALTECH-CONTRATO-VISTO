import { LoaderCircle } from "lucide-react";

import { cn } from "@/lib/cn";

type LoadingStateProps = {
  description?: string;
  label?: string;
  rows?: number;
  variant?: "panel" | "inline";
};

export function LoadingState({
  description,
  label = "Carregando...",
  rows = 3,
  variant = "panel"
}: LoadingStateProps) {
  if (variant === "inline") {
    return (
      <div className="inline-flex items-center gap-2 text-xs text-[var(--text2)]">
        <LoaderCircle aria-hidden="true" className="animate-spin text-[var(--teal)]" size={14} />
        {label}
      </div>
    );
  }

  return (
    <div className="cv-card p-5">
      <div className="flex items-center gap-3">
        <span className="flex h-11 w-11 items-center justify-center rounded-lg border border-[rgba(32,201,151,0.22)] bg-[var(--teal-dim)] text-[var(--teal)]">
          <LoaderCircle aria-hidden="true" className="animate-spin" size={18} />
        </span>
        <div>
          <p className="text-sm font-semibold text-[var(--text)]">{label}</p>
          {description && (
            <p className="mt-0.5 text-xs leading-5 text-[var(--text2)]">{description}</p>
          )}
        </div>
      </div>
      <div className="mt-5 space-y-3" aria-hidden="true">
        {Array.from({ length: rows }).map((_, index) => (
          <div className="flex items-center gap-3" key={index}>
            <div className="h-9 w-9 rounded-lg bg-[var(--surf3)]" />
            <div className="flex-1 space-y-2">
              <div className={cn("h-2.5 rounded-full bg-[var(--surf3)]", index === 0 ? "w-2/3" : "w-1/2")} />
              <div className="h-2 w-4/5 rounded-full bg-[var(--surf2)]" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
