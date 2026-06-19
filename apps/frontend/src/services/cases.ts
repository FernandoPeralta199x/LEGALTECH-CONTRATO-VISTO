import {
  MODULOS,
  PRODUTOS,
  type Modulo,
  type Produto
} from "../../lib/produtoConfig";
import type {
  Case,
  CaseAggregate,
  CaseCreate,
  CaseListFilters,
  CaseOperationSummary,
  CaseUpdate,
  Client,
  Document,
  LegalRequest,
  Party,
  ProviderResult,
  ProductType,
  Report,
  TimelineEvent,
  TriageModule
} from "../../types";
import {
  findStoredLocalCase,
  getStoredLocalCases,
  saveLocalCaseFromWizard,
  saveStoredLocalCase,
  type LocalCaseWizardInput
} from "../lib/localCases";
import { ApiClientError, apiClient } from "./apiClient";
import { fallbackReason, shouldUseMockFallback, type ServiceResult } from "./fallback";

type BackendCase = {
  id: string;
  client_id: string;
  case_type: string;
  status: string;
  priority: "low" | "normal" | "high" | "urgent";
  metadata: Record<string, unknown>;
  submitted_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

type BackendOperationalCase = {
  id?: string;
  case_id?: string;
  request_id?: string | null;
  code?: string;
  title?: string;
  description?: string;
  case_type?: string;
  product_type?: string;
  product_label?: string;
  client_id?: string | null;
  client_name?: string | null;
  status?: string;
  progress?: number;
  risk_level?: string;
  recommendation?: string | null;
  parties_count?: number;
  documents_count?: number;
  triage_status?: string;
  report_status?: string;
  source_mode?: string;
  created_at?: string;
  updated_at?: string;
};

type BackendCaseListPage = {
  items: BackendOperationalCase[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

type BackendCaseListPayload = BackendCase[] | BackendCaseListPage;

type BackendLegalRequest = {
  id: string;
  code: string;
  organization_id: string;
  created_by: string;
  product_type: string;
  product_label: string;
  title: string;
  description: string;
  status: string;
  source_mode: string;
  idempotency_key: string | null;
  created_at: string;
  updated_at: string;
};

type BackendAggregateCase = {
  id: string;
  request_id: string | null;
  code: string;
  organization_id: string;
  created_by: string;
  product_type: string;
  product_label: string;
  title: string;
  description: string;
  status: string;
  progress: number;
  risk_level: string;
  recommendation: string | null;
  source_mode: string;
  is_local_simulation: boolean;
  created_at: string;
  updated_at: string;
};

type BackendAggregateParty = {
  id: string;
  case_id: string;
  organization_id: string;
  name: string;
  document_masked: string | null;
  document_type: string;
  person_type: string;
  role: string;
  email: string | null;
  phone: string | null;
  status: string;
  risk_level: string;
  provider_status_summary: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

type BackendAggregateDocument = {
  id: string;
  case_id: string;
  organization_id: string;
  filename: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  storage_provider: string;
  storage_key: string;
  status: string;
  ocr_status: string;
  ai_read_status: string;
  preview_available: boolean;
  download_available: boolean;
  uploaded_at: string | null;
  updated_at: string;
};

type BackendAggregateTimelineEvent = {
  id: string;
  case_id: string;
  organization_id: string;
  type: string;
  title: string;
  description: string;
  severity: string;
  source: string;
  source_mode: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

type BackendAggregateTriageModule = {
  id: string;
  case_id: string;
  organization_id: string;
  module_key: string;
  module_label: string;
  provider: string;
  status: string;
  source_mode: string;
  required: boolean;
  reason: string;
  started_at: string | null;
  finished_at: string | null;
  attempts: number;
  error_code: string | null;
  error_message: string | null;
  summary: string | null;
  result_ref: string | null;
  raw_result_ref: string | null;
  created_at: string;
  updated_at: string;
};

type BackendAggregateProviderResult = {
  id: string;
  case_id: string;
  triage_module_id: string;
  organization_id: string;
  provider: string;
  provider_request_id: string | null;
  source_mode: string;
  status: string;
  input_hash: string;
  raw_result_ref: string | null;
  normalized_result: Record<string, unknown>;
  summary: string | null;
  risk_signals: string[];
  confidence: number | null;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

type BackendAggregateReport = {
  id: string;
  case_id: string;
  organization_id: string;
  status: string;
  version: number;
  summary: string;
  findings: string[];
  legal_risks: string[];
  commercial_risks: string[];
  reputational_risks: string[];
  contractual_risks: string[];
  missing_information: string[];
  recommendation: string;
  confidence: number | null;
  limitations: string[];
  source_refs: Array<Record<string, unknown> | string>;
  generated_by: string | null;
  generated_at: string | null;
  updated_at: string;
};

type BackendAggregateSummary = {
  case_id: string;
  organization_id: string;
  parties_count: number;
  documents_count: number;
  timeline_count?: number;
  triage_status: string;
  report_status: string;
  risk_level: string;
  recommendation?: string | null;
  progress: number;
  latest_event_at: string | null;
  source_mode: string;
  updated_at: string;
};

type BackendCaseAggregate = {
  case: BackendAggregateCase;
  request: BackendLegalRequest | null;
  parties: BackendAggregateParty[];
  documents: BackendAggregateDocument[];
  timeline: BackendAggregateTimelineEvent[];
  triage_modules: BackendAggregateTriageModule[];
  provider_results: BackendAggregateProviderResult[];
  report: BackendAggregateReport | null;
  summary: BackendAggregateSummary;
};

type BackendWizardSubmitResponse = BackendLegalRequest & {
  request_id?: string;
  request_status?: string;
  case_id?: string;
  case_code?: string;
  case_status?: string;
  documents_count?: number;
  parties_count?: number;
  triage_modules_count?: number;
  timeline_events_count?: number;
};

export type WizardOperationalSubmitInput = LocalCaseWizardInput & {
  idempotencyKey: string;
};

export type WizardOperationalSubmitResult = {
  requestId: string;
  caseId: string;
  caseCode: string;
  status: string;
  productType: ProductType;
  productLabel: string;
  documentsCount: number;
  partiesCount: number;
  triageModulesCount: number;
  timelineEventsCount: number;
  sourceMode: Case["sourceMode"];
};

const productAliases: Record<string, ProductType> = {
  analise_contratual: "analise_contratual",
  contract_analysis: "analise_contratual",
  consulta_objeto: "consulta_objeto",
  dados_partes: "dados_partes",
  reuniao_advogado: "reuniao_equipe",
  reuniao_equipe: "reuniao_equipe"
};

function caseCodeFromId(id: string): string {
  if (id.toLowerCase().startsWith("case-")) {
    return id.replace(/^case-/i, "CASE-").toUpperCase();
  }

  return `CASO-${id.slice(0, 8).toUpperCase()}`;
}

function productFromMetadata(metadata: Record<string, unknown>): ProductType {
  const product = metadata.product;

  return typeof product === "string"
    ? productAliases[product] ?? "analise_contratual"
    : "analise_contratual";
}

function progressFromStatus(status: string): number {
  const progress: Record<string, number> = {
    approved: 95,
    cancelled: 0,
    completed: 100,
    delivered: 100,
    draft: 5,
    failed: 100,
    processing: 45,
    review: 80,
    submitted: 15
  };

  return progress[status] ?? 35;
}

function clampProgress(progress: number): number {
  return Math.max(0, Math.min(100, Math.round(progress)));
}

function isPaginatedCaseList(payload: BackendCaseListPayload): payload is BackendCaseListPage {
  return !Array.isArray(payload) && Array.isArray(payload.items);
}

function caseTypeFromProduct(product: ProductType, rawCaseType?: string): string {
  if (rawCaseType && rawCaseType !== product) {
    return rawCaseType;
  }

  return product === "analise_contratual" ? "contract_analysis" : product;
}

function selectedWizardModules(modulos: Record<Modulo, boolean>): Modulo[] {
  return (Object.keys(MODULOS) as Modulo[]).filter((modulo) => modulos[modulo]);
}

function caseTypeForWizardProduct(product: Produto): string {
  const map: Record<Produto, string> = {
    analise_contratual: "contract_analysis",
    consulta_objeto: "object_query",
    dados_partes: "party_data",
    reuniao_equipe: "lawyer_meeting"
  };

  return map[product];
}

function primaryWizardPartyName(input: LocalCaseWizardInput): string {
  return (
    input.parties.find((party) => party.nome.trim())?.nome.trim() ??
    "Cliente nao informado"
  );
}

function wizardTitle(input: LocalCaseWizardInput): string {
  return `${PRODUTOS[input.produto].titulo} - ${primaryWizardPartyName(input)}`;
}

function wizardDescription(input: LocalCaseWizardInput): string {
  const activeModules = selectedWizardModules(input.modulos);
  const documentText = input.arquivo?.name
    ? `Documento informado: ${input.arquivo.name}.`
    : "Sem documento informado.";

  return [
    "Pedido criado pelo fluxo Novo Pedido / Wizard.",
    `Produto juridico: ${PRODUTOS[input.produto].titulo}.`,
    `Modulos selecionados: ${activeModules.length}.`,
    documentText
  ].join(" ");
}

function mapWizardSubmitPayload(input: WizardOperationalSubmitInput) {
  const activeModules = selectedWizardModules(input.modulos);
  const productLabel = PRODUTOS[input.produto].titulo;

  return {
    product_type: input.produto,
    product_label: productLabel,
    title: wizardTitle(input),
    description: wizardDescription(input),
    source_mode: "mock",
    idempotency_key: input.idempotencyKey,
    notes: "Criado pelo Wizard operacional backend mock/local.",
    selected_modules: activeModules,
    parties: input.parties
      .filter((party) => party.nome.trim())
      .map((party) => ({
        name: party.nome.trim(),
        document: (party.documento ?? "").trim() || null,
        document_type: party.tipoPessoa === "pj" ? "cnpj" : "cpf",
        person_type: party.tipoPessoa === "pj" ? "company" : "individual",
        role: party.papel,
        email: (party.email ?? "").trim() || null,
        phone: (party.telefone ?? "").trim() || null,
        metadata: {
          source: "new_case_wizard",
          wizard_party_id: party.id
        }
      })),
    document:
      input.arquivo?.status === "done"
        ? {
            filename: input.arquivo.name,
            original_filename: input.arquivo.name,
            mime_type: input.arquivo.type || "application/octet-stream",
            size_bytes: input.arquivo.size,
            storage_provider: "local",
            status: "uploaded",
            preview_available: false,
            download_available: false
          }
        : null,
    metadata: {
      case_type: caseTypeForWizardProduct(input.produto),
      module_names: activeModules.map((modulo) => MODULOS[modulo].titulo),
      modules: activeModules,
      product: input.produto,
      source: "new_case_wizard",
      source_mode: "mock"
    }
  };
}

function mapWizardSubmitResponse(
  payload: BackendWizardSubmitResponse
): WizardOperationalSubmitResult {
  const requestId = payload.request_id ?? payload.id;
  const caseId = payload.case_id ?? "";
  return {
    requestId,
    caseId,
    caseCode: payload.case_code ?? caseCodeFromId(caseId || requestId),
    status: payload.case_status ?? payload.status,
    productType: productAliases[payload.product_type] ?? "analise_contratual",
    productLabel: payload.product_label,
    documentsCount: payload.documents_count ?? 0,
    partiesCount: payload.parties_count ?? 0,
    triageModulesCount: payload.triage_modules_count ?? 0,
    timelineEventsCount: payload.timeline_events_count ?? 0,
    sourceMode: payload.source_mode as Case["sourceMode"]
  };
}

function buildCaseListQuery(filters: CaseListFilters = {}): string {
  const search = new URLSearchParams();

  if (filters.status) search.set("status", filters.status);
  if (filters.caseType) search.set("case_type", filters.caseType);
  if (filters.clientId) search.set("client_id", filters.clientId);
  if (filters.productType) search.set("product_type", filters.productType);
  if (filters.riskLevel) search.set("risk_level", filters.riskLevel);
  if (filters.q) search.set("q", filters.q);
  if (filters.page) search.set("page", String(filters.page));
  if (filters.pageSize) search.set("page_size", String(filters.pageSize));
  if (filters.sortBy) search.set("sort_by", filters.sortBy);
  if (filters.sortOrder) search.set("sort_order", filters.sortOrder);

  const query = search.toString();
  return query ? `?${query}` : "";
}

function resolveListCasesArgs(
  filtersOrClients: CaseListFilters | Client[] = {},
  maybeClients: Client[] = []
): { filters: CaseListFilters; clients: Client[] } {
  if (Array.isArray(filtersOrClients)) {
    return { filters: {}, clients: filtersOrClients };
  }

  return { filters: filtersOrClients, clients: maybeClients };
}

export function mapBackendCase(
  legalCase: BackendCase,
  clients: Client[] = []
): Case {
  const client = clients.find((item) => item.id === legalCase.client_id);

  return {
    id: legalCase.id,
    code: caseCodeFromId(legalCase.id),
    clientId: legalCase.client_id,
    clientName: client?.name ?? `Cliente ${legalCase.client_id.slice(0, 8)}`,
    caseType: legalCase.case_type,
    product: productFromMetadata(legalCase.metadata),
    status: legalCase.status as Case["status"],
    priority: legalCase.priority,
    documentsCount: 0,
    progressPercent: progressFromStatus(legalCase.status),
    assignedTo: null,
    notes:
      typeof legalCase.metadata.notes === "string"
        ? legalCase.metadata.notes
        : "",
    metadata: legalCase.metadata,
    parties: [],
    updatedAt: legalCase.updated_at,
    createdAt: legalCase.created_at,
    submittedAt: legalCase.submitted_at
  };
}

export function mapOperationalCase(legalCase: BackendOperationalCase): Case {
  const id = legalCase.case_id ?? legalCase.id ?? "";
  const product = productAliases[legalCase.product_type ?? ""] ?? "analise_contratual";
  const title = legalCase.title?.trim() || legalCase.code || "Caso operacional";
  const progress =
    typeof legalCase.progress === "number"
      ? clampProgress(legalCase.progress)
      : progressFromStatus(legalCase.status ?? "");

  return {
    id,
    code: legalCase.code ?? caseCodeFromId(id),
    clientId: legalCase.client_id ?? legalCase.request_id ?? id,
    clientName: legalCase.client_name?.trim() || "Nao informado",
    caseType: caseTypeFromProduct(product, legalCase.case_type),
    product,
    productLabel: legalCase.product_label,
    status: (legalCase.status ?? "created") as Case["status"],
    priority: "normal",
    documentsCount: legalCase.documents_count ?? 0,
    progressPercent: progress,
    progress,
    riskLevel: legalCase.risk_level as Case["riskLevel"],
    recommendation: legalCase.recommendation as Case["recommendation"],
    sourceMode: legalCase.source_mode as Case["sourceMode"],
    assignedTo: null,
    notes: legalCase.description ?? "",
    metadata: {
      description: legalCase.description,
      partiesCount: legalCase.parties_count ?? 0,
      recommendation: legalCase.recommendation,
      reportStatus: legalCase.report_status,
      requestId: legalCase.request_id,
      riskLevel: legalCase.risk_level,
      sourceMode: legalCase.source_mode,
      title,
      triageStatus: legalCase.triage_status
    },
    parties: [],
    updatedAt: legalCase.updated_at ?? new Date().toISOString(),
    createdAt: legalCase.created_at ?? legalCase.updated_at ?? new Date().toISOString(),
    submittedAt: legalCase.created_at ?? null
  };
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function isUuidLike(value: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
}

function mapAggregateCase(payload: BackendCaseAggregate): Case {
  const firstParty = payload.parties[0];
  return mapOperationalCase({
    id: payload.case.id,
    case_id: payload.case.id,
    request_id: payload.case.request_id,
    code: payload.case.code,
    title: payload.case.title,
    description: payload.case.description,
    case_type: payload.case.product_type,
    product_type: payload.case.product_type,
    product_label: payload.case.product_label,
    client_name: firstParty?.name,
    status: payload.case.status,
    progress: payload.summary.progress,
    risk_level: payload.summary.risk_level,
    recommendation: payload.case.recommendation,
    parties_count: payload.summary.parties_count,
    documents_count: payload.summary.documents_count,
    triage_status: payload.summary.triage_status,
    report_status: payload.summary.report_status,
    source_mode: payload.summary.source_mode,
    created_at: payload.case.created_at,
    updated_at: payload.summary.updated_at
  });
}

function mapLegalRequest(request: BackendLegalRequest | null): LegalRequest | null {
  if (!request) return null;

  return {
    id: request.id,
    code: request.code,
    organizationId: request.organization_id,
    createdBy: request.created_by,
    productType: productAliases[request.product_type] ?? "analise_contratual",
    productLabel: request.product_label,
    title: request.title,
    description: request.description,
    status: request.status as LegalRequest["status"],
    sourceMode: request.source_mode as LegalRequest["sourceMode"],
    idempotencyKey: request.idempotency_key,
    createdAt: request.created_at,
    updatedAt: request.updated_at
  };
}

function mapAggregateParty(party: BackendAggregateParty): Party {
  return {
    id: party.id,
    caseId: party.case_id,
    organizationId: party.organization_id,
    name: party.name,
    document: party.document_masked ?? "",
    documentMasked: party.document_masked ?? undefined,
    documentType: party.document_type as Party["documentType"],
    personType: party.person_type as Party["personType"],
    type: party.role,
    role: party.role,
    email: party.email ?? "",
    phone: party.phone ?? "",
    notes: typeof party.metadata.notes === "string" ? party.metadata.notes : "",
    status: party.status as Party["status"],
    riskLevel: party.risk_level as Party["riskLevel"],
    providerStatusSummary: party.provider_status_summary,
    metadata: party.metadata,
    createdAt: party.created_at,
    updatedAt: party.updated_at
  };
}

function mapAggregateDocument(document: BackendAggregateDocument): Document {
  const uploadedAt = document.uploaded_at ?? document.updated_at;
  return {
    id: document.id,
    filename: document.filename,
    originalFilename: document.original_filename,
    caseId: document.case_id,
    organizationId: document.organization_id,
    caseCode: caseCodeFromId(document.case_id),
    contentType: document.mime_type,
    mimeType: document.mime_type,
    status: document.status as Document["status"],
    sizeBytes: document.size_bytes,
    sizeLabel: formatBytes(document.size_bytes),
    fileHash: null,
    storageProvider: document.storage_provider as Document["storageProvider"],
    storageKey: document.storage_key,
    ocrStatus: document.ocr_status as Document["ocrStatus"],
    aiReadStatus: document.ai_read_status as Document["aiReadStatus"],
    previewAvailable: document.preview_available,
    downloadAvailable: document.download_available,
    uploadedAt,
    updatedAt: document.updated_at,
    processedAt: document.status === "processed" ? document.updated_at : null,
    metadata: {},
    notes: ""
  };
}

function timelineStatusFromSeverity(severity: string): TimelineEvent["status"] {
  if (severity === "error") return "failed";
  if (severity === "success") return "completed";
  return "processing";
}

function mapAggregateTimelineEvent(event: BackendAggregateTimelineEvent): TimelineEvent {
  return {
    id: event.id,
    caseId: event.case_id,
    organizationId: event.organization_id,
    type: event.type,
    title: event.title,
    status: timelineStatusFromSeverity(event.severity),
    label: event.title,
    description: event.description,
    severity: event.severity as TimelineEvent["severity"],
    source: event.source as TimelineEvent["source"],
    sourceMode: event.source_mode as TimelineEvent["sourceMode"],
    actor: event.source,
    metadata: event.metadata,
    createdAt: event.created_at
  };
}

function mapAggregateTriageModule(module: BackendAggregateTriageModule): TriageModule {
  return {
    id: module.id,
    caseId: module.case_id,
    organizationId: module.organization_id,
    moduleKey: module.module_key,
    moduleLabel: module.module_label,
    provider: module.provider,
    status: module.status as TriageModule["status"],
    sourceMode: module.source_mode as TriageModule["sourceMode"],
    required: module.required,
    reason: module.reason,
    startedAt: module.started_at,
    finishedAt: module.finished_at,
    attempts: module.attempts,
    errorCode: module.error_code,
    errorMessage: module.error_message,
    summary: module.summary,
    resultRef: module.result_ref,
    rawResultRef: module.raw_result_ref,
    createdAt: module.created_at,
    updatedAt: module.updated_at
  };
}

function mapAggregateProviderResult(result: BackendAggregateProviderResult): ProviderResult {
  return {
    id: result.id,
    caseId: result.case_id,
    triageModuleId: result.triage_module_id,
    organizationId: result.organization_id,
    provider: result.provider,
    providerRequestId: result.provider_request_id,
    sourceMode: result.source_mode as ProviderResult["sourceMode"],
    status: result.status as ProviderResult["status"],
    inputHash: result.input_hash,
    rawResultRef: result.raw_result_ref,
    normalizedResult: result.normalized_result,
    summary: result.summary,
    riskSignals: result.risk_signals,
    confidence: result.confidence,
    errorCode: result.error_code,
    errorMessage: result.error_message,
    createdAt: result.created_at,
    updatedAt: result.updated_at
  };
}

function sourceRefLabel(sourceRef: Record<string, unknown> | string): string {
  if (typeof sourceRef === "string") return sourceRef;
  const type = typeof sourceRef.type === "string" ? sourceRef.type : "source";
  const id = typeof sourceRef.id === "string" ? sourceRef.id : undefined;
  const summary = typeof sourceRef.summary === "string" ? sourceRef.summary : undefined;
  return [type, id, summary].filter(Boolean).join(" · ");
}

function mapAggregateReport(report: BackendAggregateReport | null, legalCase: Case): Report | null {
  if (!report) return null;

  const riskSections = [
    ...report.legal_risks.map((description, index) => ({
      id: `${report.id}-legal-${index}`,
      level: "medium" as const,
      title: "Risco jurídico",
      description
    })),
    ...report.commercial_risks.map((description, index) => ({
      id: `${report.id}-commercial-${index}`,
      level: "medium" as const,
      title: "Risco comercial",
      description
    })),
    ...report.reputational_risks.map((description, index) => ({
      id: `${report.id}-reputational-${index}`,
      level: "medium" as const,
      title: "Risco reputacional",
      description
    })),
    ...report.contractual_risks.map((description, index) => ({
      id: `${report.id}-contractual-${index}`,
      level: "medium" as const,
      title: "Risco contratual",
      description
    }))
  ];

  return {
    id: report.id,
    caseId: report.case_id,
    organizationId: report.organization_id,
    caseCode: legalCase.code,
    status: report.status as Report["status"],
    title: `Relatório ${legalCase.code}`,
    summary: report.summary,
    findings: report.findings,
    legalRisks: report.legal_risks,
    commercialRisks: report.commercial_risks,
    reputationalRisks: report.reputational_risks,
    contractualRisks: report.contractual_risks,
    missingInformation: report.missing_information,
    recommendation: report.recommendation as Report["recommendation"],
    confidence: report.confidence,
    limitations: report.limitations,
    sourceRefs: report.source_refs.map(sourceRefLabel),
    risks: riskSections,
    recommendations: report.recommendation ? [report.recommendation] : [],
    generatedAt: report.generated_at ?? report.updated_at,
    approvedAt: null,
    approvedBy: null,
    version: report.version
  };
}

function mapAggregateSummary(summary: BackendAggregateSummary): CaseOperationSummary {
  return {
    caseId: summary.case_id,
    organizationId: summary.organization_id,
    partiesCount: summary.parties_count,
    documentsCount: summary.documents_count,
    triageStatus: summary.triage_status as CaseOperationSummary["triageStatus"],
    reportStatus: summary.report_status as CaseOperationSummary["reportStatus"],
    riskLevel: summary.risk_level as CaseOperationSummary["riskLevel"],
    progress: clampProgress(summary.progress),
    latestEventAt: summary.latest_event_at,
    sourceMode: summary.source_mode as CaseOperationSummary["sourceMode"],
    updatedAt: summary.updated_at
  };
}

function fallbackDocumentsFromCase(legalCase: Case): Document[] {
  const wizardDocument = legalCase.metadata?.wizardDocument;
  if (!wizardDocument || typeof wizardDocument !== "object") return [];

  const documentMetadata = wizardDocument as Record<string, unknown>;
  const filename =
    typeof documentMetadata.filename === "string"
      ? documentMetadata.filename
      : "documento-local";
  const mimeType =
    typeof documentMetadata.mimeType === "string"
      ? documentMetadata.mimeType
      : "application/octet-stream";
  const sizeBytes =
    typeof documentMetadata.sizeBytes === "number"
      ? documentMetadata.sizeBytes
      : 0;
  const uploadedAt = legalCase.submittedAt ?? legalCase.createdAt;

  return [
    {
      id: `${legalCase.id}-document-local-1`,
      filename,
      originalFilename: filename,
      caseId: legalCase.id,
      organizationId: legalCase.organizationId ?? "local",
      caseCode: legalCase.code,
      contentType: mimeType,
      mimeType,
      status: "uploaded",
      sizeBytes,
      sizeLabel: formatBytes(sizeBytes),
      fileHash: null,
      storageProvider: "local",
      storageKey: `local/wizard/${legalCase.id}/${filename}`,
      ocrStatus: "not_started",
      aiReadStatus: "not_started",
      previewAvailable: false,
      downloadAvailable: false,
      uploadedAt,
      updatedAt: legalCase.updatedAt,
      processedAt: null,
      metadata: {
        source: "new_case_wizard",
        sourceMode: "local"
      },
      notes: "Metadata local do documento selecionado no Wizard."
    }
  ];
}

function metadataArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function fallbackTriageModulesFromCase(legalCase: Case): TriageModule[] {
  const moduleKeys = metadataArray(legalCase.metadata?.modules);
  const moduleNames = metadataArray(legalCase.metadata?.moduleNames);
  const now = legalCase.updatedAt;

  return moduleKeys.map((moduleKey, index) => ({
    id: `${legalCase.id}-triage-${moduleKey}`,
    caseId: legalCase.id,
    organizationId: legalCase.organizationId ?? "local",
    moduleKey,
    moduleLabel: moduleNames[index] ?? MODULOS[moduleKey as Modulo]?.titulo ?? moduleKey,
    provider: "mock_local",
    status: "not_started",
    sourceMode: "local",
    required: true,
    reason: "Módulo selecionado no Wizard local de fallback.",
    startedAt: null,
    finishedAt: null,
    attempts: 0,
    errorCode: null,
    errorMessage: null,
    summary: null,
    resultRef: null,
    rawResultRef: null,
    createdAt: legalCase.createdAt,
    updatedAt: now
  }));
}

function fallbackTimelineFromCase(
  legalCase: Case,
  documents: Document[],
  triageModules: TriageModule[]
): TimelineEvent[] {
  const organizationId = legalCase.organizationId ?? "local";
  const base = {
    caseId: legalCase.id,
    organizationId,
    source: "mock" as const,
    sourceMode: "local" as const,
    status: "completed" as const,
    createdAt: legalCase.createdAt
  };
  const events: TimelineEvent[] = [
    {
      ...base,
      id: `${legalCase.id}-timeline-request-created`,
      type: "request_created",
      title: "Pedido local criado",
      label: "Pedido local criado",
      description: "Fallback local registrou o pedido porque a API estava indisponível.",
      severity: "info",
      actor: "fallback-local",
      metadata: { source: "new_case_wizard", sourceMode: "local" }
    },
    {
      ...base,
      id: `${legalCase.id}-timeline-case-created`,
      type: "case_created",
      title: "Caso local criado",
      label: "Caso local criado",
      description: "Caso local de fallback criado com o mesmo case_id usado na navegação.",
      severity: "info",
      actor: "fallback-local",
      metadata: { source: "new_case_wizard", sourceMode: "local" }
    }
  ];

  legalCase.parties.forEach((party) => {
    events.push({
      ...base,
      id: `${legalCase.id}-timeline-party-${party.id}`,
      type: "party_added",
      title: "Parte adicionada",
      label: "Parte adicionada",
      description: "Parte informada no Wizard local vinculada ao caso de fallback.",
      severity: "info",
      actor: "fallback-local",
      metadata: { partyId: party.id, role: party.type, source: "new_case_wizard" }
    });
  });

  documents.forEach((document) => {
    events.push({
      ...base,
      id: `${legalCase.id}-timeline-document-${document.id}`,
      type: "document_attached",
      title: "Documento anexado",
      label: "Documento anexado",
      description: "Metadata do documento selecionado no Wizard local vinculada ao caso de fallback.",
      severity: "info",
      actor: "fallback-local",
      metadata: { documentId: document.id, filename: document.filename }
    });
  });

  if (triageModules.length > 0) {
    events.push({
      ...base,
      id: `${legalCase.id}-timeline-triage-plan-created`,
      type: "triage_plan_created",
      title: "Plano de triagem local criado",
      label: "Plano de triagem local criado",
      description: "Módulos selecionados no Wizard foram preservados no fallback local.",
      severity: "info",
      actor: "fallback-local",
      metadata: { moduleKeys: triageModules.map((module) => module.moduleKey) }
    });
  }

  events.push({
    ...base,
    id: `${legalCase.id}-timeline-wizard-completed`,
    type: "wizard_completed",
    title: "Wizard concluído",
    label: "Wizard concluído",
    description: "Novo Pedido concluído no fallback local explícito.",
    severity: "success",
    actor: "fallback-local",
    metadata: { source: "new_case_wizard", sourceMode: "local" }
  });

  return events;
}

function fallbackProgressFromAggregate(
  legalCase: Case,
  documents: Document[],
  triageModules: TriageModule[],
  timeline: TimelineEvent[]
): number {
  // Formula de fallback local: case/request (10) + partes (10) + documentos (10) + timeline (5) + plano de triagem (5).
  const progress =
    10 +
    (legalCase.parties.length > 0 ? 10 : 0) +
    (documents.length > 0 ? 10 : 0) +
    (timeline.length > 0 ? 5 : 0) +
    (triageModules.length > 0 ? 5 : 0);
  return clampProgress(Math.max(legalCase.progressPercent, Math.min(40, progress)));
}

export function mapBackendCaseAggregate(payload: BackendCaseAggregate): CaseAggregate {
  const legalCase = mapAggregateCase(payload);
  const parties = payload.parties.map(mapAggregateParty);
  return {
    case: {
      ...legalCase,
      parties,
      documentsCount: payload.summary.documents_count,
      progressPercent: clampProgress(payload.summary.progress)
    },
    request: mapLegalRequest(payload.request),
    parties,
    documents: payload.documents.map(mapAggregateDocument),
    timeline: payload.timeline.map(mapAggregateTimelineEvent),
    triageModules: payload.triage_modules.map(mapAggregateTriageModule),
    providerResults: payload.provider_results.map(mapAggregateProviderResult),
    report: mapAggregateReport(payload.report, legalCase),
    summary: mapAggregateSummary(payload.summary)
  };
}

function makeFallbackAggregate(legalCase: Case): CaseAggregate {
  const sourceMode = (legalCase.sourceMode ?? "mock") as CaseOperationSummary["sourceMode"];
  const fallbackDocuments = fallbackDocumentsFromCase(legalCase);
  const fallbackTriageModules = fallbackTriageModulesFromCase(legalCase);
  const fallbackTimeline = fallbackTimelineFromCase(
    legalCase,
    fallbackDocuments,
    fallbackTriageModules
  );
  const progress = fallbackProgressFromAggregate(
    legalCase,
    fallbackDocuments,
    fallbackTriageModules,
    fallbackTimeline
  );
  return {
    case: {
      ...legalCase,
      progress,
      progressPercent: progress
    },
    request: null,
    parties: legalCase.parties as Party[],
    documents: fallbackDocuments,
    timeline: fallbackTimeline,
    triageModules: fallbackTriageModules,
    providerResults: [],
    report: null,
    summary: {
      caseId: legalCase.id,
      organizationId: legalCase.organizationId,
      partiesCount: legalCase.parties.length,
      documentsCount: fallbackDocuments.length || legalCase.documentsCount,
      triageStatus: fallbackTriageModules.length > 0 ? "not_started" : "not_started",
      reportStatus: "not_started",
      riskLevel: legalCase.riskLevel ?? "unknown",
      progress,
      latestEventAt:
        fallbackTimeline.length > 0
          ? fallbackTimeline[fallbackTimeline.length - 1].createdAt
          : null,
      sourceMode,
      updatedAt: legalCase.updatedAt
    }
  };
}

function mapCaseListPayload(
  payload: BackendCaseListPayload,
  clients: Client[] = []
): Case[] {
  if (isPaginatedCaseList(payload)) {
    return payload.items.map((legalCase) => mapOperationalCase(legalCase));
  }

  return payload.map((legalCase) => mapBackendCase(legalCase, clients));
}

function makeMockCase(payload: CaseCreate, clients: Client[] = []): Case {
  const now = new Date().toISOString();
  const client = clients.find((item) => item.id === payload.client_id);

  return {
    id: `case-local-${Date.now()}`,
    code: `CASO-LOCAL-${Date.now().toString().slice(-4)}`,
    clientId: payload.client_id,
    clientName: client?.name ?? "Cliente",
    caseType: payload.case_type,
    product: productFromMetadata(payload.metadata ?? {}),
    status: "draft",
    priority: payload.priority ?? "normal",
    documentsCount: 0,
    progressPercent: 5,
    assignedTo: null,
    notes:
      typeof payload.metadata?.notes === "string"
        ? payload.metadata.notes
        : "",
    metadata: payload.metadata ?? { source: "frontend_mock_fallback" },
    parties: [],
    updatedAt: now,
    createdAt: now,
    submittedAt: null
  };
}

export function enrichCasesWithClients(cases: Case[], clients: Client[]): Case[] {
  return cases.map((legalCase) => {
    const client = clients.find((item) => item.id === legalCase.clientId);
    return client ? { ...legalCase, clientName: client.name } : legalCase;
  });
}

export async function listCases(
  filtersOrClients: CaseListFilters | Client[] = {},
  maybeClients: Client[] = []
): Promise<ServiceResult<Case[]>> {
  const { clients, filters } = resolveListCasesArgs(filtersOrClients, maybeClients);
  try {
    const response = await apiClient.get<BackendCaseListPayload>(
      `/api/v1/cases${buildCaseListQuery(filters)}`
    );
    return {
      data: mapCaseListPayload(response.data, clients),
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    return {
      data: getStoredLocalCases(),
      fallbackReason: fallbackReason(error),
      source: "mock"
    };
  }
}

export async function submitWizardRequest(
  input: WizardOperationalSubmitInput
): Promise<ServiceResult<WizardOperationalSubmitResult>> {
  try {
    const response = await apiClient.post<BackendWizardSubmitResponse>(
      "/api/v1/requests",
      mapWizardSubmitPayload(input)
    );
    return {
      data: mapWizardSubmitResponse(response.data),
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    const localCase = saveLocalCaseFromWizard(input);
    return {
      data: {
        requestId: localCase.requestId ?? localCase.id,
        caseId: localCase.id,
        caseCode: localCase.code,
        status: localCase.status,
        productType: localCase.product,
        productLabel: localCase.productLabel ?? PRODUTOS[localCase.product].titulo,
        documentsCount: localCase.documentsCount,
        partiesCount: localCase.parties.length,
        triageModulesCount: selectedWizardModules(input.modulos).length,
        timelineEventsCount:
          3 +
          localCase.parties.length +
          localCase.documentsCount +
          (selectedWizardModules(input.modulos).length > 0 ? 1 : 0),
        sourceMode: "local"
      },
      fallbackReason: fallbackReason(error),
      source: "mock"
    };
  }
}

export async function getCaseAggregate(
  caseId: string
): Promise<ServiceResult<CaseAggregate>> {
  const localCase = findStoredLocalCase(caseId);
  if (localCase && !isUuidLike(caseId)) {
    return {
      data: makeFallbackAggregate(localCase),
      source: "mock"
    };
  }

  try {
    const response = await apiClient.get<BackendCaseAggregate>(
      `/api/v1/cases/${caseId}/aggregate`
    );
    return {
      data: mapBackendCaseAggregate(response.data),
      source: "api"
    };
  } catch (error) {
    if (error instanceof ApiClientError && error.status === 404) {
      const legacy = await getCase(caseId);
      return {
        data: makeFallbackAggregate(legacy.data),
        fallbackReason: legacy.fallbackReason,
        source: legacy.source
      };
    }

    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    if (!localCase) {
      throw error;
    }

    return {
      data: makeFallbackAggregate(localCase),
      fallbackReason: fallbackReason(error),
      source: "mock"
    };
  }
}

export async function createCase(
  payload: CaseCreate,
  clients: Client[] = []
): Promise<ServiceResult<Case>> {
  try {
    const response = await apiClient.post<BackendCase>("/api/v1/cases", payload);
    return {
      data: mapBackendCase(response.data, clients),
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    return {
      data: makeMockCase(payload, clients),
      fallbackReason: fallbackReason(error),
      source: "mock"
    };
  }
}

export async function getCase(
  caseId: string,
  clients: Client[] = []
): Promise<ServiceResult<Case>> {
  const localCase = findStoredLocalCase(caseId);
  if (localCase) {
    return {
      data: localCase,
      source: "mock"
    };
  }

  try {
    const response = await apiClient.get<BackendCase>(`/api/v1/cases/${caseId}`);
    return {
      data: mapBackendCase(response.data, clients),
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    const legalCase = findStoredLocalCase(caseId);
    if (!legalCase) {
      throw error;
    }

    return {
      data: legalCase,
      fallbackReason: fallbackReason(error),
      source: "mock"
    };
  }
}

export async function updateCase(
  caseId: string,
  payload: CaseUpdate,
  clients: Client[] = []
): Promise<ServiceResult<Case>> {
  try {
    const response = await apiClient.patch<BackendCase>(
      `/api/v1/cases/${caseId}`,
      payload
    );
    return {
      data: mapBackendCase(response.data, clients),
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    const current = findStoredLocalCase(caseId);
    if (!current) {
      throw error;
    }
    const updated = saveStoredLocalCase({
      ...current,
      caseType: payload.case_type ?? current.caseType,
      clientId: payload.client_id ?? current.clientId,
      priority: payload.priority ?? current.priority,
      status: payload.status ?? current.status,
      updatedAt: new Date().toISOString()
    });
    return {
      data: updated,
      fallbackReason: fallbackReason(error),
      source: "mock"
    };
  }
}
