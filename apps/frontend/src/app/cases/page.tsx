"use client";

import {
  ArrowRight,
  BriefcaseBusiness,
  Calendar,
  FileText,
  Filter,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Shield,
  Trash2,
  UsersRound,
  X
} from "lucide-react";
import Link from "next/link";
import type { FormEvent } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AppLayout } from "@/components/AppLayout";
import { AuthGuard } from "@/components/AuthGuard";
import { Button } from "@/components/Button";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { FormField, SelectInput, TextArea, TextInput } from "@/components/FormField";
import { LoadingState } from "@/components/LoadingState";
import { Notification } from "@/components/Notification";
import { PageTitle } from "@/components/PageTitle";
import { PriorityBadge } from "@/components/PriorityBadge";
import { StatusBadge } from "@/components/StatusBadge";
import { formatDate, caseDisplayTitle } from "@/lib/formatters";
import { errorMessage } from "@/src/lib/errorMessage";
import { createCase, deleteCase, listCases, updateCase } from "@/src/services/cases";
import { listClients } from "@/src/services/clients";
import { validateCaseForm, type ValidationErrors } from "@/src/lib/validation";
import type { Case, CaseCreate, CaseStatus, CaseUpdate, Client, Priority, ProductType } from "@/types";

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

const contractTypes = [
  { id: "contract_analysis", label: "Análise Contratual" },
  { id: "compra_venda", label: "Compra e Venda" },
  { id: "prestacao_servicos", label: "Prestação de Serviços" },
  { id: "locacao", label: "Locação" },
  { id: "confidencialidade", label: "Confidencialidade (NDA)" },
  { id: "due_diligence", label: "Due Diligence" },
  { id: "outro", label: "Outro" }
];

const productOptions: Array<{ id: ProductType; label: string }> = [
  { id: "analise_contratual", label: "Análise contratual" },
  { id: "dados_partes", label: "Dados das partes" },
  { id: "consulta_objeto", label: "Consulta do objeto" },
  { id: "reuniao_equipe", label: "Reunião com equipe" }
];

const statusFilterOptions: Array<{ id: CaseStatus; label: string }> = [
  { id: "draft", label: "Rascunho" },
  { id: "created", label: "Criado" },
  { id: "document_attached", label: "Documento anexado" },
  { id: "awaiting_triage", label: "Aguardando triagem" },
  { id: "triage_running", label: "Triagem em andamento" },
  { id: "triage_partial", label: "Triagem parcial" },
  { id: "triage_completed", label: "Triagem concluída" },
  { id: "ai_running", label: "IA mock em andamento" },
  { id: "report_ready", label: "Relatório pronto" },
  { id: "needs_human_review", label: "Revisão humana necessária" },
  { id: "submitted", label: "Enviado no MVP" },
  { id: "triagem_pendente", label: "Triagem" },
  { id: "coleta_pendente", label: "Coleta" },
  { id: "processamento_documental", label: "Processamento local de documentos" },
  { id: "analise_contratual", label: "Análise local" },
  { id: "compliance", label: "Compliance" },
  { id: "minuta_relatorio", label: "Minuta de relatório" },
  { id: "revisao_humana", label: "Revisão conceitual" },
  { id: "processing", label: "Processamento local" },
  { id: "review", label: "Revisão local" },
  { id: "approved", label: "Aprovação local" },
  { id: "delivered", label: "Entrega local" },
  { id: "completed", label: "Concluído no MVP" },
  { id: "failed", label: "Falha" },
  { id: "cancelled", label: "Cancelado" }
];

type CaseForm = {
  caseType: string;
  clientId: string;
  notes: string;
  priority: Priority;
  product: ProductType;
  title: string;
};

const emptyCaseForm: CaseForm = {
  caseType: "contract_analysis",
  clientId: "",
  notes: "",
  priority: "normal",
  product: "analise_contratual",
  title: ""
};

function productDisplayLabel(product: ProductType): string {
  return productOptions.find((option) => option.id === product)?.label ?? product;
}

