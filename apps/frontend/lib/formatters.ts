import type { CaseStatus, ClientStatus, DocumentStatus, RiskLevel } from "@/types";

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL"
  }).format(value);
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
