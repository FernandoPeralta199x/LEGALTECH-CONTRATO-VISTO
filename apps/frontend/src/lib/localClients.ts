import type { Client, ClientCreate, ClientUpdate } from "../../types";

import { maskDocumentForDisplay } from "./clientForm";

export const LOCAL_CLIENTS_STORAGE_KEY = "legaltech.local.clients.v1";

function getLocalStorage(): Storage | null {
  try {
    return typeof globalThis.localStorage === "undefined"
      ? null
      : globalThis.localStorage;
  } catch {
    return null;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function isStoredClient(value: unknown): value is Client {
  if (!isRecord(value)) return false;

  return (
    typeof value.id === "string" &&
    typeof value.name === "string" &&
    typeof value.documentLabel === "string" &&
    typeof value.email === "string" &&
    typeof value.phone === "string" &&
    typeof value.status === "string" &&
    typeof value.riskLevel === "string" &&
    typeof value.casesCount === "number" &&
    typeof value.createdAt === "string"
  );
}

function clean(value: string | null | undefined): string | null {
  const trimmed = value?.trim() ?? "";
  return trimmed ? trimmed : null;
}

function displayNameFromPayload(payload: ClientCreate | ClientUpdate): string {
  return (
    clean(payload.display_name) ??
    clean(payload.full_name) ??
    clean(payload.legal_name) ??
    clean(payload.company_name) ??
    clean(payload.name) ??
    "Cliente local"
  );
}

function documentFromPayload(payload: ClientCreate | ClientUpdate): string | null {
  return (
    clean(payload.document) ??
    clean(payload.document_number) ??
    clean(payload.cpf) ??
    clean(payload.cnpj) ??
    clean(payload.rg)
  );
}

function localClientFromPayload(
  payload: ClientCreate,
  now = new Date()
): Client {
  const nowIso = now.toISOString();
  const document = documentFromPayload(payload);
  const displayName = displayNameFromPayload(payload);

  return {
    address: payload.address,
    birthDate: payload.birth_date,
    casesCount: 0,
    cnpj: payload.cnpj,
    companyName: payload.company_name,
    contractRole: payload.contract_role,
    cpf: payload.cpf,
    createdAt: nowIso,
    displayName,
    document,
    documentLabel: maskDocumentForDisplay(document),
    documentMasked: maskDocumentForDisplay(document),
    documentNumber: payload.document_number ?? document,
    documentType: payload.document_type,
    email: payload.email ?? "",
    fullName: payload.full_name,
    id: `client-local-${now.getTime().toString(36)}`,
    legalName: payload.legal_name,
    metadata: {
      ...(payload.metadata ?? {}),
      localOnly: true,
      source: "clients_form_fallback",
      sourceMode: "local",
      syncStatus: "local_only"
    },
    name: displayName,
    organizationId: "local",
    personType: payload.person_type,
    phone: payload.phone ?? "",
    rg: payload.rg,
    riskLevel: "low",
    sourceMode: "local",
    status: "active",
    tradeName: payload.trade_name,
    updatedAt: nowIso
  };
}

function mergePayloadIntoClient(
  client: Client,
  payload: ClientUpdate,
  now = new Date()
): Client {
  const nextPersonType = payload.person_type ?? client.personType;
  const document = documentFromPayload(payload);
  const hasDocumentUpdate =
    "document" in payload ||
    "document_number" in payload ||
    "cpf" in payload ||
    "cnpj" in payload ||
    "rg" in payload;
  const nextDocument = hasDocumentUpdate ? document : client.document;
  const displayName = displayNameFromPayload({
    ...client,
    ...payload,
    name: payload.name ?? client.name
  } as ClientUpdate);

  return {
    ...client,
    address: "address" in payload ? payload.address : client.address,
    birthDate: "birth_date" in payload ? payload.birth_date : client.birthDate,
    cnpj:
      nextPersonType === "company"
        ? "cnpj" in payload
          ? payload.cnpj
          : client.cnpj
        : null,
    companyName: "company_name" in payload ? payload.company_name : client.companyName,
    contractRole: payload.contract_role ?? client.contractRole,
    cpf:
      nextPersonType === "individual"
        ? "cpf" in payload
          ? payload.cpf
          : client.cpf
        : null,
    displayName,
    document: nextDocument,
    documentLabel: maskDocumentForDisplay(nextDocument),
    documentMasked: maskDocumentForDisplay(nextDocument),
    documentNumber: hasDocumentUpdate ? payload.document_number ?? nextDocument : client.documentNumber,
    documentType: payload.document_type ?? client.documentType,
    email: "email" in payload ? payload.email ?? "" : client.email,
    fullName: "full_name" in payload ? payload.full_name : client.fullName,
    legalName: "legal_name" in payload ? payload.legal_name : client.legalName,
    metadata: {
      ...(client.metadata ?? {}),
      ...(payload.metadata ?? {}),
      localOnly: true,
      sourceMode: "local",
      syncStatus: "local_only"
    },
    name: displayName,
    personType: nextPersonType,
    phone: "phone" in payload ? payload.phone ?? "" : client.phone,
    rg:
      nextPersonType === "individual"
        ? "rg" in payload
          ? payload.rg
          : client.rg
        : null,
    sourceMode: "local",
    tradeName: "trade_name" in payload ? payload.trade_name : client.tradeName,
    updatedAt: now.toISOString()
  };
}

function dedupeClients(clients: Client[]): Client[] {
  const seen = new Set<string>();
  const result: Client[] = [];

  clients.forEach((client) => {
    if (seen.has(client.id)) return;
    seen.add(client.id);
    result.push(client);
  });

  return result;
}

export function getStoredLocalClients(): Client[] {
  const storage = getLocalStorage();
  if (!storage) return [];

  try {
    const raw = storage.getItem(LOCAL_CLIENTS_STORAGE_KEY);
    if (!raw) return [];

    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? parsed.filter(isStoredClient) : [];
  } catch {
    return [];
  }
}

export function saveStoredLocalClient(client: Client): Client {
  const storage = getLocalStorage();
  if (!storage) return client;

  const next = dedupeClients([
    client,
    ...getStoredLocalClients().filter((stored) => stored.id !== client.id)
  ]);
  storage.setItem(LOCAL_CLIENTS_STORAGE_KEY, JSON.stringify(next));
  return client;
}

export function findStoredLocalClient(clientId: string): Client | undefined {
  return getStoredLocalClients().find((client) => client.id === clientId);
}

export function createStoredLocalClient(payload: ClientCreate): Client {
  return saveStoredLocalClient(localClientFromPayload(payload));
}

export function updateStoredLocalClient(
  clientId: string,
  payload: ClientUpdate
): Client | null {
  const current = getStoredLocalClients().find((client) => client.id === clientId);
  if (!current) return null;

  return saveStoredLocalClient(mergePayloadIntoClient(current, payload));
}
