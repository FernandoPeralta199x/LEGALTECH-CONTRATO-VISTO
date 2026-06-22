import { cn } from "@/lib/cn";

type Cfg = {
  label: string;
  dot:   string;
  tone:  string;
};

const triageMap: Record<string, Cfg> = {
  /* ── Aguardando (cinza) ─────────────────────────────────────────── */
  not_started:             { label: "Aguardando triagem",      dot: "bg-slate-400",              tone: "cv-badge-muted" },
  skipped:                 { label: "Não aplicável",           dot: "bg-slate-400",              tone: "cv-badge-muted" },
  provider_not_configured: { label: "Provider não configurado", dot: "bg-slate-400",             tone: "cv-badge-muted" },
  /* ── Consultando (amarelo) ──────────────────────────────────────── */
  queued:                  { label: "Na fila",                 dot: "bg-amber-400 animate-pulse", tone: "cv-badge-orange" },
  running:                 { label: "Consultando",             dot: "bg-amber-400 animate-ping",  tone: "cv-badge-orange" },
  /* ── Dados recebidos (verde) ────────────────────────────────────── */
  completed:               { label: "Dados recebidos",         dot: "bg-emerald-500",            tone: "cv-badge-teal" },
  /* ── Erro (vermelho) ────────────────────────────────────────────── */
  failed:                  { label: "Erro na consulta",        dot: "bg-red-500",                tone: "border-red-500/25 bg-red-500/10 text-red-300" },
};

const otherMap: Record<string, Cfg> = {
  /* ── Case ──────────────────────────────────────────────────────── */
  draft:                    { label: "Rascunho",                dot: "bg-slate-500",              tone: "cv-badge-muted" },
  submitted:                { label: "Registrado localmente",   dot: "bg-blue-500",               tone: "cv-badge-blue" },
  triagem_pendente:         { label: "Triagem",                 dot: "bg-amber-500",              tone: "cv-badge-orange" },
  coleta_pendente:          { label: "Coleta",                  dot: "bg-orange-500",             tone: "cv-badge-orange" },
  processamento_documental: { label: "Preparação local",        dot: "bg-purple-500 animate-ping", tone: "cv-badge-blue" },
  analise_contratual:       { label: "Triagem local",           dot: "bg-violet-500 animate-ping", tone: "cv-badge-blue" },
  compliance:               { label: "Compliance",              dot: "bg-cyan-500",               tone: "cv-badge-blue" },
  minuta_relatorio:         { label: "Minuta",                  dot: "bg-indigo-500",             tone: "cv-badge-blue" },
  revisao_humana:           { label: "Revisão planejada",       dot: "bg-yellow-500 animate-pulse", tone: "cv-badge-orange" },
  processing:               { label: "Preparação local",        dot: "bg-purple-500 animate-ping", tone: "cv-badge-blue" },
  review:                   { label: "Revisão",                 dot: "bg-yellow-500 animate-pulse", tone: "cv-badge-orange" },
  approved:                 { label: "Validação local",         dot: "bg-teal-500",               tone: "cv-badge-teal" },
  delivered:                { label: "Entrega demonstrativa",   dot: "bg-emerald-500",            tone: "cv-badge-teal" },
  cancelled:                { label: "Cancelado",               dot: "bg-slate-600",              tone: "cv-badge-muted" },
  /* ── Document ───────────────────────────────────────────────────── */
  pending_upload:           { label: "Aguardando",              dot: "bg-slate-500",              tone: "cv-badge-muted" },
  uploaded:                 { label: "Anexo local",             dot: "bg-blue-500",               tone: "cv-badge-blue" },
  processed:                { label: "Preparado no MVP",        dot: "bg-teal-500",               tone: "cv-badge-teal" },
  validated:                { label: "Validação local",         dot: "bg-emerald-500",            tone: "cv-badge-teal" },
  /* ── Report ─────────────────────────────────────────────────────── */
  in_review:                { label: "Em revisão",              dot: "bg-yellow-500 animate-pulse", tone: "cv-badge-orange" },
  /* ── Client / generic ───────────────────────────────────────────── */
  active:                   { label: "Ativo no MVP",            dot: "bg-emerald-500",            tone: "cv-badge-teal" },
  inactive:                 { label: "Inativo",                 dot: "bg-slate-600",              tone: "cv-badge-muted" },
  /* ── Risk ───────────────────────────────────────────────────────── */
  low:                      { label: "Risco baixo",             dot: "bg-green-500",              tone: "cv-badge-teal" },
  medium:                   { label: "Risco médio",             dot: "bg-amber-500",              tone: "cv-badge-orange" },
  high:                     { label: "Risco alto",              dot: "bg-red-500",                tone: "border-red-500/25 bg-red-500/10 text-red-300" }
};

const map: Record<string, Cfg> = { ...otherMap, ...triageMap };

type StatusBadgeProps = {
  status:    string;
  className?: string;
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const cfg = map[status] ?? {
    label: status,
    dot:   "bg-slate-500",
    tone:  "cv-badge-muted"
  };

  return (
    <span className={cn("cv-badge", cfg.tone, className)}>
      <span className={cn("h-1.5 w-1.5 shrink-0 rounded-full", cfg.dot)} />
      {cfg.label}
    </span>
  );
}
