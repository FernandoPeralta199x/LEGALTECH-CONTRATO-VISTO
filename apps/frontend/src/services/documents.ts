import type { Document, DocumentCreate, DocumentUpdate } from "../../types";
import { apiClient, resolveApiBaseUrl } from "./apiClient";
import { fallbackReason, shouldUseMockFallback, type ServiceResult } from "./fallback";

type BackendDocument = {
  id: string;
  case_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  file_hash: string | null;
  status: string;
  uploaded_by: string | null;
  uploaded_at: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type DocumentDownloadUrl = {
  expires_in_seconds: number;
  method: string;
  url: string;
};

export type EnqueueProcessingResult = {
  document_id: string;
  job_id: string;
  queue_backend: string;
  status: string;
};

export type DocumentUploadPayload = {
  caseId: string;
  file: File;
  metadata?: Record<string, unknown>;
};

const AUTHORITATIVE_METADATA_FIELDS = new Set([
  "organization_id",
  "tenant_id",
  "storage_bucket",
  "storage_key",
  "uploaded_by"
]);

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${Math.round(bytes / 1024)} KB`;
  }

  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function caseCodeFromId(caseId: string): string {
  if (caseId.toLowerCase().startsWith("case-")) {
    return caseId.replace(/^case-/i, "CASE-").toUpperCase();
  }

  return `CASO-${caseId.slice(0, 8).toUpperCase()}`;
}

export function mapBackendDocument(document: BackendDocument): Document {
  return {
    id: document.id,
    filename: document.filename,
    caseId: document.case_id,
    caseCode: caseCodeFromId(document.case_id),
    contentType: document.content_type,
    status: document.status as Document["status"],
    sizeBytes: document.size_bytes,
    sizeLabel: formatBytes(document.size_bytes),
    fileHash: document.file_hash,
    uploadedAt: document.uploaded_at ?? document.created_at,
    processedAt: document.status === "processed" ? document.updated_at : null,
    metadata: document.metadata,
    notes:
      typeof document.metadata.notes === "string"
        ? document.metadata.notes
        : ""
  };
}

function makeMockDocument(payload: DocumentCreate): Document {
  const now = new Date().toISOString();

  return {
    id: `doc-local-${Date.now()}`,
    filename: payload.filename,
    caseId: payload.case_id,
    caseCode: caseCodeFromId(payload.case_id),
    contentType: payload.content_type,
    status: payload.status ?? "pending_upload",
    sizeBytes: payload.size_bytes,
    sizeLabel: formatBytes(payload.size_bytes),
    fileHash: payload.file_hash ?? null,
    uploadedAt: now,
    processedAt: null,
    metadata: payload.metadata ?? { source: "frontend_mock_fallback" },
    notes:
      typeof payload.metadata?.notes === "string"
        ? payload.metadata.notes
        : ""
  };
}

function safeUploadMetadata(
  metadata: Record<string, unknown> | undefined
): Record<string, unknown> {
  if (!metadata) {
    return {};
  }

  return Object.fromEntries(
    Object.entries(metadata).filter(
      ([key, value]) =>
        !AUTHORITATIVE_METADATA_FIELDS.has(key) && value !== undefined
    )
  );
}

export async function listDocuments(
  params: { caseId?: string; status?: string } = {}
): Promise<ServiceResult<Document[]>> {
  try {
    const search = new URLSearchParams();
    if (params.caseId) {
      search.set("case_id", params.caseId);
    }
    if (params.status) {
      search.set("status", params.status);
    }

    const query = search.toString();
    const response = await apiClient.get<BackendDocument[]>(
      `/api/v1/documents${query ? `?${query}` : ""}`
    );

    return {
      data: response.data.map(mapBackendDocument),
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    return {
      data: [],
      fallbackReason: fallbackReason(error),
      source: "mock"
    };
  }
}

export async function createDocument(
  payload: DocumentCreate
): Promise<ServiceResult<Document>> {
  try {
    const response = await apiClient.post<BackendDocument>("/api/v1/documents", payload);
    return {
      data: mapBackendDocument(response.data),
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    return {
      data: makeMockDocument(payload),
      fallbackReason: fallbackReason(error),
      source: "mock"
    };
  }
}

export async function uploadDocument(
  payload: DocumentUploadPayload
): Promise<ServiceResult<Document>> {
  const formData = new FormData();
  const metadata = safeUploadMetadata(payload.metadata);

  formData.set("case_id", payload.caseId);
  formData.set("file", payload.file);
  if (Object.keys(metadata).length > 0) {
    formData.set("metadata", JSON.stringify(metadata));
  }

  const response = await apiClient.postForm<BackendDocument>(
    "/api/v1/documents/upload",
    formData
  );

  return {
    data: mapBackendDocument(response.data),
    source: "api"
  };
}

export async function getDocument(
  documentId: string
): Promise<ServiceResult<Document>> {
  try {
    const response = await apiClient.get<BackendDocument>(
      `/api/v1/documents/${documentId}`
    );
    return {
      data: mapBackendDocument(response.data),
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    throw error;
  }
}

export async function updateDocument(
  documentId: string,
  payload: DocumentUpdate
): Promise<ServiceResult<Document>> {
  try {
    const response = await apiClient.patch<BackendDocument>(
      `/api/v1/documents/${documentId}`,
      payload
    );
    return {
      data: mapBackendDocument(response.data),
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    throw error;
  }
}

export async function getDocumentDownloadUrl(
  documentId: string
): Promise<ServiceResult<DocumentDownloadUrl>> {
  try {
    const response = await apiClient.get<DocumentDownloadUrl>(
      `/api/v1/documents/${documentId}/download-url`
    );
    return {
      data: response.data,
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    return {
      data: {
        expires_in_seconds: 900,
        method: "GET",
        url: `${resolveApiBaseUrl()}/mock-download-unavailable`
      },
      fallbackReason: fallbackReason(error),
      source: "mock"
    };
  }
}

export async function enqueueDocumentProcessing(
  documentId: string
): Promise<ServiceResult<EnqueueProcessingResult>> {
  try {
    const response = await apiClient.post<EnqueueProcessingResult>(
      `/api/v1/documents/${documentId}/enqueue-processing`,
      {}
    );
    return {
      data: response.data,
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    return {
      data: {
        document_id: documentId,
        job_id: `job-local-${Date.now()}`,
        queue_backend: "mock",
        status: "queued"
      },
      fallbackReason: fallbackReason(error),
      source: "mock"
    };
  }
}
