"use client";

import {
  Download,
  FileText,
  Plus,
  RefreshCw,
  Send,
  Upload,
  X
} from "lucide-react";
import Link from "next/link";
import type { ChangeEvent, FormEvent, ReactNode } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { AppLayout } from "@/components/AppLayout";
import { AuthGuard } from "@/components/AuthGuard";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { FormField, SelectInput, TextInput } from "@/components/FormField";
import { LoadingState } from "@/components/LoadingState";
import { Notification } from "@/components/Notification";
import { PageTitle } from "@/components/PageTitle";
import { StatusBadge } from "@/components/StatusBadge";
import { formatDate } from "@/lib/formatters";
import { errorMessage } from "@/src/lib/errorMessage";
import { listCases } from "@/src/services/cases";
import {
  enqueueDocumentProcessing,
  getDocumentDownloadUrl,
  listDocuments,
  uploadDocument
} from "@/src/services/documents";
import { validateDocumentUploadForm, type ValidationErrors } from "@/src/lib/validation";
import type { Case, Document } from "@/types";

type DocumentForm = {
  caseId: string;
  notes: string;
};

const emptyDocumentForm: DocumentForm = {
  caseId: "",
  notes: ""
};

const acceptedUploadTypes = ".pdf,.png,.jpg,.jpeg,.docx,.txt,.md";

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${Math.round(bytes / 1024)} KB`;
  }

  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function documentTypeLabel(contentType: string): string {
  const labels: Record<string, string> = {
    "application/pdf": "PDF",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
    "image/jpeg": "JPG",
    "image/png": "PNG",
    "text/markdown": "MD",
    "text/plain": "TXT"
  };

  return labels[contentType] ?? contentType.split("/")[1]?.toUpperCase() ?? "Arquivo";
}

function documentSourceLabel(document: Document): string {
  if (document.status === "uploaded") {
    return "Anexo local do caso";
  }

  return "Metadados do MVP local";
}

export default function DocumentsPage() {
  const [actionMessage, setActionMessage] = useState("");
  const [actionBusyId, setActionBusyId] = useState("");
  const [cases, setCases] = useState<Case[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [error, setError] = useState("");
  const [fallbackReason, setFallbackReason] = useState("");
  const [form, setForm] = useState<DocumentForm>(emptyDocumentForm);
  const [formErrors, setFormErrors] = useState<ValidationErrors>({});
  const [loading, setLoading] = useState(true);
  const [pendingEnqueue, setPendingEnqueue] = useState<Document | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedCase, setSelectedCase] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const refreshDocuments = useCallback(async () => {
    setLoading(true);
    setError("");
    setActionMessage("");

    try {
      const [casesResult, documentsResult] = await Promise.all([
        listCases(),
        listDocuments()
      ]);
      setCases(casesResult.data);
      setDocuments(documentsResult.data);
      setForm((current) => ({
        ...current,
        caseId: current.caseId || casesResult.data[0]?.id || ""
      }));
      setFallbackReason(
        casesResult.source === "mock" || documentsResult.source === "mock"
          ? casesResult.fallbackReason ?? documentsResult.fallbackReason ?? ""
          : ""
      );
    } catch (err) {
      setError(errorMessage(err, "Não foi possível carregar documentos."));
      setFallbackReason("");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refreshDocuments();
    }, 0);

    return () => window.clearTimeout(timer);
  }, [refreshDocuments]);

  const visibleDocuments = useMemo(() => {
    return selectedCase
      ? documents.filter((document) => document.caseId === selectedCase)
      : documents;
  }, [documents, selectedCase]);

  function updateForm<K extends keyof DocumentForm>(field: K, value: DocumentForm[K]) {
    setForm((current) => ({ ...current, [field]: value }));
    setFormErrors((current) => ({ ...current, [field]: "" }));
    setError("");
    setActionMessage("");
  }

  function clearSelectedFile() {
    setSelectedFile(null);
    setFormErrors((current) => ({ ...current, file: "" }));
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setFormErrors((current) => ({ ...current, file: "" }));
    setError("");
    setActionMessage("");
  }

  function closeUploadForm() {
    setShowForm(false);
    setFormErrors({});
    setForm((current) => ({ ...emptyDocumentForm, caseId: current.caseId }));
    clearSelectedFile();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting) {
      return;
    }

    const validation = validateDocumentUploadForm({
      caseId: form.caseId,
      file: selectedFile
    });
    setFormErrors(validation.errors);
    if (!validation.valid) {
      setError("Revise os campos destacados antes de enviar o documento.");
      return;
    }

    setSubmitting(true);
    setError("");
    setActionMessage("");

    try {
      const result = await uploadDocument({
        caseId: form.caseId,
        file: selectedFile as File,
        metadata: {
          notes: form.notes.trim(),
          source: "frontend_local_upload"
        }
      });
      setDocuments((current) => [result.data, ...current]);
      setFallbackReason("");
      setActionMessage("Documento enviado e vinculado ao caso no armazenamento local do MVP.");
      setShowForm(false);
      setForm((current) => ({ ...emptyDocumentForm, caseId: current.caseId }));
      clearSelectedFile();
      setFormErrors({});
    } catch (err) {
      setError(errorMessage(err, "Não foi possível carregar documentos."));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDownloadUrl(documentId: string) {
    setActionMessage("");
    setError("");
    setActionBusyId(`download-${documentId}`);

    try {
      const result = await getDocumentDownloadUrl(documentId);
      setFallbackReason(result.source === "mock" ? result.fallbackReason ?? fallbackReason : fallbackReason);
      setActionMessage(
        result.source === "mock"
          ? "Backend local indisponível: URL temporária simulada para desenvolvimento."
          : `URL temporária gerada pela API local. Expiração: ${result.data.expires_in_seconds}s.`
      );
    } catch (err) {
      setError(errorMessage(err, "Não foi possível carregar documentos."));
    } finally {
      setActionBusyId("");
    }
  }

  async function confirmEnqueue() {
    if (!pendingEnqueue) {
      return;
    }

    const documentId = pendingEnqueue.id;
    setActionMessage("");
    setError("");
    setActionBusyId(`enqueue-${documentId}`);

    try {
      const result = await enqueueDocumentProcessing(documentId);
      setActionMessage(`Job local/MVP de processamento registrado: ${result.data.job_id}.`);
      setPendingEnqueue(null);
    } catch (err) {
      setError(errorMessage(err, "Não foi possível carregar documentos."));
    } finally {
      setActionBusyId("");
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
                variant="secondary"
              >
                Novo Pedido
              </Button>
              <Button
                icon={<RefreshCw aria-hidden="true" size={15} />}
                loading={loading}
                onClick={() => void refreshDocuments()}
                variant="secondary"
              >
                Atualizar
              </Button>
              <Button
                icon={<Upload aria-hidden="true" size={15} />}
                onClick={() => {
                  setShowForm((current) => !current);
                  setError("");
                  setActionMessage("");
                }}
              >
                Enviar documento
              </Button>
            </div>
          }
          description="Organize documentos como insumos locais vinculados a casos. Upload é local/MVP; OCR, IA, cloud e SQS reais não estão ativos nesta tela."
          eyebrow="Documentos"
          title="Insumos e anexos jurídicos"
        />

        {fallbackReason && (
          <Notification title="Fallback local ativo" tone="warning">
            A API local não respondeu. A listagem pode usar dados demonstrativos do fallback local.
          </Notification>
        )}
        {error && !loading && (
          <Notification onDismiss={() => setError("")} title="Atenção" tone="error">
            {error}
          </Notification>
        )}
        {actionMessage && (
          <Notification onDismiss={() => setActionMessage("")} title="Ação local do MVP" tone="success">
            {actionMessage}
          </Notification>
        )}

        {showForm && (
          <form
            className="cv-form-card mb-6 p-4 sm:p-5"
            onSubmit={handleSubmit}
          >
            <div className="mb-4 flex flex-col gap-1">
              <h2 className="text-sm font-semibold text-[var(--text)]">Enviar documento ao caso</h2>
              <p className="text-xs leading-5 text-[var(--text2)]">
                Vincule um arquivo ao caso selecionado para organizar insumos do MVP local. O envio local não executa OCR, IA, storage cloud ou SQS real.
              </p>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField error={formErrors.caseId} label="Caso vinculado" required>
                <SelectInput
                  disabled={cases.length === 0}
                  invalid={Boolean(formErrors.caseId)}
                  onChange={(event) => updateForm("caseId", event.target.value)}
                  value={form.caseId}
                >
                  {cases.length === 0 ? (
                    <option value="">Nenhum caso disponível</option>
                  ) : (
                    cases.map((legalCase) => (
                      <option key={legalCase.id} value={legalCase.id}>
                        {legalCase.code} · {legalCase.clientName}
                      </option>
                    ))
                  )}
                </SelectInput>
              </FormField>
              <FormField error={formErrors.file} label="Arquivo" required>
                <input
                  aria-invalid={Boolean(formErrors.file) || undefined}
                  accept={acceptedUploadTypes}
                  className={`cv-input w-full px-3 ${formErrors.file ? "cv-input-invalid" : ""}`}
                  onChange={handleFileChange}
                  ref={fileInputRef}
                  type="file"
                />
              </FormField>
              <FormField label="Observação">
                <TextInput
                  onChange={(event) => updateForm("notes", event.target.value)}
                  placeholder="Observação para o MVP local"
                  value={form.notes}
                />
              </FormField>
            </div>
            {selectedFile && (
              <div className="cv-list-row mt-4 flex items-center gap-3 px-4 py-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--surf3)]">
                  <FileText className="text-[var(--text2)]" size={16} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-semibold text-[var(--text)]">
                    {selectedFile.name}
                  </p>
                  <p className="text-[11px] text-[var(--text3)]">
                    {formatBytes(selectedFile.size)} · {documentTypeLabel(selectedFile.type)}
                  </p>
                </div>
                <button
                  aria-label="Remover arquivo selecionado"
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-[var(--text2)] transition hover:bg-red-500/10 hover:text-red-500"
                  onClick={clearSelectedFile}
                  type="button"
                >
                  <X size={14} />
                </button>
              </div>
            )}
            <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <Button disabled={submitting} onClick={closeUploadForm} variant="secondary">
                Cancelar
              </Button>
              <Button
                icon={<Upload aria-hidden="true" size={15} />}
                loading={submitting}
                type="submit"
              >
                Enviar documento
              </Button>
            </div>
          </form>
        )}

        <div className="mb-6 max-w-sm">
          <FormField label="Filtrar por caso vinculado">
            <SelectInput
              onChange={(event) => setSelectedCase(event.target.value)}
              value={selectedCase}
            >
              <option value="">Todos os casos</option>
              {cases.map((legalCase) => (
                <option key={legalCase.id} value={legalCase.id}>
                  {legalCase.code}
                </option>
              ))}
            </SelectInput>
          </FormField>
        </div>

        <Card
          actions={
            <Button href="/reports" size="sm" variant="secondary">
              Relatórios
            </Button>
          }
          title="Documentos do fluxo"
          description="Arquivos e metadados vinculados a casos. Relatórios é a área geral de entrega/revisão; não há relatório prometido por documento."
        >
          {loading ? (
            <LoadingState
              description="Carregando casos e documentos vinculados."
              label="Carregando documentos"
              rows={4}
            />
          ) : error && documents.length === 0 ? (
            <ErrorState
              action={
                <Button icon={<RefreshCw size={15} />} onClick={() => void refreshDocuments()} variant="secondary">
                  Tentar novamente
                </Button>
              }
              description="A listagem de documentos não pôde ser carregada. Erros da API local são exibidos sem fallback indevido."
              details={error}
            />
          ) : visibleDocuments.length === 0 ? (
            <EmptyState
              action={
                <Button icon={<Upload size={15} />} onClick={() => setShowForm(true)}>
                  Enviar documento
                </Button>
              }
              secondaryAction={
                selectedCase ? (
                  <Button onClick={() => setSelectedCase("")} variant="secondary">
                    Ver todos os casos
                  </Button>
                ) : (
                  <Button href="/cases/new" icon={<Plus size={15} />} variant="secondary">
                    Novo Pedido
                  </Button>
                )
              }
              description={
                selectedCase
                  ? "Nenhum documento encontrado para o caso selecionado. Envie um anexo local ou limpe o filtro para revisar outros casos."
                  : "Envie arquivos locais vinculados a casos ou inicie Novo Pedido para organizar primeiro o contexto jurídico."
              }
              icon={<FileText size={20} />}
              title={selectedCase ? "Sem documentos neste caso" : "Sem documentos enviados"}
              variant="compact"
            />
          ) : (
            <div className="space-y-3">
              {visibleDocuments.map((doc) => (
                <div
                  className="cv-list-row flex flex-col gap-4 px-4 py-3 md:flex-row md:items-center"
                  key={doc.id}
                >
                  <div className="flex min-w-0 flex-1 items-center gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--surf3)]">
                      <FileText className="text-[var(--text2)]" size={16} />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-xs font-semibold text-[var(--text)]">
                        {doc.filename}
                      </p>
                      <p className="text-[11px] text-[var(--text3)]">
                        {doc.sizeLabel} · {documentTypeLabel(doc.contentType)}
                      </p>
                      <span className="cv-badge cv-badge-muted mt-1">
                        {documentSourceLabel(doc)}
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-xs sm:grid-cols-3 md:flex md:items-center md:gap-5">
                    <div>
                      <p className="text-[11px] text-[var(--text3)]">Caso</p>
                      <Link
                        className="font-medium text-[var(--teal)] hover:underline"
                        href={`/cases/${doc.caseId}`}
                      >
                        {doc.caseCode}
                      </Link>
                    </div>
                    <div>
                      <p className="text-[11px] text-[var(--text3)]">Upload</p>
                      <p className="text-[var(--text2)]">{formatDate(doc.uploadedAt)}</p>
                    </div>
                    <div className="self-center">
                      <StatusBadge status={doc.status} />
                    </div>
                  </div>
                  <div className="flex items-center gap-2 md:ml-auto">
                    <IconButton
                      disabled={Boolean(actionBusyId)}
                      label="Gerar URL temporária local"
                      loading={actionBusyId === `download-${doc.id}`}
                      onClick={() => void handleDownloadUrl(doc.id)}
                    >
                      <Download size={13} />
                    </IconButton>
                    <IconButton
                      disabled={Boolean(actionBusyId)}
                      label="Registrar processamento local"
                      loading={actionBusyId === `enqueue-${doc.id}`}
                      onClick={() => setPendingEnqueue(doc)}
                    >
                      <Send size={13} />
                    </IconButton>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <ConfirmDialog
          confirmLabel="Registrar localmente"
          description="A API local valida o contexto do caso e documento quando disponível antes de registrar o job local/MVP. Esta ação não promete OCR, IA ou análise jurídica automática nesta tela."
          loading={Boolean(actionBusyId)}
          onCancel={() => setPendingEnqueue(null)}
          onConfirm={() => void confirmEnqueue()}
          open={Boolean(pendingEnqueue)}
          title={`Registrar processamento local de ${pendingEnqueue?.filename ?? "documento"}?`}
        />
      </AppLayout>
    </AuthGuard>
  );
}

function IconButton({
  children,
  disabled = false,
  label,
  loading = false,
  onClick
}: {
  children: ReactNode;
  disabled?: boolean;
  label: string;
  loading?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      aria-label={label}
      className="flex h-11 w-11 items-center justify-center rounded-lg border border-[var(--bd)] bg-[var(--surf2)] text-[var(--text2)] transition hover:bg-[var(--surf3)] hover:text-[var(--text)] disabled:cursor-not-allowed disabled:opacity-45"
      disabled={disabled || loading}
      onClick={onClick}
      title={label}
      type="button"
    >
      {loading ? (
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current/30 border-t-current" />
      ) : (
        children
      )}
    </button>
  );
}
