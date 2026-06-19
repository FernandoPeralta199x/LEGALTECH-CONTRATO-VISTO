import { AlertCircle, CheckCircle2, Clock, Loader2, Play, SkipForward } from "lucide-react";

import type { AgentExecution } from "@/types";
import { cn } from "@/lib/cn";

function formatDuration(ms: number | null): string {
  if (!ms) return "—";
  if (ms < 60000) return `${(ms / 1000).toFixed(0)}s`;
  return `${(ms / 60000).toFixed(1)}min`;
}

const agentTypeLabel: Record<string, string> = {
  triagem: "Triagem",
  coleta: "Coleta Externa",
  doc_processor: "Processador Documental",
  contrato_analyzer: "Análise Contratual",
  compliance: "Compliance",
  report_writer: "Gerador de Relatório"
};

type AgentCardProps = {
  execution: AgentExecution;
};

export function AgentCard({ execution }: AgentCardProps) {
  const statusIcon = {
    queued: <Clock className="text-[var(--text3)]" size={16} />,
    running: <Loader2 className="animate-spin text-[var(--teal)]" size={16} />,
    completed: <CheckCircle2 className="text-[var(--teal)]" size={16} />,
    failed: <AlertCircle className="text-red-600" size={16} />,
    skipped: <SkipForward className="text-[var(--text3)]" size={16} />
  };

  const statusClass: Record<string, string> = {
    queued: "border-[var(--bd)] bg-[var(--surf2)]",
    running: "border-[rgba(32,201,151,0.25)] bg-[var(--teal-dim)] shadow-glow-teal",
    completed: "border-[rgba(32,201,151,0.2)] bg-[var(--teal-dim)]",
    failed: "border-red-500/25 bg-red-500/10",
    skipped: "border-[var(--bd)] bg-[var(--surf2)] opacity-70"
  };

  return (
    <div
      className={cn(
        "rounded-lg border p-4 transition-all",
        statusClass[execution.status]
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div
            className={cn(
              "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border",
              execution.status === "running"
                ? "border-[rgba(32,201,151,0.28)] bg-[var(--teal-dim)]"
                : execution.status === "completed"
                ? "border-[rgba(32,201,151,0.22)] bg-[var(--surf)]"
                : execution.status === "failed"
                ? "border-red-500/25 bg-[var(--surf)]"
                : "border-[var(--bd)] bg-[var(--surf3)]"
            )}
          >
            {statusIcon[execution.status]}
          </div>
          <div>
            <p className="text-xs font-semibold text-[var(--text)]">
              {execution.agentName}
            </p>
            <p className="text-[11px] text-[var(--text2)]">
              {agentTypeLabel[execution.agentType] ?? execution.agentType}
            </p>
          </div>
        </div>
        <span className="text-[11px] text-[var(--text3)]">
          {formatDuration(execution.durationMs)}
        </span>
      </div>

      {execution.outputSummary && (
        <p className="mt-3 text-xs leading-5 text-[var(--text2)]">
          {execution.outputSummary}
        </p>
      )}

      {execution.errorMessage && (
        <p className="mt-2 text-xs text-red-700">{execution.errorMessage}</p>
      )}

      {execution.status === "running" && (
        <div className="mt-3 h-1 overflow-hidden rounded-full bg-[var(--surf3)]">
          <div className="h-1 w-1/2 animate-pulse rounded-full bg-[var(--teal)]" />
        </div>
      )}
    </div>
  );
}
