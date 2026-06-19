// ─── Enums & literals ─────────────────────────────────────────────────────────

export type Role = "owner" | "admin" | "analyst" | "client" | "support" | "viewer";

export const REQUEST_STATUS_VALUES = [
  "draft",
  "submitted",
  "case_created",
  "cancelled",
  "failed"
] as const;

export type RequestStatus = (typeof REQUEST_STATUS_VALUES)[number];

export const CASE_STATUS_VALUES = [
  "draft",
  "created",
  "document_attached",
  "awaiting_triage",
  "triage_running",
  "triage_partial",
  "triage_completed",
  "ai_running",
  "report_ready",
  "needs_human_review",
  "completed",
  "failed"
] as const;

export type StandardCaseStatus = (typeof CASE_STATUS_VALUES)[number];

export type LegacyCaseStatus =
  | "submitted"
  | "triagem_pendente"
  | "coleta_pendente"
  | "processamento_documental"
  | "analise_contratual"
  | "compliance"
  | "minuta_relatorio"
  | "revisao_humana"
  | "processing"
  | "review"
  | "approved"
  | "delivered"
  | "cancelled";

export type CaseStatus = StandardCaseStatus | LegacyCaseStatus;

export const MODULE_STATUS_VALUES = [
  "not_started",
  "queued",
  "running",
  "completed",
  "failed",
  "skipped",
  "provider_not_configured"
] as const;

export type ModuleStatus = (typeof MODULE_STATUS_VALUES)[number];

export const DOCUMENT_STATUS_VALUES = [
  "uploaded",
  "available",
  "processing",
  "processed",
  "failed",
  "missing"
] as const;

export type StandardDocumentStatus = (typeof DOCUMENT_STATUS_VALUES)[number];
export type LegacyDocumentStatus = "pending_upload" | "validated" | "deleted";
export type DocumentStatus = StandardDocumentStatus | LegacyDocumentStatus;

export const REPORT_STATUS_VALUES = [
  "not_started",
  "generating",
  "ready",
  "failed"
] as const;

export type StandardReportStatus = (typeof REPORT_STATUS_VALUES)[number];
export type LegacyReportStatus =
  | "draft"
  | "in_review"
  | "approved"
  | "delivered"
  | "rejected";
export type ReportStatus = StandardReportStatus | LegacyReportStatus;

export const PROVIDER_RESULT_STATUS_VALUES = [
  "pending",
  "running",
  "completed",
  "failed",
  "not_configured",
  "skipped"
] as const;

export type ProviderResultStatus = (typeof PROVIDER_RESULT_STATUS_VALUES)[number];

export const SOURCE_MODE_VALUES = [
  "local",
  "mock",
  "simulated",
  "real",
  "hybrid"
] as const;

export type SourceMode = (typeof SOURCE_MODE_VALUES)[number];

export const RISK_LEVEL_VALUES = [
  "unknown",
  "low",
  "medium",
  "high",
  "critical"
] as const;

export type RiskLevel = (typeof RISK_LEVEL_VALUES)[number];

export type Priority = "low" | "normal" | "high" | "urgent";

export type ClientStatus = "active" | "review" | "inactive";
export type ClientPersonType = "individual" | "company";
export type ClientContractRole =
  | "contractor"
  | "contracted"
  | "intervening"
  | "guarantor"
  | "witness"
  | "other";

export type ReviewStatus = "pending" | "approved" | "rejected" | "adjustment_requested";

export type AgentExecutionStatus = "queued" | "running" | "completed" | "failed" | "skipped";

export type PartyType =
  | "cliente"
  | "contraparte"
  | "responsavel"
  | "testemunha"
  | "outro"
  | "contratante"
  | "contratada"
  | "avalista"
  | "fiador";

export type ContractType =
  | "compra_venda"
  | "prestacao_servicos"
  | "locacao"
  | "parceria"
  | "confidencialidade"
  | "due_diligence"
  | "outro";

export type ProductType =
  | "dados_partes"
  | "consulta_objeto"
  | "analise_contratual"
  | "reuniao_equipe";

export type DocumentType = "cpf" | "cnpj" | "rg" | "unknown";
export type PersonType = "individual" | "company" | "unknown";
export type TimelineSeverity = "info" | "success" | "warning" | "error";
export type TimelineSource = "user" | "system" | "provider" | "ai" | "mock";
export type StorageProvider = "local" | "s3" | "mock";
export type ReportRecommendation =
  | "proceed"
  | "proceed_with_caution"
  | "do_not_proceed"
  | "human_review_required";

export type AuditAction =
  | "case_created"
  | "case_submitted"
  | "document_uploaded"
  | "document_processed"
  | "agent_started"
  | "agent_completed"
  | "report_generated"
  | "review_approved"
  | "review_rejected"
  | "review_adjustment"
  | "status_changed"
  | "user_login"
  | "user_logout";

// ─── Core entities ─────────────────────────────────────────────────────────────

