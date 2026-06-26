import type { CaseStatus, ClientStatus, DocumentStatus, RiskLevel } from "@/types";

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL"
  }).format(value);
}

export function formatCents(cents: number): string {
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(cents / 100);
}

export function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  }).format(new Date(value));
}

export function formatRiskLabel(value: RiskLevel): string {
  const labels: Record<RiskLevel, string> = {
    critical: "Critico",
    high: "Alto",
    low: "Baixo",
    medium: "Moderado",
    unknown: "Nao informado"
  };

  return labels[value];
}

export function formatStatusLabel(
  value: CaseStatus | ClientStatus | DocumentStatus
): string {
  const labels: Record<string, string> = {
    active: "Ativo",
    completed: "Concluido",
    draft: "Rascunho",
    failed: "Falhou",
    inactive: "Inativo",
    pending_upload: "Aguardando upload",
    processed: "Processado",
    processing: "Em processamento",
    review: "Em revisao",
    submitted: "Enviado",
    uploaded: "Enviado"
  };

  return labels[value] ?? value;
}

function formatSizeUnit(value: number, unit: string): string {
  const rounded = Math.round(value * 10) / 10;
  const text = Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1);
  return `${text} ${unit}`;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return formatSizeUnit(bytes / 1024, "KB");
  return formatSizeUnit(bytes / (1024 * 1024), "MB");
}

const caseTypeLabel: Record<string, string> = {
  compra_venda: "Compra e Venda",
  confidencialidade: "Confidencialidade (NDA)",
  contract_analysis: "Análise Contratual",
  due_diligence: "Due Diligence",
  locacao: "Locação",
  outro: "Outro",
  parceria: "Parceria",
  prestacao_servicos: "Prestação de Serviços"
};

export function caseDisplayTitle(legalCase: { title?: string | null; metadata?: { title?: unknown }; caseType: string }): string {
  if (legalCase.title?.trim()) {
    return legalCase.title.trim();
  }

  const title = legalCase.metadata?.title;
  return typeof title === "string" && title.trim()
    ? title.trim()
    : caseTypeLabel[legalCase.caseType] ?? legalCase.caseType;
}
