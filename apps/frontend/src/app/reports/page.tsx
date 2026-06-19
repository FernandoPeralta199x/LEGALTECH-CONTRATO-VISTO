"use client";

import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  Download,
  FileText,
  Lock,
  RefreshCw,
  Scale
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AppLayout } from "@/components/AppLayout";
import { AuthGuard } from "@/components/AuthGuard";
import { Button } from "@/components/Button";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { Notification } from "@/components/Notification";
import { PageTitle } from "@/components/PageTitle";
import { StatusBadge } from "@/components/StatusBadge";
import { formatDate } from "@/lib/formatters";
import { errorMessage } from "@/src/lib/errorMessage";
import {
  listOperationalReports,
  type OperationalReportListItem
} from "@/src/services/reports";

const statusIcon: Record<string, ReactNode> = {
  failed: <AlertTriangle className="text-red-700" size={16} />,
  generating: <Clock className="text-[var(--text2)]" size={16} />,
  not_started: <Clock className="text-[var(--text2)]" size={16} />,
  ready: <CheckCircle2 className="text-[var(--teal)]" size={16} />
};

const statusMeta: Record<
  string,
  { delivery: string; exportLabel: string; exportTitle: string }
> = {
  failed: {
    delivery: "Falha mock/local",
    exportLabel: "PDF indisponível",
    exportTitle: "PDF/exportação real ainda não implementados nesta versão."
  },
  generating: {
    delivery: "Geração mock/local",
    exportLabel: "PDF não implementado",
    exportTitle: "PDF real indisponível enquanto o relatório está em geração mock/local."
  },
  not_started: {
    delivery: "Não iniciado",
    exportLabel: "PDF não implementado",
    exportTitle: "PDF/exportação real ainda não implementados nesta versão."
  },
  ready: {
    delivery: "Relatório mock pronto",
    exportLabel: "PDF roadmap",
    exportTitle: "PDF real ainda não existe nesta versão."
  }
};

function sourceLabel(value: unknown): string {
  return typeof value === "string" && value ? value : "api";
}

