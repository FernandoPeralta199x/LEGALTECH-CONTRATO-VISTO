import { Clock, Wallet } from "lucide-react";

import { formatCurrency } from "@/lib/formatters";

type EstimateCardProps = {
  valorCents: number;
  prazoHoras: number;
  loading?: boolean;
  error?: string | null;
};

function formatPrazo(hours: number): string {
  if (hours < 24) return `${hours}h úteis`;
  const dias = Math.round(hours / 24);
  return `${dias} ${dias === 1 ? "dia" : "dias"} úteis`;
}

export function EstimateCard({ valorCents, prazoHoras, loading, error }: EstimateCardProps) {
  return (
    <div className="rounded-2xl border border-[rgba(32,201,151,0.22)] bg-[var(--teal-dim)] px-5 py-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--surf)] text-[var(--teal)]">
            <Wallet size={16} />
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text2)]">
              Valor referencial simulado
            </p>
            <p className={"text-base font-bold text-[var(--text)]" + (loading ? " animate-pulse" : "")}>
              {loading ? "Calculando..." : formatCurrency(valorCents / 100)}
              {error && (
                <span className="ml-2 text-[10px] font-normal text-red-300">
                  (estimativa local)
                </span>
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--surf)] text-[var(--teal)]">
            <Clock size={16} />
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text2)]">
              Prazo referencial simulado
            </p>
            <p className="text-base font-bold text-[var(--text)]">
              {formatPrazo(prazoHoras)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