export type LegalRequest = {
  id: string;
  code: string;
  organizationId: string;
  createdBy: string;
  productType: ProductType;
  productLabel: string;
  title: string;
  description: string;
  status: RequestStatus;
  sourceMode: SourceMode;
  idempotencyKey: string | null;
  createdAt: string;
  updatedAt: string;
};

export type Organization = {
  id: string;
  name: string;
  cnpj: string;
  plan: "starter" | "professional" | "enterprise";
  casesLimit: number;
  casesUsed: number;
  createdAt: string;
  status: "active" | "suspended";
};

export type User = {
  id: string;
  name: string;
  email: string;
  role: Role;
  organizationId: string;
  organizationName: string;
  avatarInitials: string;
  createdAt: string;
  lastLoginAt: string;
  status: "active" | "invited" | "inactive";
};

export type Client = {
  id: string;
  organizationId?: string;
  personType?: ClientPersonType;
  contractRole?: ClientContractRole;
  name: string;
  fullName?: string | null;
  legalName?: string | null;
  companyName?: string | null;
  tradeName?: string | null;
  displayName?: string | null;
  document?: string | null;
  documentType?: DocumentType;
  documentNumber?: string | null;
  documentMasked?: string | null;
  documentLabel: string;
  cpf?: string | null;
  cnpj?: string | null;
  rg?: string | null;
  birthDate?: string | null;
  email: string;
  phone: string;
  address?: string | null;
  status: ClientStatus;
  riskLevel: RiskLevel;
  sourceMode?: SourceMode;
  casesCount: number;
  metadata?: Record<string, unknown>;
  createdAt: string;
  updatedAt?: string;
};

export type CaseParty = {
  id: string;
  caseId: string;
  organizationId?: string;
  name: string;
  document: string;
  documentMasked?: string;
  documentType?: DocumentType;
  personType?: PersonType;
  type: PartyType | string;
  email: string;
  phone: string;
  notes: string;
  status?: ModuleStatus;
  riskLevel?: RiskLevel;
  providerStatusSummary?: string | null;
  metadata?: Record<string, unknown>;
  createdAt?: string;
  updatedAt?: string;
};

export type Party = CaseParty & {
  organizationId: string;
  role: PartyType | string;
  sourceMode?: SourceMode;
};

export type Case = {
  id: string;
  requestId?: string | null;
  code: string;
  organizationId?: string;
  createdBy?: string;
  clientId: string;
  clientName: string;
  caseType: ContractType | string;
  product: ProductType;
  productType?: ProductType;
  productLabel?: string;
  title?: string;
  description?: string;
  status: CaseStatus;
  priority: Priority;
  documentsCount: number;
  progressPercent: number;
  progress?: number;
  riskLevel?: RiskLevel;
  recommendation?: ReportRecommendation | null;
  sourceMode?: SourceMode;
  isLocalSimulation?: boolean;
  assignedTo: string | null;
  notes: string;
  estimatedValue?: number;
  metadata?: Record<string, unknown>;
  parties: CaseParty[];
  updatedAt: string;
  createdAt: string;
  submittedAt: string | null;
};

export type Document = {
  id: string;
  filename: string;
  originalFilename?: string;
  caseId: string;
  organizationId?: string;
  caseCode: string;
  contentType: string;
  mimeType?: string;
  status: DocumentStatus;
  sizeBytes?: number;
  sizeLabel: string;
  fileHash?: string | null;
  storageProvider?: StorageProvider;
  storageKey?: string;
  ocrStatus?: ModuleStatus;
  aiReadStatus?: ModuleStatus;
  previewAvailable?: boolean;
  downloadAvailable?: boolean;
  uploadedAt: string;
  updatedAt?: string;
  processedAt: string | null;
  metadata?: Record<string, unknown>;
  notes: string;
};

export type ClientCreate = {
  name: string;
  person_type?: ClientPersonType;
  contract_role?: ClientContractRole;
  full_name?: string | null;
  legal_name?: string | null;
  company_name?: string | null;
  trade_name?: string | null;
  display_name?: string | null;
  document_type?: DocumentType;
  document_number?: string | null;
  document?: string | null;
  cpf?: string | null;
  cnpj?: string | null;
  rg?: string | null;
  birth_date?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  source_mode?: SourceMode;
  metadata?: Record<string, unknown>;
};

export type ClientUpdate = Partial<ClientCreate>;

export type CaseCreate = {
  client_id: string;
  case_type: string;
  priority?: Priority;
  metadata?: Record<string, unknown>;
};

export type CreateCasePayload = CaseCreate & {
  request_id?: string;
  product_type?: ProductType;
  product_label?: string;
  title?: string;
  description?: string;
  source_mode?: SourceMode;
  idempotency_key?: string;
};

export type CreateRequestPayload = {
  product_type: ProductType;
  product_label: string;
  title: string;
  description?: string;
  source_mode?: SourceMode;
  idempotency_key?: string;
  metadata?: Record<string, unknown>;
};

export type CaseUpdate = Partial<CaseCreate> & {
  status?: CaseStatus;
};