function metadataText(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

export default function ReportsPage() {
  const [error, setError] = useState("");
  const [fallbackReason, setFallbackReason] = useState("");
  const [loading, setLoading] = useState(true);
  const [reports, setReports] = useState<OperationalReportListItem[]>([]);

  const refreshReports = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const result = await listOperationalReports();
      setReports(result.data);
      setFallbackReason(result.source === "mock" ? result.fallbackReason ?? "" : "");
    } catch (err) {
      setReports([]);
      setFallbackReason("");
      setError(errorMessage(err, "Não foi possível carregar relatórios operacionais."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refreshReports();
    }, 0);

    return () => window.clearTimeout(timer);
  }, [refreshReports]);

  const metrics = useMemo(() => {
    const ready = reports.filter((item) => item.report.status === "ready").length;
    const generating = reports.filter((item) => item.report.status === "generating").length;
    const failed = reports.filter((item) => item.report.status === "failed").length;
    return { failed, generating, ready };
  }, [reports]);

  return (
    <AuthGuard>
      <AppLayout>
        <PageTitle
          actions={
            <Button
              icon={<RefreshCw aria-hidden="true" size={15} />}
              loading={loading}
              onClick={() => void refreshReports()}
              variant="secondary"
            >
              Atualizar
            </Button>
          }
          description="Área de entrega e revisão do MVP local. São listados apenas relatórios mock-operacionais gerados por case_id; relatórios demonstrativos fixos não aparecem aqui."
          eyebrow="Relatórios"
          title="Entrega e revisão"
        />

        {fallbackReason && (
          <Notification title="Fallback local ativo" tone="warning">
            API local indisponível: a lista abaixo usa apenas dados locais explícitos deste navegador.
          </Notification>
        )}

        <div className="mb-6 grid gap-3 sm:grid-cols-4">
          {[
            {
              label: "Relatórios operacionais",
              value: reports.length,
              tone: "border-[rgba(32,201,151,0.22)] bg-[var(--teal-dim)] text-[var(--teal)]"
            },
            {
              label: "Prontos",
              value: metrics.ready,
              tone: "border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
            },
            {
              label: "Gerando",
              value: metrics.generating,
              tone: "border-amber-500/25 bg-amber-500/10 text-amber-700 dark:text-amber-300"
            },
            {
              label: "Falhas",
              value: metrics.failed,
              tone: "border-red-500/25 bg-red-500/10 text-red-700 dark:text-red-300"
            }
          ].map((metric) => (
            <div className={`rounded-lg border p-4 ${metric.tone}`} key={metric.label}>
              <p className="text-xs font-medium">{metric.label}</p>
              <p className="mt-2 text-2xl font-bold">{metric.value}</p>
            </div>
          ))}
        </div>

        <div className="mb-6 flex items-start gap-3 rounded-lg border border-amber-500/25 bg-amber-500/10 px-5 py-4">
          <Lock className="shrink-0 text-amber-700" size={18} />
          <p className="text-xs leading-5 text-[var(--text2)]">
            <span className="font-semibold text-amber-700 dark:text-amber-300">
              MVP local/mock:
            </span>{" "}
            IA real, revisão persistida e exportação PDF real ainda não estão
            implementadas. Gere o relatório dentro do detalhe do caso para que
            ele apareça nesta lista operacional.
          </p>
        </div>

        {loading ? (
          <LoadingState
            description="Consultando casos e aggregates para localizar relatórios por case_id."
            label="Carregando relatórios"
          />
        ) : error ? (
          <ErrorState
            action={
              <Button
                icon={<RefreshCw size={15} />}
                onClick={() => void refreshReports()}
                variant="secondary"
              >
                Tentar novamente
              </Button>
            }
            description="A listagem de relatórios não pôde ser carregada. Erros da API não são substituídos por relatórios demonstrativos."
            details={error}
          />
        ) : reports.length === 0 ? (
          <EmptyState
            action={
              <Button href="/cases" variant="secondary">
                Ver casos
              </Button>
            }
            description="Nenhum relatório operacional foi gerado por case_id. Casos criados pelo Wizard aparecem em Casos; relatórios aparecem aqui somente depois da geração mock/local."
            icon={<FileText size={20} />}
            secondaryAction={<Button href="/cases/new">Novo Pedido</Button>}
            title="Nenhum relatório operacional"
          />
        ) : (
          <div className="space-y-4">
            {reports.map(({ caseData, report, sourceMode }) => {
              const meta = statusMeta[report.status] ?? statusMeta.not_started;

              return (
                <div className="cv-card p-5" key={report.id}>
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div className="flex min-w-0 items-start gap-4">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-[var(--bd)] bg-[var(--surf2)]">
                        {statusIcon[report.status] ?? <FileText size={18} />}
                      </div>
                      <div className="min-w-0">
                        <div className="mb-1 flex flex-wrap items-center gap-2">
                          <span className="text-[11px] font-semibold text-[var(--teal)]">
                            {caseData.code}
                          </span>
                          <span className="text-[11px] text-[var(--text3)]">
                            v{report.version}
                          </span>
                          <StatusBadge status={report.status} />
                          <span className="cv-badge cv-badge-muted">
                            {meta.delivery}
                          </span>
                          <span className="cv-badge cv-badge-muted">
                            origem {sourceLabel(sourceMode)}
                          </span>
                        </div>
                        <h2 className="text-sm font-semibold text-[var(--text)]">
                          {report.title}
                        </h2>
                        <p className="mt-1 line-clamp-2 text-xs leading-5 text-[var(--text2)]">
                          {report.summary}
                        </p>
                      </div>
                    </div>

                    <div className="flex shrink-0 flex-wrap items-center gap-2">
                      <Link
                        className="cv-btn cv-btn-secondary min-h-11 px-3 text-xs font-semibold"
                        href={`/cases/${report.caseId}`}
                      >
                        Ver caso
                        <ArrowRight size={13} />
                      </Link>
                      <button
                        className="cv-btn cv-btn-secondary min-h-11 cursor-not-allowed px-3 text-xs font-semibold opacity-60"
                        disabled
                        title={meta.exportTitle}
                        type="button"
                      >
                        <Download size={13} />
                        {meta.exportLabel}
                      </button>
                    </div>
                  </div>

                  <div className="mt-4 grid gap-3 border-t border-[var(--bd)] pt-4 text-xs sm:grid-cols-3">
                    <div>
                      <p className="text-[var(--text3)]">Caso</p>
                      <p className="mt-0.5 truncate font-medium text-[var(--text2)]">
                        {caseData.title ?? metadataText(caseData.metadata?.title, caseData.code)}
                      </p>
                    </div>
                    <div>
                      <p className="text-[var(--text3)]">Recomendação</p>
                      <p className="mt-0.5 font-medium text-[var(--text2)]">
                        {report.recommendation ?? "Revisão humana"}
                      </p>
                    </div>
                    <div>
                      <p className="text-[var(--text3)]">Geração</p>
                      <p className="mt-0.5 font-medium text-[var(--text2)]">
                        {formatDate(report.generatedAt)}
                      </p>
                    </div>
                  </div>

                  {report.risks.length > 0 && (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {report.risks.map((risk) => (
                        <span
                          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-semibold ${
                            risk.level === "high"
                              ? "border border-red-500/25 bg-red-500/10 text-red-700 dark:text-red-300"
                              : risk.level === "medium"
                                ? "border border-amber-500/25 bg-amber-500/10 text-amber-700 dark:text-amber-300"
                                : "border border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
                          }`}
                          key={risk.id}
                        >
                          <Scale size={11} />
                          {risk.title}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </AppLayout>
    </AuthGuard>
  );
}
