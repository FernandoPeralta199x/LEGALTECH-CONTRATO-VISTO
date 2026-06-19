"use client";

import {
  AlertTriangle,
  ArrowLeft,
  Bot,
  Calendar,
  CheckCircle2,
  ClipboardList,
  Clock,
  Download,
  FileText,
  Mail,
  Pencil,
  Phone,
  Plus,
  Shield,
  Upload,
  Users
} from "lucide-react";
import type { FormEvent } from "react";
import Link from "next/link";
import { use, useCallback, useEffect, useState } from "react";

import { AppLayout } from "@/components/AppLayout";
import { AuthGuard } from "@/components/AuthGuard";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { FormField, SelectInput, TextArea, TextInput } from "@/components/FormField";
import { LoadingState } from "@/components/LoadingState";
import { Notification } from "@/components/Notification";
import { PriorityBadge } from "@/components/PriorityBadge";
import { StatusBadge } from "@/components/StatusBadge";
import { Timeline } from "@/components/Timeline";
import { formatBytes, caseDisplayTitle, formatDate } from "@/lib/formatters";
import { errorMessage } from "@/src/lib/errorMessage";
import {
  createCaseParty,
  updateCaseParty
} from "@/src/services/caseParties";
import { getCaseAggregate } from "@/src/services/cases";
import {
  FINAL_REPORT_ACCEPT_ATTR,
  FINAL_REPORT_ACCEPTED_MIME,
  getFinalReportDownloadUrl,
  listFinalReports,
  uploadFinalReport,
  type FinalReportDocument
} from "@/src/services/finalReports";
import type {
  Case,
  CaseAggregate,
  CaseParty,
  CasePartyCreate,
  CasePartyUpdate,
  Document,
  ProviderResult,
  Report
} from "@/types";

const TABS = [
  { id: "overview", label: "Visão geral", icon: ClipboardList },
  { id: "parties", label: "Partes", icon: Users },
  { id: "documents", label: "Documentos", icon: FileText },
  { id: "timeline", label: "Timeline", icon: Clock },
  { id: "agents", label: "Triagem local", icon: Bot },
  { id: "report", label: "Relatório", icon: Shield }
];

const caseTypeLabel: Record<string, string> = {
  compra_venda: "Compra e Venda",
  prestacao_servicos: "Prestação de Serviços",
  locacao: "Locação",
  parceria: "Parceria",
  confidencialidade: "Confidencialidade (NDA)",
  due_diligence: "Due Diligence",
  contract_analysis: "Análise Contratual",
  outro: "Outro"
};

const partyTypeOptions = [
  { label: "Cliente", value: "cliente" },
  { label: "Contraparte", value: "contraparte" },
  { label: "Testemunha", value: "testemunha" },
  { label: "Responsável", value: "responsavel" },
  { label: "Outro", value: "outro" }
];

const partyTypeLabel: Record<string, string> = {
  avalista: "Avalista",
  cliente: "Cliente",
  contraparte: "Contraparte",
  contratada: "Contratada",
  contratante: "Contratante",
  fiador: "Fiador",
  outro: "Outro",
  responsavel: "Responsável",
  testemunha: "Testemunha"
};

const emptyPartyForm: CasePartyCreate = {
  document: "",
  email: "",
  name: "",
  notes: "",
  party_type: "cliente",
  phone: ""
};

type PageProps = { params: Promise<{ id: string }> };
type PartyFormErrors = Partial<Record<keyof CasePartyCreate, string>>;

function sourceModeLabel(value: unknown): string {
  if (typeof value !== "string" || !value) {
    return "api";
  }

  const labels: Record<string, string> = {
    hybrid: "híbrido",
    local: "local",
    mock: "mock",
    real: "real",
    simulated: "simulado"
  };

  return labels[value] ?? value;
}

function recommendationLabel(value: unknown): string {
  if (typeof value !== "string" || !value) {
    return "Pendente";
  }

  const labels: Record<string, string> = {
    do_not_proceed: "Não prosseguir",
    human_review_required: "Revisão humana obrigatória",
    proceed: "Prosseguir",
    proceed_with_caution: "Prosseguir com ressalvas"
  };

  return labels[value] ?? value;
}

function reportStatusLabel(report: Report | null): string {
  if (!report) return "Não gerado";

  const labels: Record<string, string> = {
    failed: "Falhou",
    generating: "Gerando",
    not_started: "Não iniciado",
    ready: "Pronto"
  };

  return labels[report.status] ?? report.status;
}

