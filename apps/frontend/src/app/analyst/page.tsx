"use client";

import {
  AlertTriangle,
  ClipboardCheck,
  Clock,
  FileText,
  RefreshCw
} from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AppLayout } from "@/components/AppLayout";
import { AuthGuard } from "@/components/AuthGuard";
import { Button } from "@/components/Button";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { Notification } from "@/components/Notification";
import { PageTitle } from "@/components/PageTitle";
import { PriorityBadge } from "@/components/PriorityBadge";
import { StatusBadge } from "@/components/StatusBadge";
import { formatDate } from "@/lib/formatters";
import { errorMessage } from "@/src/lib/errorMessage";
import { listCases } from "@/src/services/cases";
import type { Case } from "@/types";

const REVIEW_RELEVANT_STATUSES = new Set([
  "awaiting_triage",
  "triage_running",
  "triage_partial",
  "triage_completed",
  "ai_running",
  "report_ready",
  "needs_human_review",
  "failed"
]);

function triageQueueCases(cases: Case[]): Case[] {
  return cases.filter((legalCase) => REVIEW_RELEVANT_STATUSES.has(legalCase.status));
}

function triageStatusLabel(legalCase: Case): string {
  const triageStatus = legalCase.metadata?.triageStatus;
  return typeof triageStatus === "string" ? triageStatus : legalCase.status;
}

function metadataText(value: unknown, fallback: string): string {
  if (typeof value === "string" && value.trim()) {
    return value;
  }
  if (typeof value === "number") {
    return String(value);
  }
  return fallback;
}

