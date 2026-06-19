import type { Client, ClientCreate, ClientUpdate } from "../../types";
import { maskDocumentForDisplay } from "../lib/clientForm";
import {
  createStoredLocalClient,
  findStoredLocalClient,
  getStoredLocalClients,
  updateStoredLocalClient
} from "../lib/localClients";
import { apiClient } from "./apiClient";
import { fallbackReason, shouldUseMockFallback, type ServiceResult } from "./fallback";

type BackendClient = {
  address?: string | null;
  birth_date?: string | null;
  cnpj?: string | null;
  company_name?: string | null;
  contract_role?: string | null;
  cpf?: string | null;
  id: string;
  display_name?: string | null;
  name: string;
  document: string | null;
  document_masked?: string | null;
  document_number?: string | null;
  document_type?: string | null;
  email: string | null;
  full_name?: string | null;
  legal_name?: string | null;
  phone: string | null;
  person_type?: string | null;
  rg?: string | null;
  risk_level?: string | null;
  source_mode?: string | null;
  status?: string | null;
  trade_name?: string | null;
  metadata: Record<string, unknown>;
  organization_id?: string | null;
  created_at: string;
  updated_at: string;
};

function metadataString(client: BackendClient, key: string): string | null {
  const value = client.metadata?.[key];
  return typeof value === "string" && value.trim() ? value : null;
}

function protectedDocumentLabel(client: BackendClient): string {
  return client.document_masked ?? maskDocumentForDisplay(client.document);
}

export function mapBackendClient(client: BackendClient): Client {
  const personType = client.person_type ?? metadataString(client, "person_type");
  const contractRole = client.contract_role ?? metadataString(client, "contract_role");
  const documentType = client.document_type ?? metadataString(client, "document_type");
  const documentMasked = client.document_masked ?? maskDocumentForDisplay(client.document);

  return {
    address: client.address ?? metadataString(client, "address"),
    birthDate: client.birth_date ?? metadataString(client, "birth_date"),
    cnpj: client.cnpj ?? metadataString(client, "cnpj"),
    companyName: client.company_name ?? metadataString(client, "company_name"),
    contractRole: contractRole as Client["contractRole"],
    cpf: client.cpf ?? metadataString(client, "cpf"),
    displayName: client.display_name ?? metadataString(client, "display_name") ?? client.name,
    document: client.document,
    documentLabel: protectedDocumentLabel(client),
    documentMasked,
    documentNumber: client.document_number ?? null,
    documentType: documentType as Client["documentType"],
    email: client.email ?? "",
    fullName: client.full_name ?? metadataString(client, "full_name"),
    id: client.id,
    legalName: client.legal_name ?? metadataString(client, "legal_name"),
    name: client.name,
    organizationId: client.organization_id ?? undefined,
    personType: personType as Client["personType"],
    phone: client.phone ?? "",
    rg: client.rg ?? metadataString(client, "rg"),
    status: (client.status ?? "active") as Client["status"],
    riskLevel: (client.risk_level ?? "low") as Client["riskLevel"],
    sourceMode: client.source_mode as Client["sourceMode"],
    casesCount: 0,
    metadata: client.metadata,
    tradeName: client.trade_name ?? metadataString(client, "trade_name"),
    createdAt: client.created_at,
    updatedAt: client.updated_at
  };
}

function makeMockClient(payload: ClientCreate): Client {
  return createStoredLocalClient(payload);
}

function sanitizeClientPayload<T extends ClientCreate | ClientUpdate>(
  payload: T
): T {
  const sanitized: Partial<ClientCreate> = {};

  if ("address" in payload) {
    sanitized.address = payload.address;
  }
  if ("birth_date" in payload) {
    sanitized.birth_date = payload.birth_date;
  }
  if ("cnpj" in payload) {
    sanitized.cnpj = payload.cnpj;
  }
  if ("company_name" in payload) {
    sanitized.company_name = payload.company_name;
  }
  if ("contract_role" in payload) {
    sanitized.contract_role = payload.contract_role;
  }
  if ("cpf" in payload) {
    sanitized.cpf = payload.cpf;
  }
  if ("display_name" in payload) {
    sanitized.display_name = payload.display_name;
  }
  if ("document_number" in payload) {
    sanitized.document_number = payload.document_number;
  }
  if ("document_type" in payload) {
    sanitized.document_type = payload.document_type;
  }
  if ("name" in payload) {
    sanitized.name = payload.name;
  }
  if ("full_name" in payload) {
    sanitized.full_name = payload.full_name;
  }
  if ("legal_name" in payload) {
    sanitized.legal_name = payload.legal_name;
  }
  if ("person_type" in payload) {
    sanitized.person_type = payload.person_type;
  }
  if ("document" in payload) {
    sanitized.document = payload.document;
  }
  if ("rg" in payload) {
    sanitized.rg = payload.rg;
  }
  if ("source_mode" in payload) {
    sanitized.source_mode = payload.source_mode;
  }
  if ("trade_name" in payload) {
    sanitized.trade_name = payload.trade_name;
  }
  if ("email" in payload) {
    sanitized.email = payload.email;
  }
  if ("phone" in payload) {
    sanitized.phone = payload.phone;
  }
  if ("metadata" in payload) {
    sanitized.metadata = payload.metadata;
  }

  return sanitized as T;
}

export async function listClients(): Promise<ServiceResult<Client[]>> {
  try {
    const response = await apiClient.get<BackendClient[]>("/api/v1/clients");
    return {
      data: response.success ? response.data.map(mapBackendClient) : [],
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    return {
      data: getStoredLocalClients(),
      fallbackReason: fallbackReason(error),
      source: "mock"
    };
  }
}

export async function createClient(
  payload: ClientCreate
): Promise<ServiceResult<Client>> {
  const safePayload = sanitizeClientPayload(payload);
  try {
    const response = await apiClient.post<BackendClient>(
      "/api/v1/clients",
      safePayload
    );
    return {
      data: mapBackendClient(response.data),
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    return {
      data: makeMockClient(safePayload),
      fallbackReason: fallbackReason(error),
      source: "mock"
    };
  }
}

export async function getClient(clientId: string): Promise<ServiceResult<Client>> {
  try {
    const response = await apiClient.get<BackendClient>(`/api/v1/clients/${clientId}`);
    return {
      data: mapBackendClient(response.data),
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    const localClient = findStoredLocalClient(clientId);
    if (!localClient) {
      throw error;
    }

    return {
      data: localClient,
      fallbackReason: fallbackReason(error),
      source: "mock"
    };
  }
}

export async function updateClient(
  clientId: string,
  payload: ClientUpdate
): Promise<ServiceResult<Client>> {
  const safePayload = sanitizeClientPayload(payload);
  try {
    const response = await apiClient.patch<BackendClient>(
      `/api/v1/clients/${clientId}`,
      safePayload
    );
    return {
      data: mapBackendClient(response.data),
      source: "api"
    };
  } catch (error) {
    if (!shouldUseMockFallback(error)) {
      throw error;
    }

    const localClient = updateStoredLocalClient(clientId, safePayload);
    if (!localClient) {
      throw error;
    }

    return {
      data: localClient,
      fallbackReason: fallbackReason(error),
      source: "mock"
    };
  }
}
