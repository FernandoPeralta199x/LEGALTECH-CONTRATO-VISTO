import { mockParties } from "../../lib/mockData";
import type { CaseParty, CasePartyCreate, CasePartyUpdate } from "../../types";
import { apiClient } from "./apiClient";
import { fallbackReason, shouldUseMockFallback, type ServiceResult } from "./fallback";

type BackendCaseParty = {
  id: string;
  case_id: string;
  party_type: string;
  name: string;
  document: string | null;
  email: string | null;
  phone: string | null;
  notes: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

function sanitizeCasePartyPayload<T extends CasePartyCreate | CasePartyUpdate>(
  payload: T
): T {
  const sanitized: Partial<CasePartyCreate> = {};

  if ("party_type" in payload) {
    sanitized.party_type = payload.party_type;
  }
  if ("name" in payload) {
    sanitized.name = payload.name;
  }
  if ("document" in payload) {
    sanitized.document = payload.document;
  }
  if ("email" in payload) {
    sanitized.email = payload.email;
  }
  if ("phone" in payload) {
    sanitized.phone = payload.phone;
  }
  if ("notes" in payload) {
    sanitized.notes = payload.notes;
  }
  if ("metadata" in payload) {
    sanitized.metadata = payload.metadata;
  }

  return sanitized as T;
}

function makeMockCaseParty(caseId: string, payload: CasePartyCreate): CaseParty {
  const now = new Date().toISOString();
  return {
    id: `party-local-${Date.now()}`,
    caseId,
    name: payload.name,
    document: payload.document ?? "",
    type: payload.party_type,
    email: payload.email ?? "",
    phone: payload.phone ?? "",
    notes: payload.notes ?? "",
    metadata: payload.metadata ?? { source: "frontend_mock_fallback" },
    createdAt: now,
    updatedAt: now
  };
}

export function mapBackendCaseParty(party: BackendCaseParty): CaseParty {
  return {
    id: party.id,
    caseId: party.case_id,
    name: party.name,
    document: party.document ?? "",
    type: party.party_type,
    email: party.email ?? "",
    phone: party.phone ?? "",
    notes: party.notes ?? "",
    metadata: party.metadata,
    createdAt: party.created_at,
    updatedAt: party.updated_at
  };
}

export async function listCaseParties(
  caseId: string
): Promise<ServiceResult<CaseParty[]>> {
  try {
    const response = await apiClient.get<BackendCaseParty[]>(
      `/api/v1/cases/${caseId}/parties`
    );
    return {
      data: response.data.map(mapBackendCaseParty),
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    return {
      data: mockParties.filter((party) => party.caseId === caseId),
      fallbackReason: fallbackReason(error),
      source: "mock"
    };
  }
}

export async function createCaseParty(
  caseId: string,
  payload: CasePartyCreate
): Promise<ServiceResult<CaseParty>> {
  const safePayload = sanitizeCasePartyPayload(payload);
  try {
    const response = await apiClient.post<BackendCaseParty>(
      `/api/v1/cases/${caseId}/parties`,
      safePayload
    );
    return {
      data: mapBackendCaseParty(response.data),
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    return {
      data: makeMockCaseParty(caseId, safePayload),
      fallbackReason: fallbackReason(error),
      source: "mock"
    };
  }
}

export async function updateCaseParty(
  caseId: string,
  partyId: string,
  payload: CasePartyUpdate
): Promise<ServiceResult<CaseParty>> {
  const safePayload = sanitizeCasePartyPayload(payload);
  try {
    const response = await apiClient.patch<BackendCaseParty>(
      `/api/v1/cases/${caseId}/parties/${partyId}`,
      safePayload
    );
    return {
      data: mapBackendCaseParty(response.data),
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    const current =
      mockParties.find((party) => party.caseId === caseId && party.id === partyId) ??
      mockParties.find((party) => party.caseId === caseId) ??
      makeMockCaseParty(caseId, {
        name: safePayload.name ?? "Parte local",
        party_type: safePayload.party_type ?? "outro"
      });

    return {
      data: {
        ...current,
        name: safePayload.name ?? current.name,
        document: safePayload.document ?? current.document,
        type: safePayload.party_type ?? current.type,
        email: safePayload.email ?? current.email,
        phone: safePayload.phone ?? current.phone,
        notes: safePayload.notes ?? current.notes,
        metadata: safePayload.metadata ?? current.metadata,
        updatedAt: new Date().toISOString()
      },
      fallbackReason: fallbackReason(error),
      source: "mock"
    };
  }
}
