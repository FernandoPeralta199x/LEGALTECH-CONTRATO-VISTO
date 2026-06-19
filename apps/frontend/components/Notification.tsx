import {
  AlertTriangle,
  CheckCircle2,
  Info,
  X
} from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

type NotificationTone = "error" | "info" | "success" | "warning";

type NotificationProps = {
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  compact?: boolean;
  onDismiss?: () => void;
  title?: string;
  tone?: NotificationTone;
};

const toneConfig: Record<NotificationTone, { className: string; icon: typeof Info }> = {
  error: {
    className: "border-red-500/25 bg-red-50 text-red-900 dark:bg-red-500/10 dark:text-red-200",
    icon: AlertTriangle
  },
  info: {
    className: "border-blue-500/25 bg-blue-50 text-blue-900 dark:bg-blue-500/10 dark:text-blue-200",
    icon: Info
  },
  success: {
    className: "border-emerald-500/25 bg-emerald-50 text-emerald-900 dark:bg-emerald-500/10 dark:text-emerald-200",
    icon: CheckCircle2
  },
  warning: {
    className: "border-amber-500/25 bg-amber-50 text-amber-900 dark:bg-amber-500/10 dark:text-amber-200",
    icon: AlertTriangle
  }
};

export function Notification({
  actions,
  children,
  className,
  compact = false,
  onDismiss,
  title,
  tone = "info"
}: NotificationProps) {
  const config = toneConfig[tone];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "mb-4 rounded-lg border shadow-sm",
        compact ? "px-3 py-2" : "px-4 py-3",
        config.className,
        className
      )}
      role={tone === "error" ? "alert" : "status"}
    >
      <div className="flex items-start gap-3">
        <Icon aria-hidden="true" className="mt-0.5 shrink-0" size={compact ? 14 : 16} />
        <div className="min-w-0 flex-1">
          {title && <p className="text-xs font-semibold">{title}</p>}
          <div className={cn("text-xs leading-5", title && "mt-0.5")}>{children}</div>
          {actions && <div className="mt-3 flex flex-wrap gap-2">{actions}</div>}
        </div>
        {onDismiss && (
          <button
            aria-label="Fechar aviso"
            className="rounded-lg p-1 opacity-70 transition hover:bg-black/5 hover:opacity-100 dark:hover:bg-white/10"
            onClick={onDismiss}
            type="button"
          >
            <X aria-hidden="true" size={14} />
          </button>
        )}
      </div>
    </div>
  );
}
