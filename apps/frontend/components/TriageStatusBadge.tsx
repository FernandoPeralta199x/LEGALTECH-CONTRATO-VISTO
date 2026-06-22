import { cn } from "@/lib/cn";

type TriageStatus =
  | "not_started"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "skipped"
  | "provider_not_configured"
  | string;

type Cfg = {
  label: string;
  dot: string;
  tone: string;
};

const map: Record<string, Cfg> = {
  /* Aguardando */
  not_started: {
    label: "Aguardando triagem",
    dot: "bg-slate-400",
    tone: "cv-badge-muted",
  },
  skipped: {
    label: "Não aplicável",
    dot: "bg-slate-400",
    tone: "cv-badge-muted",
  },
  provider_not_configured: {
    label: "Provider não configurado",
    dot: "bg-slate-400",
    tone: "cv-badge-muted",
  },
  /* Consultando */
  queued: {
    label: "Na fila",
    dot: "bg-amber-400 animate-pulse",
    tone: "cv-badge-orange",
  },
  running: {
    label: "Consultando",
    dot: "bg-amber-400 animate-ping",
    tone: "cv-badge-orange",
  },
  /* Dados recebidos */
  completed: {
    label: "Dados recebidos",
    dot: "bg-emerald-500",
    tone: "cv-badge-teal",
  },
  /* Erro */
  failed: {
    label: "Erro na consulta",
    dot: "bg-red-500",
    tone: "border-red-500/25 bg-red-500/10 text-red-300",
  },
};

type TriageStatusBadgeProps = {
  status: TriageStatus;
  className?: string;
};

export function TriageStatusBadge({ status, className }: TriageStatusBadgeProps) {
  const cfg = map[status] ?? {
    label: status,
    dot: "bg-slate-400",
    tone: "cv-badge-muted",
  };

  return (
    <span className={cn("cv-badge", cfg.tone, className)}>
      <span className={cn("h-1.5 w-1.5 shrink-0 rounded-full", cfg.dot)} />
      {cfg.label}
    </span>
  );
}
