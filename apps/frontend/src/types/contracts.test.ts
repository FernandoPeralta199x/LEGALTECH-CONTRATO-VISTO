import assert from "node:assert/strict";
import test from "node:test";

import type {
  ApiResponse,
  CaseAggregate,
  CaseListFilters,
  PaginatedResponse
} from "../../types";
import {
  CASE_STATUS_VALUES,
  DOCUMENT_STATUS_VALUES,
  MODULE_STATUS_VALUES,
  PROVIDER_RESULT_STATUS_VALUES,
  REPORT_STATUS_VALUES,
  REQUEST_STATUS_VALUES,
  RISK_LEVEL_VALUES,
  SOURCE_MODE_VALUES
} from "../../types";

test("exports canonical multi-request enum values", () => {
  assert.deepEqual([...REQUEST_STATUS_VALUES], [
    "draft",
    "submitted",
    "case_created",
    "cancelled",
    "failed"
  ]);
  assert.equal(CASE_STATUS_VALUES.includes("awaiting_triage"), true);
  assert.equal(MODULE_STATUS_VALUES.includes("provider_not_configured"), true);
  assert.equal(DOCUMENT_STATUS_VALUES.includes("available"), true);
  assert.equal(REPORT_STATUS_VALUES.includes("ready"), true);
  assert.equal(PROVIDER_RESULT_STATUS_VALUES.includes("not_configured"), true);
  assert.equal(SOURCE_MODE_VALUES.includes("hybrid"), true);
  assert.equal(RISK_LEVEL_VALUES.includes("critical"), true);
});

test("ApiResponse success and error envelopes carry observability fields", () => {
  const success: ApiResponse<{ id: string }> = {
    success: true,
    data: { id: "case-1" },
    error: null,
    request_id: "req-1",
    source_mode: "local",
    timestamp: "2026-06-11T10:00:00.000Z"
  };

  const failure: ApiResponse<never> = {
    success: false,
    data: null,
    error: {
      code: "NOT_FOUND",
      details: {},
      message: "Caso nao encontrado."
    },
    request_id: "req-2",
    source_mode: "real",
    timestamp: "2026-06-11T10:00:00.000Z"
  };

  assert.equal(success.error, null);
  assert.equal(failure.data, null);
  assert.equal(failure.error.code, "NOT_FOUND");
});

test("PaginatedResponse and CaseListFilters support list contracts", () => {
  const filters: CaseListFilters = {
    page: 2,
    pageSize: 10,
    productType: "analise_contratual",
    q: "CASO",
    riskLevel: "unknown",
    sortBy: "updated_at",
    sortOrder: "desc",
    status: "created"
  };

  const page: PaginatedResponse<{ id: string }> = {
    items: [{ id: "case-1" }],
    page: filters.page ?? 1,
    page_size: filters.pageSize ?? 20,
    total: 1,
    total_pages: 1
  };

  assert.equal(page.items[0].id, "case-1");
  assert.equal(filters.status, "created");
});

test("CaseAggregate keeps operational data isolated by case id", () => {
  const aggregate: CaseAggregate = {
    case: {
      assignedTo: null,
      caseType: "contract_analysis",
      clientId: "client-1",
      clientName: "Cliente demonstrativo",
      code: "CASO-1",
      createdAt: "2026-06-11T10:00:00.000Z",
      createdBy: "user-1",
      documentsCount: 0,
      id: "case-1",
      isLocalSimulation: true,
      notes: "",
      organizationId: "org-1",
      parties: [],
      priority: "normal",
      product: "analise_contratual",
      productLabel: "Analise contratual",
      productType: "analise_contratual",
      progress: 0,
      progressPercent: 0,
      requestId: "request-1",
      riskLevel: "unknown",
      sourceMode: "local",
      status: "created",
      submittedAt: null,
      updatedAt: "2026-06-11T10:00:00.000Z"
    },
    documents: [],
    parties: [],
    providerResults: [],
    report: null,
    request: {
      code: "PED-1",
      createdAt: "2026-06-11T10:00:00.000Z",
      createdBy: "user-1",
      description: "",
      id: "request-1",
      idempotencyKey: null,
      organizationId: "org-1",
      productLabel: "Analise contratual",
      productType: "analise_contratual",
      sourceMode: "local",
      status: "case_created",
      title: "Pedido demonstrativo",
      updatedAt: "2026-06-11T10:00:00.000Z"
    },
    summary: {
      caseId: "case-1",
      documentsCount: 0,
      latestEventAt: null,
      organizationId: "org-1",
      partiesCount: 0,
      progress: 0,
      reportStatus: "not_started",
      riskLevel: "unknown",
      sourceMode: "local",
      triageStatus: "not_started",
      updatedAt: "2026-06-11T10:00:00.000Z"
    },
    timeline: [],
    triageModules: []
  };

  assert.equal(aggregate.case.id, aggregate.summary.caseId);
  assert.equal(aggregate.case.organizationId, aggregate.request?.organizationId);
});
