import { Clock, Wallet } from "lucide-react";

type EstimateCardProps = {
  valorCents: number;
  prazoHoras: number;
};

function formatBRL(cents: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL"
  }).format(cents / 100);
}

function formatPrazo(hours: number): string {
  if (hours < 24) return `${hours}h úteis`;
  const dias = Math.round(hours / 24);
  return `${dias} ${dias === 1 ? "dia" : "dias"} úteis`;
}

export function EstimateCard({ valorCents, prazoHoras }: EstimateCardProps) {
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
            <p className="text-base font-bold text-[var(--text)]">
              {formatBRL(valorCents)}
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