function ProviderResultRow({ result }: { result: ProviderResult }) {
  return (
    <div className="rounded-lg border border-[var(--bd)] bg-[var(--surf2)] p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-xs font-semibold text-[var(--text)]">{result.provider}</p>
          <p className="mt-0.5 text-[11px] text-[var(--text3)]">
            {sourceModeLabel(result.sourceMode)}
            {typeof result.confidence === "number"
              ? ` · confiança ${(result.confidence * 100).toFixed(0)}%`
              : ""}
          </p>
        </div>
        <StatusBadge status={result.status} />
      </div>
      {result.summary && (
        <p className="mt-2 text-xs leading-5 text-[var(--text2)]">
          {result.summary}
        </p>
      )}
      {result.riskSignals.length > 0 && (
        <p className="mt-2 text-[11px] text-[var(--text3)]">
          Sinais: {result.riskSignals.join(", ")}
        </p>
      )}
    </div>
  );
}

function validatePartyForm(form: CasePartyCreate): PartyFormErrors {
  const errors: PartyFormErrors = {};
  const document = form.document?.trim() ?? "";
  const email = form.email?.trim() ?? "";

  if (!form.name.trim()) {
    errors.name = "Informe o nome da parte.";
  }

  if (!form.party_type.trim()) {
    errors.party_type = "Selecione o papel da parte.";
  }

  if (document && !/^[A-Za-z0-9./-]+$/.test(document)) {
    errors.document = "Use apenas números, letras, pontos, barras ou hífens.";
  }

  if (email && !email.includes("@")) {
    errors.email = "Informe um e-mail válido ou deixe o campo vazio.";
  }

  return errors;
}

function buildPartyPayload(form: CasePartyCreate): CasePartyCreate {
  return {
    document: form.document?.trim() || null,
    email: form.email?.trim() || null,
    name: form.name.trim(),
    notes: form.notes?.trim() || null,
    party_type: form.party_type,
    phone: form.phone?.trim() || null
  };
}

function partyFormFromParty(party: CaseParty): CasePartyCreate {
  return {
    document: party.document ?? "",
    email: party.email ?? "",
    name: party.name,
    notes: party.notes ?? "",
    party_type: party.type,
    phone: party.phone ?? ""
  };
}

function aggregatePartyFromCaseParty(
  party: CaseParty,
  fallbackOrganizationId: string
): CaseAggregate["parties"][number] {
  return {
    ...party,
    organizationId: party.organizationId ?? fallbackOrganizationId,
    role: typeof party.metadata?.role === "string" ? party.metadata.role : party.type
  };
}