function reportStatusLabel(legalCase: Case): string {
  const reportStatus = legalCase.metadata?.reportStatus;
  if (typeof reportStatus !== "string" || !reportStatus) {
    return "Pendente";
  }

  const labels: Record<string, string> = {
    failed: "Falhou",
    generating: "Gerando",
    not_started: "Pendente",
    ready: "Pronto"
  };

  return labels[reportStatus] ?? reportStatus;
}

function sourceModeLabel(legalCase: Case): string {
  const sourceMode = legalCase.sourceMode ?? legalCase.metadata?.sourceMode;
  if (typeof sourceMode !== "string" || !sourceMode) {
    return "api";
  }

  const labels: Record<string, string> = {
    hybrid: "híbrido",
    local: "local",
    mock: "mock",
    real: "real",
    simulated: "simulado"
  };

  return labels[sourceMode] ?? sourceMode;
}

export default function CasesPage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [error, setError] = useState("");
  const [fallbackReason, setFallbackReason] = useState("");
  const [filter, setFilter] = useState("");
  const [form, setForm] = useState<CaseForm>(emptyCaseForm);
  const [formErrors, setFormErrors] = useState<ValidationErrors>({});
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [editing, setEditing] = useState<Case | null>(null);
  const [editPriority, setEditPriority] = useState<Priority>("normal");
  const [editStatus, setEditStatus] = useState<CaseStatus>("draft");
  const [editSaving, setEditSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteCandidate, setDeleteCandidate] = useState<Case | null>(null);

  function openEdit(legalCase: Case, event: React.MouseEvent) {
    event.preventDefault();
    event.stopPropagation();
    setEditing(legalCase);
    setEditPriority(legalCase.priority);
    setEditStatus(legalCase.status);
    setError("");
    setSuccessMessage("");
  }

  function closeEdit() {
    setEditing(null);
    setEditSaving(false);
  }

  async function handleEditSave() {
    if (!editing || editSaving) return;
    setEditSaving(true);
    setError("");
    try {
      const payload: CaseUpdate = {
        priority: editPriority,
        status: editStatus
      };
      const result = await updateCase(editing.id, payload, clients);
      setCases((current) =>
        current.map((c) => (c.id === editing.id ? result.data : c))
      );
      setSuccessMessage(
        result.source === "mock"
          ? "Caso atualizado no fallback local."
          : "Caso atualizado pela API."
      );
      closeEdit();
    } catch (err) {
      setError(errorMessage(err, "Não foi possível salvar a edição."));
    } finally {
      setEditSaving(false);
    }
  }

  async function handleDelete(legalCase: Case, event: React.MouseEvent) {
    event.preventDefault();
    event.stopPropagation();
    if (deletingId) return;
    setDeleteCandidate(legalCase);
  }

  async function confirmDelete() {
    const legalCase = deleteCandidate;
    if (!legalCase) return;
    setDeletingId(legalCase.id);
    setError("");
    try {
      const result = await deleteCase(legalCase.id);
      setCases((current) => current.filter((c) => c.id !== legalCase.id));
      setSuccessMessage(
        result.source === "mock"
          ? "Caso removido do fallback local."
          : "Caso excluído pela API."
      );
      setDeleteCandidate(null);
    } catch (err) {
      setError(errorMessage(err, "Não foi possível excluir o caso."));
    } finally {
      setDeletingId(null);
    }
  }

  function cancelDelete() {
    setDeleteCandidate(null);
  }

  const refreshCases = useCallback(async () => {
    setLoading(true);
    setError("");
    setSuccessMessage("");

    try {
      const clientsResult = await listClients();
      const casesResult = await listCases(clientsResult.data);
      setClients(clientsResult.data);
      setCases(casesResult.data);
      setForm((current) => ({
        ...current,
        clientId: current.clientId || clientsResult.data[0]?.id || ""
      }));
      setFallbackReason(
        clientsResult.source === "mock" || casesResult.source === "mock"
          ? clientsResult.fallbackReason ?? casesResult.fallbackReason ?? ""
          : ""
      );
    } catch (err) {
      setError(errorMessage(err, "Não foi possível carregar casos."));
      setFallbackReason("");
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

  const filteredCases = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return cases.filter((legalCase) => {
      const matchesStatus = filter ? legalCase.status === filter : true;
      const matchesQuery = normalized
        ? [
            legalCase.code,
            legalCase.clientName,
            legalCase.caseType,
            caseDisplayTitle(legalCase)
          ]
            .join(" ")
            .toLowerCase()
            .includes(normalized)
        : true;
      return matchesStatus && matchesQuery;
    });
  }, [cases, filter, query]);

  function updateForm<K extends keyof CaseForm>(field: K, value: CaseForm[K]) {
    setForm((current) => ({ ...current, [field]: value }));
    setFormErrors((current) => ({ ...current, [field]: "" }));
    setError("");
    setSuccessMessage("");
  }

  function clearListFilters() {
    setFilter("");
    setQuery("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting) {
      return;
    }

    const validation = validateCaseForm(form);
    setFormErrors(validation.errors);
    if (!validation.valid) {
      setError("Revise os campos destacados antes de criar o caso.");
      return;
    }

    setSubmitting(true);
    setError("");
    setSuccessMessage("");

    try {
      const payload: CaseCreate = {
        case_type: form.caseType,
        client_id: form.clientId,
        metadata: {
          notes: form.notes.trim(),
          product: form.product,
          source: "frontend",
          title: form.title.trim()
        },
        priority: form.priority
      };
      const result = await createCase(payload, clients);
      setCases((current) => [result.data, ...current]);
      setFallbackReason(result.source === "mock" ? result.fallbackReason ?? "" : "");
      setSuccessMessage(
        result.source === "mock"
          ? "Caso criado no fallback local de desenvolvimento."
          : "Caso criado pela API local."
      );
      setShowForm(false);
      setForm((current) => ({
        ...emptyCaseForm,
        clientId: current.clientId || clients[0]?.id || ""
      }));
      setFormErrors({});
    } catch (err) {
      setError(errorMessage(err, "Não foi possível carregar casos."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthGuard>
      <AppLayout>
        <PageTitle
          actions={
            <div className="flex flex-wrap items-center gap-2">
              <Button
                href="/cases/new"
                icon={<Plus aria-hidden="true" size={15} />}
              >
                Novo Pedido
              </Button>
              <Button
                icon={<RefreshCw aria-hidden="true" size={15} />}
                loading={loading}
                onClick={() => void refreshCases()}
                variant="secondary"
              >
                Atualizar
              </Button>
              <Button
                icon={<Plus aria-hidden="true" size={15} />}
                onClick={() => {
                  setShowForm((current) => !current);
                  setError("");
                  setSuccessMessage("");
                }}
                variant="secondary"
              >
                Criar caso rápido
              </Button>
            </div>
          }
          description="Acompanhe registros existentes, abra detalhes para analisar e editar, e use Novo Pedido como fluxo principal de entrada do MVP local."
          eyebrow="Casos"
          title="Operação de casos"
        />

        {fallbackReason && (
          <Notification title="Fallback local ativo" tone="warning">
            A API local não respondeu. A lista usa dados demonstrativos e não substitui validação com PostgreSQL local.
          </Notification>
        )}
        {successMessage && (
          <Notification onDismiss={() => setSuccessMessage("")} title="Ação local registrada" tone="success">
            {successMessage}
          </Notification>
        )}
        {error && !loading && (
          <Notification onDismiss={() => setError("")} title="Atenção" tone="error">
            {error}
          </Notification>
        )}

        {showForm && (
          <form
            className="cv-form-card mb-6 p-4 sm:p-5"
            onSubmit={handleSubmit}
          >
            <div className="mb-4 flex flex-col gap-1">
              <h2 className="text-sm font-semibold text-[var(--text)]">Caso rápido local</h2>
              <p className="text-xs leading-5 text-[var(--text2)]">
                Ação operacional direta para o MVP local. O fluxo principal continua
                sendo Novo Pedido.
              </p>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="md:col-span-2">
                <FormField error={formErrors.title} label="Título do caso" required>
                  <TextInput
                    invalid={Boolean(formErrors.title)}
                    onChange={(event) => updateForm("title", event.target.value)}
                    placeholder="Análise contratual local"
                    value={form.title}
                  />
                </FormField>
              </div>
              <FormField error={formErrors.clientId} label="Cliente vinculado" required>
                <SelectInput
                  disabled={clients.length === 0}
                  invalid={Boolean(formErrors.clientId)}
                  onChange={(event) => updateForm("clientId", event.target.value)}
                  value={form.clientId}
                >
                  {clients.length === 0 ? (
                    <option value="">Nenhum cliente disponível</option>
                  ) : (
                    clients.map((client) => (
                      <option key={client.id} value={client.id}>
                        {client.name}
                      </option>
                    ))
                  )}
                </SelectInput>
              </FormField>
              <FormField error={formErrors.caseType} label="Tipo de caso" required>
                <SelectInput
                  invalid={Boolean(formErrors.caseType)}
                  onChange={(event) => updateForm("caseType", event.target.value)}
                  value={form.caseType}
                >
                  {contractTypes.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.label}
                    </option>
                  ))}
                </SelectInput>
              </FormField>
              <FormField label="Produto">
                <SelectInput
                  onChange={(event) => updateForm("product", event.target.value as ProductType)}
                  value={form.product}
                >
                  {productOptions.map((product) => (
                    <option key={product.id} value={product.id}>
                      {product.label}
                    </option>
                  ))}
                </SelectInput>
              </FormField>
              <FormField error={formErrors.priority} label="Prioridade" required>
                <SelectInput
                  invalid={Boolean(formErrors.priority)}
                  onChange={(event) => updateForm("priority", event.target.value as Priority)}
                  value={form.priority}
                >
                  <option value="low">Baixa</option>
                  <option value="normal">Normal</option>
                  <option value="high">Alta</option>
                  <option value="urgent">Urgente</option>
                </SelectInput>
              </FormField>
              <div className="md:col-span-2">
                <FormField label="Observações">
                  <TextArea
                    onChange={(event) => updateForm("notes", event.target.value)}
                    placeholder="Observação demonstrativa local"
                    value={form.notes}
                  />
                </FormField>
              </div>
            </div>
            <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <Button disabled={submitting} onClick={() => setShowForm(false)} variant="secondary">
                Cancelar
              </Button>
              <Button loading={submitting} type="submit">
                Criar caso
              </Button>
            </div>
          </form>
        )}

        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative w-full max-w-sm sm:w-80">
              <Search
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text3)]"
                size={14}
              />
              <input
                className="cv-input w-full pl-9 pr-3 text-sm"
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Buscar por código, cliente ou título..."
                type="search"
                value={query}
              />
            </div>
            <div className="relative w-full sm:w-auto">
              <Filter
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text3)]"
                size={13}
              />
              <select
                className="cv-input w-full pl-9 pr-3 text-xs font-medium [&_option]:bg-[var(--surf)]"
                onChange={(event) => setFilter(event.target.value)}
                value={filter}
              >
                <option value="">Todos os status</option>
                {statusFilterOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {!loading && (
            <p className="text-xs text-[var(--text2)]">
              {filteredCases.length} caso{filteredCases.length !== 1 ? "s" : ""} exibido{filteredCases.length !== 1 ? "s" : ""}
            </p>
          )}
        </div>

        {loading ? (
          <LoadingState
            description="Carregando clientes e casos da API local ou fallback local."
            label="Carregando casos"
          />
        ) : error && cases.length === 0 ? (
          <ErrorState
            action={
              <Button icon={<RefreshCw size={15} />} onClick={() => void refreshCases()} variant="secondary">
                Tentar novamente
              </Button>
            }
            description="A listagem de casos não pôde ser carregada pela API local. Se for 401/403, faça login novamente com uma conta autorizada."
            details={error}
          />
        ) : filteredCases.length === 0 ? (
          <EmptyState
            action={
              query || filter ? (
                <Button icon={<Filter size={15} />} onClick={clearListFilters} variant="secondary">
                  Limpar filtros
                </Button>
              ) : (
                <Button href="/cases/new" icon={<Plus size={15} />}>
                  Novo Pedido
                </Button>
              )
            }
            secondaryAction={
              query || filter ? (
                <Button href="/cases/new" icon={<Plus size={15} />}>
                  Novo Pedido
                </Button>
              ) : (
                <Button onClick={() => setShowForm(true)} variant="secondary">
                  Criar caso rápido
                </Button>
              )
            }
            description={
              query || filter
                ? "Nenhum registro existente corresponde à busca atual. Limpe os filtros ou inicie uma nova simulação em Novo Pedido."
                : clients.length === 0
                  ? "Use Novo Pedido para simular o fluxo principal. O caso rápido exige um cliente já disponível no MVP local."
                  : "Use Novo Pedido para compor uma simulação frontend-first ou crie um caso rápido para validação operacional local."
            }
            icon={<BriefcaseBusiness size={20} />}
            title={query || filter ? "Nenhum caso corresponde aos filtros" : "Nenhum registro operacional ainda"}
          />
        ) : (
          <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
            {filteredCases.map((c) => (
              <Link
                className="cv-card cv-card-hover group block p-5"
                href={`/cases/${c.id}`}
                key={c.id}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-[var(--bd)] bg-[var(--surf2)] transition group-hover:border-[rgba(32,201,151,0.25)] group-hover:bg-[var(--teal-dim)]">
                    <BriefcaseBusiness
                      className="text-[var(--text2)] transition group-hover:text-[var(--teal)]"
                      size={18}
                    />
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button
                      aria-label="Editar caso"
                      className="cv-icon-btn"
                      onClick={(e) => openEdit(c, e)}
                      type="button"
                    >
                      <Pencil size={13} />
                    </button>
                    <button
                      aria-label="Excluir caso"
                      className="cv-icon-btn cv-icon-btn--danger"
                      disabled={deletingId === c.id}
                      onClick={(e) => handleDelete(c, e)}
                      type="button"
                    >
                      <Trash2 size={13} />
                    </button>
                    <StatusBadge status={c.status} />
                  </div>
                </div>

                <p className="mt-4 text-[11px] font-semibold text-brand-teal">
                  {c.code}
                </p>
                <p className="mt-1 text-[10px] font-semibold uppercase tracking-normal text-[var(--text3)]">
                  Origem: {sourceModeLabel(c)}
                </p>
                <h2 className="mt-1 line-clamp-2 min-h-10 text-sm font-semibold leading-5 text-[var(--text)]">
                  {caseDisplayTitle(c)}
                </h2>
                <p className="mt-1 truncate text-xs text-[var(--text2)]">{c.clientName}</p>
                <p className="mt-1 text-[11px] text-[var(--text3)]">
                  {caseTypeLabel[c.caseType] ?? c.caseType} · {c.productLabel ?? productDisplayLabel(c.product)}
                </p>

                <div className="mt-4">
                  <div className="mb-1.5 flex items-center justify-between">
                    <span className="text-[10px] text-[var(--text3)]">Progresso</span>
                    <span className="text-[10px] font-semibold text-[var(--text2)]">
                      {c.progressPercent}%
                    </span>
                  </div>
                  <div className="h-1 overflow-hidden rounded-full bg-[var(--surf3)]">
                    <div
                      className={`h-1 rounded-full transition-all ${
                        c.progressPercent === 100
                          ? "bg-teal-500"
                          : c.progressPercent > 60
                            ? "bg-brand-teal"
                            : "bg-violet-500"
                      }`}
                      style={{ width: `${c.progressPercent}%` }}
                    />
                  </div>
                </div>

                <div className="mt-4 grid gap-2 text-xs">
                  <div className="flex min-w-0 items-center gap-2 text-[var(--text2)]">
                    <UsersRound className="shrink-0 text-[var(--text3)]" size={12} />
                    <span className="truncate">Cliente: {c.clientName}</span>
                  </div>
                  <div className="flex min-w-0 items-center gap-2 text-[var(--text2)]">
                    <FileText className="shrink-0 text-[var(--text3)]" size={12} />
                    <span className="truncate">
                      Documentos: {c.documentsCount} na listagem
                    </span>
                  </div>
                  <div className="flex min-w-0 items-center gap-2 text-[var(--text2)]">
                    <Shield className="shrink-0 text-[var(--text3)]" size={12} />
                    <span className="truncate">Relatório: {reportStatusLabel(c)}</span>
                  </div>
                </div>

                <div className="mt-3 flex items-center justify-between gap-3 border-t border-[var(--bd)] pt-3 text-[11px] text-[var(--text3)]">
                  <span className="flex min-w-0 items-center gap-1.5">
                    <Calendar className="shrink-0" size={11} />
                    <span className="truncate">Atualizado em {formatDate(c.updatedAt)}</span>
                  </span>
                  <span className="flex shrink-0 items-center gap-2">
                    <PriorityBadge priority={c.priority} />
                    <ArrowRight className="text-[var(--text3)] transition group-hover:text-[var(--teal)]" size={13} />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}

        {editing && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
            onClick={closeEdit}
          >
            <div
              className="cv-card w-full max-w-md p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-start justify-between gap-3 mb-5">
                <div>
                  <h2 className="text-base font-bold text-[var(--text)]">
                    Editar caso
                  </h2>
                  <p className="mt-1 text-xs text-[var(--text2)]">
                    {editing.code} · {caseDisplayTitle(editing)}
                  </p>
                </div>
                <button
                  aria-label="Fechar"
                  className="cv-icon-btn"
                  onClick={closeEdit}
                  type="button"
                >
                  <X size={14} />
                </button>
              </div>

              <div className="space-y-4">
                <FormField label="Prioridade">
                  <SelectInput
                    onChange={(e) => setEditPriority(e.target.value as Priority)}
                    value={editPriority}
                  >
                    <option value="low">Baixa</option>
                    <option value="normal">Normal</option>
                    <option value="high">Alta</option>
                    <option value="urgent">Urgente</option>
                  </SelectInput>
                </FormField>

                <FormField label="Status">
                  <SelectInput
                    onChange={(e) => setEditStatus(e.target.value as CaseStatus)}
                    value={editStatus}
                  >
                    {statusFilterOptions.map((option) => (
                      <option key={option.id} value={option.id}>
                        {option.label}
                      </option>
                    ))}
                  </SelectInput>
                </FormField>
              </div>

              <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
                <Button
                  disabled={editSaving}
                  onClick={closeEdit}
                  variant="secondary"
                >
                  Cancelar
                </Button>
                <Button loading={editSaving} onClick={() => void handleEditSave()}>
                  Salvar alterações
                </Button>
              </div>
            </div>
          </div>
        )}
        <ConfirmDialog
          cancelLabel="Cancelar"
          confirmLabel="Excluir caso"
          description={
            deleteCandidate
              ? `Excluir o caso "${caseDisplayTitle(deleteCandidate)}" (${deleteCandidate.code})? A ação faz soft-delete: o caso some da listagem, mas pode ser recuperado pelo admin do banco.`
              : ""
          }
          loading={Boolean(deletingId)}
          onCancel={cancelDelete}
          onConfirm={() => void confirmDelete()}
          open={Boolean(deleteCandidate)}
          title="Confirmar exclusão"
          variant="danger"
        />
      </AppLayout>
    </AuthGuard>
  );
}
