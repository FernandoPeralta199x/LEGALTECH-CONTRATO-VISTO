from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RequestStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    CASE_CREATED = "case_created"
    CANCELLED = "cancelled"
    FAILED = "failed"


class CaseStatus(StrEnum):
    DRAFT = "draft"
    CREATED = "created"
    DOCUMENT_ATTACHED = "document_attached"
    AWAITING_TRIAGE = "awaiting_triage"
    TRIAGE_RUNNING = "triage_running"
    TRIAGE_PARTIAL = "triage_partial"
    TRIAGE_COMPLETED = "triage_completed"
    AI_RUNNING = "ai_running"
    REPORT_READY = "report_ready"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    COMPLETED = "completed"
    FAILED = "failed"


class ModuleStatus(StrEnum):
    NOT_STARTED = "not_started"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PROVIDER_NOT_CONFIGURED = "provider_not_configured"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    AVAILABLE = "available"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    MISSING = "missing"


class ReportStatus(StrEnum):
    NOT_STARTED = "not_started"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class ProviderResultStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    NOT_CONFIGURED = "not_configured"
    SKIPPED = "skipped"


class SourceMode(StrEnum):
    LOCAL = "local"
    MOCK = "mock"
    SIMULATED = "simulated"
    REAL = "real"
    HYBRID = "hybrid"