export default function CaseDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const [activeTab, setActiveTab] = useState("overview");
  const [caseAggregate, setCaseAggregate] = useState<CaseAggregate | null>(null);
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [caseDocuments, setCaseDocuments] = useState<Document[]>([]);
  const [caseParties, setCaseParties] = useState<CaseParty[]>([]);
  const [editingParty, setEditingParty] = useState<CaseParty | null>(null);
  const [error, setError] = useState("");
  const [fallbackReason, setFallbackReason] = useState("");
  const [loading, setLoading] = useState(true);
  const [partyError, setPartyError] = useState("");
  const [partyForm, setPartyForm] = useState<CasePartyCreate>(emptyPartyForm);
  const [partyFormErrors, setPartyFormErrors] = useState<PartyFormErrors>({});
  const [partySubmitting, setPartySubmitting] = useState(false);
  const [partySuccessMessage, setPartySuccessMessage] = useState("");
  const [showPartyForm, setShowPartyForm] = useState(false);
  const [finalReports, setFinalReports] = useState<FinalReportDocument[]>([]);
  const [finalReportUploading, setFinalReportUploading] = useState(false);
  const [finalReportError, setFinalReportError] = useState("");
  const [finalReportSuccess, setFinalReportSuccess] = useState("");

  const refreshFinalReports = useCallback(async () => {
    try {
      const reports = await listFinalReports(id);
      setFinalReports(reports);
    } catch (err) {
      setFinalReportError(errorMessage(err, "Não foi possível carregar relatórios finais."));
      setFinalReports([]);
    }
  }, [id]);

  async function handleFinalReportUpload(event: FormEvent<HTMLInputElement>) {
    const input = event.currentTarget;
    const file = input.files?.[0];
    if (!file) return;

    // Validate MIME / extension
    const ext = file.name.toLowerCase().split(".").pop() ?? "";
    const allowedExt = ["pdf", "docx", "doc", "txt"];
    if (
      !FINAL_REPORT_ACCEPTED_MIME.includes(file.type) &&
      !allowedExt.includes(ext)
    ) {
      setFinalReportError(
        "Tipo de arquivo não suportado. Envie PDF, DOCX ou TXT."
      );
      input.value = "";
      return;
    }

    // Size limit: 25 MB (a generous cap for legal reports)
    const maxBytes = 25 * 1024 * 1024;
    if (file.size > maxBytes) {
      setFinalReportError("Arquivo excede o limite de 25 MB.");
      input.value = "";
      return;
    }

    setFinalReportUploading(true);
    setFinalReportError("");
    setFinalReportSuccess("");
    try {
      const doc = await uploadFinalReport(id, file);
      setFinalReports((current) => [doc, ...current]);
      setFinalReportSuccess(`"${doc.filename}" enviado com sucesso.`);
    } catch (err) {
      setFinalReportError(errorMessage(err, "Falha ao enviar o relatório."));
    } finally {
      setFinalReportUploading(false);
      input.value = "";
    }
  }

  async function handleFinalReportDownload(documentId: string) {
    try {
      const url = await getFinalReportDownloadUrl(documentId);
      window.open(url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setFinalReportError(
        errorMessage(err, "Não foi possível gerar o link de download.")
      );
    }
  }

  const refreshCase = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const aggregateResult = await getCaseAggregate(id);
      setCaseAggregate(aggregateResult.data);
      setCaseData(aggregateResult.data.case);
      setCaseDocuments(aggregateResult.data.documents);
      setCaseParties(aggregateResult.data.parties);
      setFallbackReason(
        aggregateResult.source === "mock" ? aggregateResult.fallbackReason ?? "" : ""
      );
      void refreshFinalReports();
    } catch (err) {
      setError(errorMessage(err));
      setFallbackReason("");
      setCaseAggregate(null);
      setCaseData(null);
      setCaseDocuments([]);
      setCaseParties([]);
    } finally {
      setLoading(false);
    }
  }, [id, refreshFinalReports]);

  function syncCaseParties(updater: (current: CaseParty[]) => CaseParty[]) {
    setCaseParties((current) => {
      const next = updater(current);
      setCaseData((currentCase) =>
        currentCase ? { ...currentCase, parties: next } : currentCase
      );
      setCaseAggregate((currentAggregate) =>
        currentAggregate
          ? {
              ...currentAggregate,
              case: { ...currentAggregate.case, parties: next },
              parties: next.map((party) =>
                aggregatePartyFromCaseParty(
                  party,
                  currentAggregate.case.organizationId ?? ""
                )
              ),
              summary: {
                ...currentAggregate.summary,
                partiesCount: next.length
              }
            }
          : currentAggregate
      );
      return next;
    });
  }

  function resetPartyForm() {
    setEditingParty(null);
    setPartyForm(emptyPartyForm);
    setPartyFormErrors({});
    setPartyError("");
    setShowPartyForm(false);
  }

  function startCreateParty() {
    setEditingParty(null);
    setPartyForm(emptyPartyForm);
    setPartyFormErrors({});
    setPartyError("");
    setPartySuccessMessage("");
    setShowPartyForm(true);
  }

  function startEditParty(party: CaseParty) {
    setEditingParty(party);
    setPartyForm(partyFormFromParty(party));
    setPartyFormErrors({});
    setPartyError("");
    setPartySuccessMessage("");
    setShowPartyForm(true);
  }

  function updatePartyForm<K extends keyof CasePartyCreate>(
    field: K,
    value: CasePartyCreate[K]
  ) {
    setPartyForm((current) => ({ ...current, [field]: value }));
    setPartyFormErrors((current) => ({ ...current, [field]: "" }));
    setPartyError("");
    setPartySuccessMessage("");
  }

  async function handlePartySubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (partySubmitting) {
      return;
    }

    const validationErrors = validatePartyForm(partyForm);
    setPartyFormErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      setPartyError("Revise os campos destacados antes de registrar a parte local.");
      return;
    }

    setPartySubmitting(true);
    setPartyError("");
    setPartySuccessMessage("");

    try {
      const payload = buildPartyPayload(partyForm);
      const result = editingParty
        ? await updateCaseParty(id, editingParty.id, payload as CasePartyUpdate)
        : await createCaseParty(id, payload);

      syncCaseParties((current) =>
        editingParty
          ? current.map((party) =>
              party.id === result.data.id ? result.data : party
            )
          : [result.data, ...current]
      );
      setFallbackReason(result.source === "mock" ? result.fallbackReason ?? "" : "");
      setPartySuccessMessage(
        result.source === "mock"
          ? editingParty
            ? "Registro local de parte atualizado no fallback de desenvolvimento."
            : "Registro local de parte criado no fallback de desenvolvimento."
          : editingParty
            ? "Registro de parte atualizado pela API local."
            : "Registro de parte criado pela API local."
      );
      resetPartyForm();
    } catch (err) {
      setPartyError(errorMessage(err));
    } finally {
      setPartySubmitting(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refreshCase();
    }, 0);

    return () => window.clearTimeout(timer);
  }, [refreshCase]);

  if (loading) {
    return (
      <AuthGuard>
        <AppLayout>
          <LoadingState
            description="Consultando visão local do caso, cliente e documentos indicados."
            label="Carregando caso"
            rows={4}
          />
        </AppLayout>
      </AuthGuard>
    );
  }

  if (!caseData) {
    return (
      <AuthGuard>
        <AppLayout>
          <ErrorState
            action={
              <Button href="/cases" variant="secondary">
                Voltar para casos
              </Button>
            }
            description="Não foi possível carregar o detalhe do caso. Verifique se está logado com permissões adequadas e se a API local está disponível."
            details={error || "Caso não encontrado."}
            title="Caso não encontrado"
          />
        </AppLayout>
      </AuthGuard>
    );
  }

  const caseTimeline = caseAggregate?.timeline ?? [];
  const triageModules = caseAggregate?.triageModules ?? [];
  const providerResults = caseAggregate?.providerResults ?? [];
  const caseReport = caseAggregate?.report ?? null;
  const summary = caseAggregate?.summary;

  return (
    <AuthGuard>
      <AppLayout>
        {fallbackReason && (
          <Notification title="Fallback local do MVP" tone="warning">
            API local indisponível: detalhes carregados por fallback mockado local.
          </Notification>
        )}
        {error && (
          <Notification title="Atenção" tone="error">
            {error}
          </Notification>
        )}
        {partySuccessMessage && (
          <Notification
            onDismiss={() => setPartySuccessMessage("")}
            title="Ação local registrada"
            tone="success"
          >
            {partySuccessMessage}
          </Notification>
        )}
        {partyError && (
          <Notification onDismiss={() => setPartyError("")} title="Atenção" tone="error">
            {partyError}
          </Notification>
        )}

        {/* Breadcrumb */}
        <Link
          className="mb-4 flex items-center gap-1.5 text-xs text-[var(--text2)] transition hover:text-[var(--teal)]"
          href="/cases"
        >
          <ArrowLeft size={14} />
          Todos os casos
        </Link>

        {/* Case header */}
        <div className="cv-card mb-6 p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span className="text-xs font-semibold text-brand-teal">
                  {caseData.code}
                </span>
                <StatusBadge status={caseData.status} />
                <PriorityBadge priority={caseData.priority} />
              </div>
              <h1 className="text-xl font-bold text-[var(--text)]">
                {caseDisplayTitle(caseData)}
              </h1>
              <p className="mt-1 text-sm text-[var(--text2)]">
                {caseData.clientName} · {caseTypeLabel[caseData.caseType] ?? caseData.caseType}
              </p>
              {caseData.notes && (
                <p className="mt-2 text-xs leading-5 text-[var(--text2)]">{caseData.notes}</p>
              )}
            </div>
            <div className="shrink-0 text-left sm:text-right">
              <div className="mb-3 text-left sm:text-right">
                <span className="text-2xl font-bold text-[var(--text)]">
                  {caseData.progressPercent}%
                </span>
                <p className="text-[11px] text-[var(--text2)]">Progresso geral</p>
              </div>
              <div className="h-1.5 w-32 overflow-hidden rounded-full bg-[var(--surf3)]">
                <div
                  className="h-1.5 rounded-full bg-[var(--teal)]"
                  style={{ width: `${caseData.progressPercent}%` }}
                />
              </div>
            </div>
          </div>

          <dl className="mt-6 flex flex-wrap gap-6 border-t border-[var(--bd)] pt-4 text-xs">
            {[
              {
                label: "Responsável",
                value: caseData.assignedTo ?? "Não atribuído"
              },
              { label: "Documentos", value: `${summary?.documentsCount ?? caseData.documentsCount}` },
              { label: "Partes", value: `${summary?.partiesCount ?? caseParties.length}` },
              { label: "Risco", value: summary?.riskLevel ?? caseData.riskLevel ?? "unknown" },
              {
                label: "Recomendação",
                value: recommendationLabel(caseData.recommendation)
              },
              {
                label: "Origem",
                value: sourceModeLabel(summary?.sourceMode ?? caseData.sourceMode)
              },
              {
                label: "Criado em",
                value: formatDate(caseData.createdAt)
              },
              {
                label: "Atualizado",
                value: formatDate(caseData.updatedAt)
              }
            ].map((item) => (
              <div key={item.label}>
                <dt className="text-[var(--text3)]">{item.label}</dt>
                <dd className="mt-0.5 font-medium text-[var(--text2)]">{item.value}</dd>
              </div>
            ))}
          </dl>
        </div>

        {/* Tabs */}
        <div className="mb-6 flex overflow-x-auto border-b border-[var(--bd)]">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                className={`flex items-center gap-2 whitespace-nowrap border-b-2 px-4 py-3 text-xs font-medium transition ${
                  active
                    ? "border-[var(--teal)] text-[var(--teal)]"
                    : "border-transparent text-[var(--text2)] hover:text-[var(--text)]"
                }`}
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                type="button"
              >
                <Icon size={14} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab: Overview */}
        {activeTab === "overview" && (
          <div className="grid gap-6 lg:grid-cols-2 animate-in">
            <Card title="Status atual">
              <div className="flex items-center gap-4">
                <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full border-4 border-[rgba(32,201,151,0.3)] bg-[var(--teal-dim)]">
                  <span className="text-sm font-bold text-[var(--teal)]">
                    {caseData.progressPercent}%
                  </span>
                </div>
                <div>
                  <StatusBadge status={caseData.status} />
                  {caseData.assignedTo && (
                    <p className="mt-1.5 text-xs text-[var(--text2)]">
                      Responsável: {caseData.assignedTo}
                    </p>
                  )}
                </div>
              </div>
            </Card>

            <Card title="Estatísticas">
              <dl className="grid grid-cols-2 gap-4">
                {[
                  { label: "Documentos", value: summary?.documentsCount ?? caseData.documentsCount },
                  { label: "Partes", value: summary?.partiesCount ?? caseParties.length },
                  {
                    label: "Triagem",
                    value: summary?.triageStatus ?? "not_started"
                  },
                  {
                    label: "Relatório",
                    value: reportStatusLabel(caseReport)
                  }
                ].map((stat) => (
                  <div key={stat.label}>
                    <dt className="text-[11px] text-[var(--text3)]">{stat.label}</dt>
                    <dd className="mt-0.5 text-lg font-bold text-[var(--text)]">{stat.value}</dd>
                  </div>
                ))}
              </dl>
            </Card>

            {caseData.status === "revisao_humana" && (
              <div className="lg:col-span-2 rounded-lg border border-[rgba(249,115,22,0.25)] bg-[var(--orange-dim)] p-5">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="shrink-0 text-[var(--orange)]" size={20} />
                  <div>
                      <p className="text-sm font-semibold text-[var(--text)]">
                      Revisão demonstrativa
                    </p>
                    <p className="mt-0.5 text-xs text-[var(--text2)]">
                      Este caso está em etapa demonstrativa de revisão. Revisão
                      humana persistida, aprovação real e entrega ao cliente ficam no
                      roadmap.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab: Parties */}
        {activeTab === "parties" && (
          <div className="animate-in">
            <div className="mb-4 flex justify-end">
              <Button icon={<Plus aria-hidden="true" size={15} />} onClick={startCreateParty}>
                Adicionar parte
              </Button>
            </div>
            {caseParties.length === 0 ? (
              <EmptyState
                action={
                  <Button icon={<Plus size={15} />} onClick={startCreateParty}>
                    Adicionar parte
                  </Button>
                }
                description="Cadastre partes fictícias vinculadas a este caso para validar o fluxo local."
                icon={<Users size={20} />}
                title="Nenhuma parte registrada"
              />
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                {caseParties.map((party) => (
                  <Card key={party.id}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex min-w-0 items-start gap-3">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-[var(--bd)] bg-[var(--surf2)] text-xs font-bold text-[var(--teal)]">
                          {party.name.slice(0, 2).toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-[var(--text)]">
                            {party.name}
                          </p>
                          <span className="inline-flex rounded-md bg-[var(--surf3)] px-2 py-0.5 text-[11px] text-[var(--text2)]">
                            {partyTypeLabel[party.type] ?? party.type}
                          </span>
                        </div>
                      </div>
                      <Button
                        aria-label={`Editar parte ${party.name}`}
                        icon={<Pencil aria-hidden="true" size={14} />}
                        onClick={() => startEditParty(party)}
                        size="sm"
                        variant="secondary"
                      >
                        Editar
                      </Button>
                    </div>
                    <dl className="mt-4 space-y-2 text-xs">
                      <div className="flex min-w-0 items-center gap-2 text-[var(--text2)]">
                        <FileText size={12} className="shrink-0 text-[var(--text3)]" />
                        <span className="truncate">{party.document || "Documento não informado"}</span>
                      </div>
                      <div className="flex min-w-0 items-center gap-2 text-[var(--text2)]">
                        <Mail size={12} className="shrink-0 text-[var(--text3)]" />
                        <span className="truncate">{party.email || "E-mail não informado"}</span>
                      </div>
                      <div className="flex min-w-0 items-center gap-2 text-[var(--text2)]">
                        <Phone size={12} className="shrink-0 text-[var(--text3)]" />
                        <span className="truncate">{party.phone || "Telefone não informado"}</span>
                      </div>
                    </dl>
                    {party.notes && (
                      <p className="mt-3 border-t border-[var(--bd)] pt-3 text-xs leading-5 text-[var(--text2)]">
                        {party.notes}
                      </p>
                    )}
                  </Card>
                ))}
              </div>
            )}
            {showPartyForm && (
              <div
                aria-modal="true"
                className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4 py-8 backdrop-blur-sm"
                role="dialog"
              >
                <form
                  className="cv-card max-h-[calc(100vh-4rem)] w-full max-w-2xl overflow-y-auto p-5 shadow-2xl"
                  onSubmit={handlePartySubmit}
                >
                  <div className="mb-5">
                    <h2 className="text-sm font-semibold text-[var(--text)]">
                      {editingParty ? "Editar parte" : "Adicionar parte"}
                    </h2>
                    <p className="mt-1 text-xs leading-5 text-[var(--text2)]">
                      Use apenas dados fictícios. A referência de organização e caso é validada pela API local quando disponível.
                    </p>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField error={partyFormErrors.name} label="Nome da parte" required>
                      <TextInput
                        invalid={Boolean(partyFormErrors.name)}
                        onChange={(event) => updatePartyForm("name", event.target.value)}
                        placeholder="Parte fictícia"
                        value={partyForm.name}
                      />
                    </FormField>
                    <FormField error={partyFormErrors.party_type} label="Papel" required>
                      <SelectInput
                        invalid={Boolean(partyFormErrors.party_type)}
                        onChange={(event) => updatePartyForm("party_type", event.target.value)}
                        value={partyForm.party_type}
                      >
                        {partyTypeOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </SelectInput>
                    </FormField>
                    <FormField
                      error={partyFormErrors.document}
                      hint="Opcional. Use identificadores fictícios em ambiente local."
                      label="Documento"
                    >
                      <TextInput
                        invalid={Boolean(partyFormErrors.document)}
                        onChange={(event) => updatePartyForm("document", event.target.value)}
                        placeholder="00000000000"
                        value={partyForm.document ?? ""}
                      />
                    </FormField>
                    <FormField error={partyFormErrors.email} label="E-mail">
                      <TextInput
                        invalid={Boolean(partyFormErrors.email)}
                        onChange={(event) => updatePartyForm("email", event.target.value)}
                        placeholder="parte@example.test"
                        type="email"
                        value={partyForm.email ?? ""}
                      />
                    </FormField>
                    <FormField label="Telefone">
                      <TextInput
                        onChange={(event) => updatePartyForm("phone", event.target.value)}
                        placeholder="+5500000000000"
                        value={partyForm.phone ?? ""}
                      />
                    </FormField>
                    <FormField label="Observações">
                      <TextArea
                        onChange={(event) => updatePartyForm("notes", event.target.value)}
                        placeholder="Observações fictícias sobre a parte"
                        value={partyForm.notes ?? ""}
                      />
                    </FormField>
                  </div>
                  <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
                    <Button disabled={partySubmitting} onClick={resetPartyForm} variant="secondary">
                      Cancelar
                    </Button>
                    <Button loading={partySubmitting} type="submit">
                      {editingParty ? "Salvar alterações" : "Adicionar parte"}
                    </Button>
                  </div>
                </form>
              </div>
            )}
          </div>
        )}

        {/* Tab: Documents */}
        {activeTab === "documents" && (
          <div className="animate-in space-y-3">
            {caseDocuments.length === 0 ? (
              <EmptyState
                action={
                  <Button href="/documents" variant="secondary">
                    Abrir documentos
                  </Button>
                }
                description="Nenhum metadado de documento foi encontrado para este caso."
                icon={<FileText size={20} />}
                title="Sem documentos"
              />
            ) : (
              caseDocuments.map((doc) => (
                <div
                  className="flex flex-col gap-3 rounded-lg border border-[var(--bd)] bg-[var(--surf2)] px-5 py-4 sm:flex-row sm:items-center sm:gap-4"
                  key={doc.id}
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--surf3)]">
                    <FileText className="text-[var(--text2)]" size={18} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-[var(--text)]">
                      {doc.filename}
                    </p>
                    <p className="text-xs text-[var(--text3)]">
                      {doc.sizeLabel} · {formatDate(doc.uploadedAt)}
                    </p>
                    <p className="mt-1 text-[11px] text-[var(--text3)]">
                      OCR: {doc.ocrStatus ?? "not_started"} · IA: {doc.aiReadStatus ?? "not_started"}
                    </p>
                  </div>
                  <div className="self-start sm:self-center">
                    <StatusBadge status={doc.status} />
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Tab: Timeline */}
        {activeTab === "timeline" && (
          <div className="animate-in">
            <Card title="Linha do tempo operacional">
              <Timeline events={caseTimeline} />
            </Card>
          </div>
        )}

        {/* Tab: Agents */}
        {activeTab === "agents" && (
          <div className="animate-in">
            <div className="mb-4 flex items-center gap-2">
              <Bot className="text-brand-teal" size={18} />
              <h2 className="text-sm font-semibold text-[var(--text)]">
                Módulos de triagem do caso
              </h2>
            </div>
            {triageModules.length === 0 ? (
              <EmptyState
                description="Nenhum módulo de triagem foi registrado para este caso."
                icon={<Bot size={20} />}
                title="Triagem ainda não iniciada"
              />
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {triageModules.map((module) => (
                  <Card key={module.id}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-[var(--text)]">
                          {module.moduleLabel}
                        </p>
                        <p className="mt-1 text-[11px] text-[var(--text2)]">
                          {module.provider} · {sourceModeLabel(module.sourceMode)}
                        </p>
                      </div>
                      <StatusBadge status={module.status} />
                    </div>
                    <dl className="mt-4 grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <dt className="text-[var(--text3)]">Tentativas</dt>
                        <dd className="font-medium text-[var(--text2)]">{module.attempts}</dd>
                      </div>
                      <div>
                        <dt className="text-[var(--text3)]">Obrigatório</dt>
                        <dd className="font-medium text-[var(--text2)]">
                          {module.required ? "Sim" : "Não"}
                        </dd>
                      </div>
                    </dl>
                    {module.reason && (
                      <p className="mt-3 text-xs leading-5 text-[var(--text2)]">
                        {module.reason}
                      </p>
                    )}
                    {module.summary && (
                      <p className="mt-3 border-t border-[var(--bd)] pt-3 text-xs leading-5 text-[var(--text2)]">
                        {module.summary}
                      </p>
                    )}
                    {module.errorMessage && (
                      <p className="mt-2 text-xs text-red-700">
                        {module.errorMessage}
                      </p>
                    )}
                  </Card>
                ))}
                {providerResults.length > 0 && (
                  <div className="sm:col-span-2">
                    <Card title="Resultados de providers">
                      <div className="space-y-3">
                        {providerResults.map((result) => (
                          <ProviderResultRow result={result} key={result.id} />
                        ))}
                      </div>
                    </Card>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Tab: Report */}
        {activeTab === "report" && (
          <div className="animate-in space-y-6">
            {/* Final report upload + list (always visible) */}
            <Card>
              <div className="flex items-center gap-2 mb-3">
                <Upload size={18} style={{ color: "var(--accent)" }} />
                <h3 className="text-sm font-bold text-[var(--text)]">
                  Relatório final do analista
                </h3>
              </div>
              <p className="text-xs text-[var(--text2)] mb-4">
                Faça upload do relatório jurídico finalizado pelo analista.
                Aceita PDF, DOCX ou TXT (máx. 25 MB). Ficará vinculado ao caso e
                disponível para download posterior.
              </p>

              {finalReportError && (
                <div className="mb-3 flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-400">
                  <AlertTriangle size={14} />
                  {finalReportError}
                </div>
              )}
              {finalReportSuccess && (
                <div className="mb-3 flex items-center gap-2 rounded-lg border border-[rgba(32,201,151,0.3)] bg-[var(--teal-dim)] px-3 py-2 text-xs text-[var(--teal)]">
                  <CheckCircle2 size={14} />
                  {finalReportSuccess}
                </div>
              )}

              <label
                className={`flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-dashed border-[var(--bd2)] bg-[var(--surf2)] px-4 py-6 text-sm font-medium text-[var(--text2)] transition hover:border-[var(--accent)] hover:bg-[var(--surf3)] ${
                  finalReportUploading ? "pointer-events-none opacity-60" : ""
                }`}
              >
                <Upload size={16} />
                {finalReportUploading
                  ? "Enviando..."
                  : "Selecionar arquivo (PDF, DOCX, TXT)"}
                <input
                  accept={FINAL_REPORT_ACCEPT_ATTR}
                  className="hidden"
                  disabled={finalReportUploading}
                  onChange={handleFinalReportUpload}
                  type="file"
                />
              </label>

              {finalReports.length > 0 && (
                <div className="mt-5 space-y-2">
                  <p className="text-[11px] uppercase tracking-wide text-[var(--text3)]">
                    Relatórios enviados ({finalReports.length})
                  </p>
                  {finalReports.map((doc) => (
                    <div
                      className="flex items-center gap-3 rounded-lg border border-[var(--bd)] bg-[var(--surf2)] px-4 py-3"
                      key={doc.id}
                    >
                      <FileText
                        className="shrink-0 text-[var(--text2)]"
                        size={16}
                      />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-[var(--text)]">
                          {doc.filename}
                        </p>
                        <p className="text-[11px] text-[var(--text3)]">
                          {formatBytes(doc.sizeBytes)}
                          {doc.uploadedAt
                            ? ` · ${formatDate(doc.uploadedAt)}`
                            : ""}
                        </p>
                      </div>
                      <button
                        className="cv-icon-btn"
                        onClick={() => void handleFinalReportDownload(doc.id)}
                        title="Baixar"
                        type="button"
                      >
                        <Download size={13} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            {/* AI-generated preliminary report */}
            {!caseReport ? (
              <EmptyState
                description="O resumo demonstrativo ainda não está disponível. Revisão humana persistida, IA real e PDF/exportação ficam no roadmap."
                icon={<Shield size={20} />}
                title="Relatório preliminar não disponível"
              />
            ) : (
              <div className="space-y-6">
                <Card>
                  <div className="flex items-start justify-between gap-4 mb-4">
                    <div>
                      <h2 className="text-sm font-bold text-[var(--text)]">
                        {caseReport.title}
                      </h2>
                      <p className="mt-1 text-[11px] text-[var(--text3)]">
                        Versão {caseReport.version} ·{" "}
                        {formatDate(caseReport.generatedAt)}
                      </p>
                    </div>
                    <StatusBadge status={caseReport.status} />
                  </div>

                  {caseReport.status === "in_review" && (
                    <div className="mb-5 flex items-center gap-3 rounded-lg border border-[rgba(249,115,22,0.25)] bg-[var(--orange-dim)] px-4 py-3">
                      <AlertTriangle className="shrink-0 text-[var(--orange)]" size={16} />
                      <p className="text-xs text-[var(--text2)]">
                        Este relatório está em revisão demonstrativa. Validação
                        humana persistida, aprovação real e entrega ao cliente ficam
                        no roadmap.
                      </p>
                    </div>
                  )}

                  <p className="text-sm leading-6 text-[var(--text2)]">
                    {caseReport.summary}
                  </p>
                  <dl className="mt-5 grid gap-3 border-t border-[var(--bd)] pt-4 text-xs sm:grid-cols-3">
                    <div>
                      <dt className="text-[var(--text3)]">Recomendação</dt>
                      <dd className="mt-0.5 font-semibold text-[var(--text)]">
                        {recommendationLabel(caseReport.recommendation)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-[var(--text3)]">Confiança</dt>
                      <dd className="mt-0.5 font-semibold text-[var(--text)]">
                        {typeof caseReport.confidence === "number"
                          ? `${(caseReport.confidence * 100).toFixed(0)}%`
                          : "Não informado"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-[var(--text3)]">Status</dt>
                      <dd className="mt-0.5 font-semibold text-[var(--text)]">
                        {reportStatusLabel(caseReport)}
                      </dd>
                    </div>
                  </dl>
                </Card>

                {caseReport.risks.length > 0 && (
                  <Card title="Indicadores demonstrativos de risco">
                    <div className="space-y-4">
                      {caseReport.risks.map((risk) => (
                        <div
                          className={`rounded-lg border p-4 ${
                            risk.level === "high"
                              ? "border-red-500/20 bg-red-500/5"
                              : risk.level === "medium"
                              ? "border-[rgba(249,115,22,0.2)] bg-[var(--orange-dim)]"
                              : "border-[rgba(32,201,151,0.2)] bg-[var(--teal-dim)]"
                          }`}
                          key={risk.id}
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <StatusBadge status={risk.level} />
                            <p className="text-sm font-semibold text-[var(--text)]">
                              {risk.title}
                            </p>
                          </div>
                          <p className="text-xs leading-5 text-[var(--text2)]">
                            {risk.description}
                          </p>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}

                {caseReport.recommendations.length > 0 && (
                  <Card title="Recomendações">
                    <ul className="space-y-2">
                      {caseReport.recommendations.map((rec, i) => (
                        <li className="flex items-start gap-3" key={i}>
                          <CheckCircle2
                            className="mt-0.5 shrink-0 text-[var(--teal)]"
                            size={14}
                          />
                          <p className="text-xs leading-5 text-[var(--text2)]">
                            {recommendationLabel(rec)}
                          </p>
                        </li>
                      ))}
                    </ul>
                  </Card>
                )}

                {caseReport.limitations && caseReport.limitations.length > 0 && (
                  <Card title="Limitações">
                    <ul className="space-y-2">
                      {caseReport.limitations.map((limitation, index) => (
                        <li className="text-xs leading-5 text-[var(--text2)]" key={index}>
                          {limitation}
                        </li>
                      ))}
                    </ul>
                  </Card>
                )}

                {caseReport.sourceRefs && caseReport.sourceRefs.length > 0 && (
                  <Card title="Fontes utilizadas">
                    <ul className="space-y-2">
                      {caseReport.sourceRefs.map((sourceRef, index) => (
                        <li className="text-xs leading-5 text-[var(--text2)]" key={index}>
                          {sourceRef}
                        </li>
                      ))}
                    </ul>
                  </Card>
                )}

                <div className="flex items-center gap-3 rounded-lg border border-[var(--bd)] bg-[var(--surf2)] p-4">
                  <FileText className="shrink-0 text-[var(--text3)]" size={16} />
                  <p className="text-xs text-[var(--text2)]">
                    PDF/exportação real ainda não está implementado nesta versão;
                    permanece como etapa planejada do roadmap.
                  </p>
                  <button
                    className="ml-auto shrink-0 rounded-lg border border-[var(--bd)] bg-[var(--surf3)] px-3 py-1.5 text-xs font-medium text-[var(--text3)] cursor-not-allowed opacity-50"
                    disabled
                    type="button"
                  >
                    PDF no roadmap
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </AppLayout>
    </AuthGuard>
  );
}