export default function AnalystPage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [error, setError] = useState("");
  const [fallbackReason, setFallbackReason] = useState("");
  const [loading, setLoading] = useState(true);

  const refreshCases = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const result = await listCases();
      setCases(result.data);
      setFallbackReason(result.source === "mock" ? result.fallbackReason ?? "" : "");
    } catch (err) {
      setCases([]);
      setFallbackReason("");
      setError(errorMessage(err, "Não foi possível carregar a triagem operacional."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refreshCases();
    }, 0);

    return () => window.clearTimeout(timer);
  }, [refreshCases]);

  const pendingCases = useMemo(() => triageQueueCases(cases), [cases]);
  const reportReadyCount = cases.filter((legalCase) => legalCase.status === "report_ready").length;
  const reviewCount = cases.filter((legalCase) => legalCase.status === "needs_human_review").length;

  return (
    <AuthGuard>
      <AppLayout>
        <PageTitle
          actions={
            <>
              <Link
                className="inline-flex items-center gap-2 rounded-lg bg-brand-teal px-4 py-2.5 text-sm font-semibold text-white shadow-glow-teal transition hover:bg-brand-teal-dark"
                href="/cases/new"
              >
                <FileText size={15} />
                Novo Pedido
              </Link>
              <Button
                icon={<RefreshCw aria-hidden="true" size={15} />}
                loading={loading}
                onClick={() => void refreshCases()}
                variant="secondary"
              >
                Atualizar
              </Button>
            </>
          }
          description="Triagem local e revisão operacional baseadas nos casos criados pelo fluxo Novo Pedido/backend. Esta tela não executa IA/RAG real, aprovação persistida ou parecer jurídico final."
          eyebrow="Analista"
          title="Triagem e revisão operacional"
        />

        {fallbackReason && (
          <Notification title="Fallback local ativo" tone="warning">
            API local indisponível: a fila abaixo usa apenas casos criados no fallback local deste navegador.
          </Notification>
        )}

        <div className="mb-6 flex items-start gap-3 rounded-lg border border-amber-500/25 bg-amber-500/10 px-5 py-4">
          <AlertTriangle className="mt-0.5 shrink-0 text-amber-400" size={18} />
          <p className="text-sm leading-6 text-[var(--text2)]">
            Área operacional do MVP local/mock. Os itens abaixo vêm de{" "}
            <code>GET /api/v1/cases</code> ou do fallback local explícito; casos
            demonstrativos fixos não são exibidos nesta fila.
          </p>
        </div>

        <div className="mb-6 grid gap-4 sm:grid-cols-3">
          {[
            {
              label: "Casos operacionais",
              value: cases.length,
              description: "Casos retornados pelo backend ou fallback local explícito."
            },
            {
              label: "Na fila de triagem",
              value: pendingCases.length,
              description: "Casos com status operacional de triagem, IA ou revisão."
            },
            {
              label: "Revisão/relatório",
              value: reviewCount + reportReadyCount,
              description: "Casos que chegaram a relatório ou revisão humana."
            }
          ].map((metric) => (
            <div
              className="rounded-lg border border-[var(--border)] bg-[var(--surf)] p-5"
              key={metric.label}
            >
              <p className="text-xs text-[var(--text2)]">{metric.label}</p>
              <p className="mt-2 text-3xl font-bold text-[var(--text)]">
                {metric.value}
              </p>
              <p className="mt-2 text-xs leading-5 text-[var(--text2)]">
                {metric.description}
              </p>
            </div>
          ))}
        </div>

        {loading ? (
          <LoadingState
            description="Consultando a fila operacional de casos do MVP local/mock."
            label="Carregando triagem"
          />
        ) : error ? (
          <ErrorState
            action={
              <Button
                icon={<RefreshCw size={15} />}
                onClick={() => void refreshCases()}
                variant="secondary"
              >
                Tentar novamente
              </Button>
            }
            description="A fila de triagem não pôde ser carregada. Erros de autenticação ou permissão não são mascarados por dados demonstrativos."
            details={error}
          />
        ) : pendingCases.length === 0 ? (
          <EmptyState
            action={<Button href="/cases/new">Novo Pedido</Button>}
            icon={<ClipboardCheck size={20} />}
            secondaryAction={<Button href="/cases" variant="secondary">Ver Casos</Button>}
            title="Nenhum caso operacional em triagem"
            description="Crie um pedido pelo Wizard para que o backend gere request, case, timeline e plano de triagem por case_id."
          />
        ) : (
          <div className="space-y-4">
            {pendingCases.map((legalCase) => (
              <div
                className="rounded-lg border border-[var(--border)] bg-[var(--surf)] p-5"
                key={legalCase.id}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="mb-1 flex flex-wrap items-center gap-2">
                      <span className="text-[11px] font-semibold text-brand-teal-dark">
                        {legalCase.code}
                      </span>
                      <StatusBadge status={legalCase.status} />
                      <PriorityBadge priority={legalCase.priority} />
                    </div>
                    <p className="text-sm font-semibold text-[var(--text)]">
                      {legalCase.title ??
                        metadataText(legalCase.metadata?.title, legalCase.caseType)}
                    </p>
                    <p className="text-xs text-[var(--text2)]">
                      {legalCase.clientName} · origem {legalCase.sourceMode ?? "api"}
                    </p>
                    <div className="mt-2 flex items-center gap-1.5 text-[11px] text-[var(--text2)]">
                      <Clock size={11} />
                      Atualizado {formatDate(legalCase.updatedAt)}
                    </div>
                  </div>
                  <Link
                    className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surf2)] px-3 py-2 text-xs font-medium text-[var(--text)] transition hover:border-brand-teal/40"
                    href={`/cases/${legalCase.id}`}
                  >
                    <FileText size={13} />
                    Abrir caso
                  </Link>
                </div>

                <div className="mt-4 grid gap-2 rounded-lg border border-[var(--border)] bg-[var(--surf2)] p-3 sm:grid-cols-4">
                  <div>
                    <p className="text-[11px] text-[var(--text2)]">Partes</p>
                    <p className="mt-1 text-xs font-semibold text-[var(--text)]">
                      {metadataText(
                        legalCase.metadata?.partiesCount,
                        String(legalCase.parties.length)
                      )}
                    </p>
                  </div>
                  <div>
                    <p className="text-[11px] text-[var(--text2)]">Documentos</p>
                    <p className="mt-1 text-xs font-semibold text-[var(--text)]">
                      {legalCase.documentsCount}
                    </p>
                  </div>
                  <div>
                    <p className="text-[11px] text-[var(--text2)]">Triagem</p>
                    <p className="mt-1 text-xs font-semibold text-[var(--text)]">
                      {triageStatusLabel(legalCase)}
                    </p>
                  </div>
                  <div>
                    <p className="text-[11px] text-[var(--text2)]">Progresso</p>
                    <p className="mt-1 text-xs font-semibold text-[var(--text)]">
                      {legalCase.progressPercent}%
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </AppLayout>
    </AuthGuard>
  );
}