export type CaseListFilters = {
  page?: number;
  pageSize?: number;
  status?: CaseStatus;
  productType?: ProductType;
  riskLevel?: RiskLevel;
  q?: string;
  caseType?: string;
  clientId?: string;
  sortBy?: "created_at" | "updated_at" | "status" | "risk_level";
  sortOrder?: "asc" | "desc";
};

export type CaseListItem = {
  id: string;
  code: string;
  title: string;
  clientName: string;
  productType: ProductType;
  productLabel: string;
  status: CaseStatus;
  progress: number;
  riskLevel: RiskLevel;
  sourceMode: SourceMode;
  documentsCount: number;
  partiesCount: number;
  updatedAt: string;
};

export type CasePartyCreate = {
  party_type: PartyType | string;
  name: string;
  document?: string | null;
  email?: string | null;
  phone?: string | null;
  notes?: string | null;
  metadata?: Record<string, unknown>;
};

export type CasePartyUpdate = Partial<CasePartyCreate>;

export type DocumentCreate = {
  case_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  file_hash?: string | null;
  status?: DocumentStatus;
  metadata?: Record<string, unknown>;
};

export type DocumentUpdate = Partial<DocumentCreate>;

export type AgentExecution = {
  id: string;
  caseId: string;
  agentName: string;
  agentType:
    | "triagem"
    | "coleta"
    | "doc_processor"
    | "contrato_analyzer"
    | "compliance"
    | "report_writer";
  status: AgentExecutionStatus;
  startedAt: string;
  finishedAt: string | null;
  durationMs: number | null;
  outputSummary: string | null;
  errorMessage: string | null;
};

export type TriageModule = {
  id: string;
  caseId: string;
  organizationId: string;
  moduleKey: string;
  moduleLabel: string;
  provider: string;
  status: ModuleStatus;
  sourceMode: SourceMode;
  required: boolean;
  reason: string;
  startedAt: string | null;
  finishedAt: string | null;
  attempts: number;
  errorCode: string | null;
  errorMessage: string | null;
  summary: string | null;
  resultRef: string | null;
  rawResultRef: string | null;
  createdAt: string;
  updatedAt: string;
};

export type ProviderResult = {
  id: string;
  caseId: string;
  triageModuleId: string;
  organizationId: string;
  provider: string;
  providerRequestId: string | null;
  sourceMode: SourceMode;
  status: ProviderResultStatus;
  inputHash: string;
  rawResultRef: string | null;
  normalizedResult: Record<string, unknown>;
  summary: string | null;
  riskSignals: string[];
  confidence: number | null;
  errorCode: string | null;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
};

export type Report = {
  id: string;
  caseId: string;
  organizationId?: string;
  caseCode: string;
  status: ReportStatus;
  title: string;
  summary: string;
  findings?: string[];
  legalRisks?: string[];
  commercialRisks?: string[];
  reputationalRisks?: string[];
  contractualRisks?: string[];
  missingInformation?: string[];
  recommendation?: ReportRecommendation;
  confidence?: number | null;
  limitations?: string[];
  sourceRefs?: string[];
  risks: ReportRisk[];
  recommendations: string[];
  generatedAt: string;
  approvedAt: string | null;
  approvedBy: string | null;
  version: number;
};

export type ReportRisk = {
  id: string;
  level: RiskLevel;
  title: string;
  description: string;
};

export type Review = {
  id: string;
  caseId: string;
  reportId: string;
  status: ReviewStatus;
  assignedTo: string;
  checklist: ReviewChecklistItem[];
  observations: string;
  createdAt: string;
  reviewedAt: string | null;
};

export type ReviewChecklistItem = {
  id: string;
  label: string;
  checked: boolean;
};

export type AuditLog = {
  id: string;
  caseId: string | null;
  userId: string;
  userName: string;
  action: AuditAction;
  description: string;
  metadata: Record<string, string>;
  createdAt: string;
};

export type TimelineEvent = {
  id: string;
  caseId: string;
  organizationId?: string;
  type?: string;
  title?: string;
  status: CaseStatus;
  label: string;
  description: string;
  severity?: TimelineSeverity;
  source?: TimelineSource;
  sourceMode?: SourceMode;
  actor: string;
  metadata?: Record<string, unknown>;
  createdAt: string;
};

export type CaseOperationSummary = {
  caseId: string;
  organizationId?: string;
  partiesCount: number;
  documentsCount: number;
  triageStatus: ModuleStatus;
  reportStatus: ReportStatus;
  riskLevel: RiskLevel;
  progress: number;
  latestEventAt: string | null;
  sourceMode: SourceMode;
  updatedAt: string;
};

export type CaseAggregate = {
  case: Case;
  request: LegalRequest | null;
  parties: Party[];
  documents: Document[];
  timeline: TimelineEvent[];
  triageModules: TriageModule[];
  providerResults: ProviderResult[];
  report: Report | null;
  summary: CaseOperationSummary;
};