class RiskLevel(StrEnum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TimelineSeverity(StrEnum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class TimelineSource(StrEnum):
    USER = "user"
    SYSTEM = "system"
    PROVIDER = "provider"
    AI = "ai"
    MOCK = "mock"


class ReportRecommendation(StrEnum):
    PROCEED = "proceed"
    PROCEED_WITH_CAUTION = "proceed_with_caution"
    DO_NOT_PROCEED = "do_not_proceed"
    HUMAN_REVIEW_REQUIRED = "human_review_required"


class ApiErrorSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ApiEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    data: Any | None
    error: ApiErrorSchema | None
    request_id: str
    source_mode: SourceMode
    timestamp: datetime


class PaginatedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[Any] = Field(default_factory=list)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    total: int = Field(default=0, ge=0)
    total_pages: int = Field(default=0, ge=0)


class LegalRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    code: str
    organization_id: UUID
    created_by: UUID
    product_type: str
    product_label: str
    title: str
    description: str = ""
    status: RequestStatus
    source_mode: SourceMode
    idempotency_key: str | None = None
    created_at: datetime
    updated_at: datetime


class CreateRequestPayloadSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_type: str
    product_label: str
    title: str
    description: str = ""
    source_mode: SourceMode = SourceMode.LOCAL
    idempotency_key: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None
    selected_modules: list[str] = Field(default_factory=list)
    parties: list["WizardPartyPayloadSchema"] = Field(default_factory=list)
    document: "WizardDocumentPayloadSchema | None" = None


class WizardPartyPayloadSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    document: str | None = None
    document_type: str = "unknown"
    person_type: str = "unknown"
    role: str
    email: str | None = None
    phone: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WizardDocumentPayloadSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str
    original_filename: str | None = None
    mime_type: str = "application/octet-stream"
    size_bytes: int = Field(default=0, ge=0)
    storage_provider: str = "local"
    storage_key: str | None = None
    status: DocumentStatus = DocumentStatus.UPLOADED
    preview_available: bool = False
    download_available: bool = False


class CaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    request_id: UUID | None = None
    code: str
    organization_id: UUID
    created_by: UUID
    product_type: str
    product_label: str
    title: str
    description: str = ""
    status: CaseStatus
    progress: int = Field(ge=0, le=100)
    risk_level: RiskLevel = RiskLevel.UNKNOWN
    recommendation: ReportRecommendation | None = None
    source_mode: SourceMode
    is_local_simulation: bool = False
    created_at: datetime
    updated_at: datetime


class CreateCasePayloadSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: UUID | None = None
    client_id: UUID | None = None
    case_type: str
    product_type: str
    product_label: str
    title: str
    description: str = ""
    priority: str = "normal"
    source_mode: SourceMode = SourceMode.LOCAL
    idempotency_key: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


def _digits(value: str | None) -> str:
    return "".join(ch for ch in value or "" if ch.isdigit())


def mask_document(value: str | None) -> str | None:
    digits = _digits(value)
    if not digits:
        return None

    if len(digits) <= 4:
        return "****"

    return f"{digits[:3]}****{digits[-2:]}"


class PartySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    case_id: UUID
    organization_id: UUID
    name: str
    document: str | None = Field(default=None, exclude=True)
    document_masked: str | None = None
    document_type: str = "unknown"
    person_type: str = "unknown"
    role: str
    email: str | None = None
    phone: str | None = None
    status: ModuleStatus = ModuleStatus.NOT_STARTED
    risk_level: RiskLevel = RiskLevel.UNKNOWN
    provider_status_summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def ensure_masked_document(self) -> PartySchema:
        raw_digits = _digits(self.document)
        masked_digits = _digits(self.document_masked)
        if raw_digits and (not masked_digits or masked_digits == raw_digits):
            self.document_masked = mask_document(self.document)
        return self


class DocumentSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    case_id: UUID
    organization_id: UUID
    filename: str
    original_filename: str
    mime_type: str
    size_bytes: int = Field(ge=0)
    storage_provider: str
    storage_key: str
    status: DocumentStatus
    ocr_status: ModuleStatus = ModuleStatus.NOT_STARTED
    ai_read_status: ModuleStatus = ModuleStatus.NOT_STARTED
    preview_available: bool = False
    download_available: bool = False
    uploaded_at: datetime | None = None
    updated_at: datetime


class TimelineEventSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    case_id: UUID
    organization_id: UUID
    type: str
    title: str
    description: str
    severity: TimelineSeverity
    source: TimelineSource
    source_mode: SourceMode
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class TriageModuleSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    case_id: UUID
    organization_id: UUID
    module_key: str
    module_label: str
    provider: str
    status: ModuleStatus
    source_mode: SourceMode
    required: bool
    reason: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    attempts: int = Field(default=0, ge=0)
    error_code: str | None = None
    error_message: str | None = None
    summary: str | None = None
    result_ref: str | None = None
    raw_result_ref: str | None = None
    created_at: datetime
    updated_at: datetime


class ProviderResultSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    case_id: UUID
    triage_module_id: UUID
    organization_id: UUID
    provider: str
    provider_request_id: str | None = None
    source_mode: SourceMode
    status: ProviderResultStatus
    input_hash: str
    raw_result_ref: str | None = None
    normalized_result: dict[str, Any] = Field(default_factory=dict)
    summary: str | None = None
    risk_signals: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0, le=1)
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class ReportSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    case_id: UUID
    organization_id: UUID
    status: ReportStatus
    version: int = Field(ge=1)
    summary: str
    findings: list[str] = Field(default_factory=list)
    legal_risks: list[str] = Field(default_factory=list)
    commercial_risks: list[str] = Field(default_factory=list)
    reputational_risks: list[str] = Field(default_factory=list)
    contractual_risks: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    recommendation: ReportRecommendation
    confidence: float | None = Field(default=None, ge=0, le=1)
    limitations: list[str] = Field(default_factory=list)
    source_refs: list[dict[str, Any] | str] = Field(default_factory=list)
    generated_by: str | None = None
    generated_at: datetime | None = None
    updated_at: datetime


class CaseOperationSummarySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: UUID
    organization_id: UUID
    parties_count: int = Field(ge=0)
    documents_count: int = Field(ge=0)
    triage_status: ModuleStatus
    report_status: ReportStatus
    risk_level: RiskLevel
    progress: int = Field(ge=0, le=100)
    latest_event_at: datetime | None = None
    source_mode: SourceMode
    updated_at: datetime


class CaseAggregateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case: CaseSchema
    request: LegalRequestSchema | None = None
    parties: list[PartySchema] = Field(default_factory=list)
    documents: list[DocumentSchema] = Field(default_factory=list)
    timeline: list[TimelineEventSchema] = Field(default_factory=list)
    triage_modules: list[TriageModuleSchema] = Field(default_factory=list)
    provider_results: list[ProviderResultSchema] = Field(default_factory=list)
    report: ReportSchema | None = None
    summary: CaseOperationSummarySchema
