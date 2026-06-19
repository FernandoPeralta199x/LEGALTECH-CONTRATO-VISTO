"use client";

import {
  mockAgentExecutions,
  mockAuditLogs,
  mockCases,
  mockClients,
  mockDocuments,
  mockReports,
  mockReviews,
  mockTimeline,
  mockUsers
} from "@/lib/mockData";
import type {
  AgentExecution,
  AuditLog,
  Case,
  Client,
  Document,
  Report,
  Review,
  TimelineEvent,
  User
} from "@/types";

const DELAY_MS = 600;

function delay(ms = DELAY_MS): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ─── GET /api/v1/me ────────────────────────────────────────────────────────────

export async function getMe(): Promise<User> {
  await delay();
  return mockUsers[0];
}

// ─── GET /api/v1/clients ───────────────────────────────────────────────────────

export async function getClients(): Promise<Client[]> {
  await delay();
  return mockClients;
}

// ─── POST /api/v1/clients ──────────────────────────────────────────────────────

export async function createClient(data: Partial<Client>): Promise<Client> {
  await delay();
  return {
    id: `client-${Date.now()}`,
    name: data.name ?? "Novo Cliente",
    documentLabel: "Documento protegido",
    email: data.email ?? "",
    phone: data.phone ?? "",
    status: "active",
    riskLevel: "low",
    casesCount: 0,
    organizationId: "org-001",
    createdAt: new Date().toISOString()
  };
}

// ─── GET /api/v1/cases ─────────────────────────────────────────────────────────

export async function getCases(): Promise<Case[]> {
  await delay();
  return mockCases;
}

// ─── POST /api/v1/cases ────────────────────────────────────────────────────────

export async function createCase(data: Partial<Case>): Promise<Case> {
  await delay();
  return {
    id: `case-${Date.now()}`,
    code: `CASO-2026-00${mockCases.length + 1}`,
    clientId: data.clientId ?? "client-001",
    clientName: data.clientName ?? "Cliente",
    caseType: data.caseType ?? "outro",
    product: data.product ?? "analise_contratual",
    status: "draft",
    priority: data.priority ?? "normal",
    documentsCount: 0,
    progressPercent: 5,
    assignedTo: null,
    notes: data.notes ?? "",
    parties: [],
    updatedAt: new Date().toISOString(),
    createdAt: new Date().toISOString(),
    submittedAt: null
  };
}

// ─── GET /api/v1/cases/:id ─────────────────────────────────────────────────────

export async function getCase(caseId: string): Promise<Case> {
  await delay();
  const found = mockCases.find((c) => c.id === caseId);
  if (!found) throw new Error(`Caso ${caseId} não encontrado.`);
  return found;
}

// ─── PATCH /api/v1/cases/:id ───────────────────────────────────────────────────

export async function updateCase(caseId: string, data: Partial<Case>): Promise<Case> {
  await delay();
  const found = mockCases.find((c) => c.id === caseId);
  if (!found) throw new Error(`Caso ${caseId} não encontrado.`);
  return { ...found, ...data, updatedAt: new Date().toISOString() };
}

// ─── POST /api/v1/cases/:id/submit ────────────────────────────────────────────

export async function submitCase(caseId: string): Promise<Case> {
  await delay(800);
  const found = mockCases.find((c) => c.id === caseId);
  if (!found) throw new Error(`Caso ${caseId} não encontrado.`);
  return {
    ...found,
    status: "submitted",
    submittedAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };
}

// ─── GET /api/v1/cases/:id/timeline ───────────────────────────────────────────

export async function getCaseTimeline(caseId: string): Promise<TimelineEvent[]> {
  await delay();
  return mockTimeline.filter((t) => t.caseId === caseId);
}

// ─── GET /api/v1/cases/:id/status ─────────────────────────────────────────────

export async function getCaseStatus(caseId: string): Promise<{ status: string; progressPercent: number }> {
  await delay();
  const found = mockCases.find((c) => c.id === caseId);
  if (!found) throw new Error(`Caso ${caseId} não encontrado.`);
  return { status: found.status, progressPercent: found.progressPercent };
}

// ─── POST /api/v1/cases/:id/documents/presigned-upload ────────────────────────

export async function getPresignedUploadUrl(
  caseId: string,
  filename: string
): Promise<{ uploadUrl: string; documentId: string }> {
  await delay();
  return {
    uploadUrl: `https://mock-s3-upload.example.test/${caseId}/${filename}`,
    documentId: `doc-${Date.now()}`
  };
}

// ─── POST /api/v1/cases/:id/documents/confirm-upload ─────────────────────────

export async function confirmUpload(
  caseId: string,
  documentId: string
): Promise<Document> {
  await delay();
  return {
    id: documentId,
    filename: "arquivo-enviado.pdf",
    caseId,
    caseCode: "CASO-2026-001",
    contentType: "application/pdf",
    status: "uploaded",
    sizeLabel: "1.2 MB",
    uploadedAt: new Date().toISOString(),
    processedAt: null,
    notes: ""
  };
}

// ─── GET /api/v1/cases/:id/documents ──────────────────────────────────────────

export async function getCaseDocuments(caseId: string): Promise<Document[]> {
  await delay();
  return mockDocuments.filter((d) => d.caseId === caseId);
}

// ─── GET /api/v1/cases/:id/agents/executions ──────────────────────────────────

export async function getCaseAgentExecutions(caseId: string): Promise<AgentExecution[]> {
  await delay();
  return mockAgentExecutions.filter((e) => e.caseId === caseId);
}

// ─── GET /api/v1/cases/:id/reports ────────────────────────────────────────────

export async function getCaseReports(caseId: string): Promise<Report[]> {
  await delay();
  return mockReports.filter((r) => r.caseId === caseId);
}

// ─── GET /api/v1/reports ──────────────────────────────────────────────────────

export async function getReports(): Promise<Report[]> {
  await delay();
  return mockReports;
}

// ─── GET /api/v1/reviews (analista) ───────────────────────────────────────────

export async function getPendingReviews(): Promise<Review[]> {
  await delay();
  return mockReviews.filter((r) => r.status === "pending");
}

// ─── POST /api/v1/reviews/:id/approve ─────────────────────────────────────────

export async function approveReview(reviewId: string): Promise<Review> {
  await delay(800);
  const found = mockReviews.find((r) => r.id === reviewId);
  if (!found) throw new Error(`Revisão ${reviewId} não encontrada.`);
  return { ...found, status: "approved", reviewedAt: new Date().toISOString() };
}

// ─── POST /api/v1/reviews/:id/reject ──────────────────────────────────────────

export async function rejectReview(reviewId: string, reason: string): Promise<Review> {
  await delay(800);
  const found = mockReviews.find((r) => r.id === reviewId);
  if (!found) throw new Error(`Revisão ${reviewId} não encontrada.`);
  return {
    ...found,
    status: "rejected",
    observations: reason,
    reviewedAt: new Date().toISOString()
  };
}

// ─── POST /api/v1/reviews/:id/request-adjustment ──────────────────────────────

export async function requestAdjustment(
  reviewId: string,
  observations: string
): Promise<Review> {
  await delay(800);
  const found = mockReviews.find((r) => r.id === reviewId);
  if (!found) throw new Error(`Revisão ${reviewId} não encontrada.`);
  return {
    ...found,
    status: "adjustment_requested",
    observations,
    reviewedAt: new Date().toISOString()
  };
}

// ─── GET /api/v1/audit-logs ───────────────────────────────────────────────────

export async function getAuditLogs(): Promise<AuditLog[]> {
  await delay();
  return mockAuditLogs;
}
