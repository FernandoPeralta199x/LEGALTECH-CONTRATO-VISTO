import { MODULOS, PRODUTOS, type Modulo } from "../../lib/produtoConfig";
import type { Case, CaseParty, CaseStatus, Priority, ProductType } from "../../types";

export const LOCAL_CASES_STORAGE_KEY = "legaltech.local.cases.v1";

type WizardPartySummary = {
  documento?: string;
  email?: string;
  id: string;
  nome: string;
  papel: string;
  telefone?: string;
  tipoPessoa?: "pf" | "pj";
};

type WizardFileSummary = {
  name?: string;
  progress?: number;
  size?: number;
  status: string;
  type?: string;
} | null;

export type LocalCaseWizardInput = {
  arquivo: WizardFileSummary;
  modulos: Record<Modulo, boolean>;
  parties: WizardPartySummary[];
  produto: ProductType;
};

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

function isStoredCase(value: unknown): value is Case {
  if (!isRecord(value)) return false;

  return (
    typeof value.id === "string" &&
    typeof value.code === "string" &&
    typeof value.clientId === "string" &&
    typeof value.clientName === "string" &&
    typeof value.caseType === "string" &&
    typeof value.product === "string" &&
    typeof value.status === "string" &&
    typeof value.priority === "string" &&
    typeof value.documentsCount === "number" &&
    typeof value.progressPercent === "number" &&
    typeof value.notes === "string" &&
    Array.isArray(value.parties) &&
    typeof value.updatedAt === "string" &&
    typeof value.createdAt === "string" &&
    (typeof value.submittedAt === "string" || value.submittedAt === null)
  );
}

function selectedModules(modulos: Record<Modulo, boolean>): Modulo[] {
  return (Object.keys(MODULOS) as Modulo[]).filter((modulo) => modulos[modulo]);
}

function caseTypeForProduct(product: ProductType): string {
  const map: Record<ProductType, string> = {
    analise_contratual: "contract_analysis",
    consulta_objeto: "outro",
    dados_partes: "due_diligence",
    reuniao_equipe: "outro"
  };

  return map[product];
}

function normalizeIdPart(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(-12);
}

function makeLocalCaseCode(now: Date): string {
  return `CASO-LOCAL-${now.getTime().toString().slice(-6)}`;
}

function makeLocalCaseId(now: Date, partyId: string): string {
  const timestamp = now.getTime().toString(36);
  const suffix = normalizeIdPart(partyId) || "wizard";
  return `case-local-${timestamp}-${suffix}`;
}

function calculateOperationalFallbackProgress({
  documentReady,
  modulesCount,
  partiesCount
}: {
  documentReady: boolean;
  modulesCount: number;
  partiesCount: number;
}): number {
  // Formula local: request/case (10) + partes (10) + documento (10) + timeline (5) + plano de triagem (5).
  return Math.min(
    40,
    10 +
      (partiesCount > 0 ? 10 : 0) +
      (documentReady ? 10 : 0) +
      (documentReady || partiesCount > 0 || modulesCount > 0 ? 5 : 0) +
      (modulesCount > 0 ? 5 : 0)
  );
}

function maskDocument(value: string | undefined): string {
  const digits = (value ?? "").replace(/\D/g, "");
  if (!digits) return "";
  if (digits.length <= 4) return "****";

  const prefix = digits.slice(0, 3);
  const suffix = digits.slice(-2);
  return `${prefix}****${suffix}`;
}

function dedupeCases(cases: Case[]): Case[] {
  const seen = new Set<string>();
  const result: Case[] = [];

  cases.forEach((legalCase) => {
    const keys = [legalCase.id, legalCase.code].filter(Boolean);
    if (keys.some((key) => seen.has(key))) {
      return;
    }

    keys.forEach((key) => seen.add(key));
    result.push(legalCase);
  });

  return result;
}

export function getStoredLocalCases(): Case[] {
  const storage = getLocalStorage();
  if (!storage) return [];

  try {
    const raw = storage.getItem(LOCAL_CASES_STORAGE_KEY);
    if (!raw) return [];

    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? parsed.filter(isStoredCase) : [];
  } catch {
    return [];
  }
}

export function saveStoredLocalCase(legalCase: Case): Case {
  const storage = getLocalStorage();
  if (!storage) return legalCase;

  const next = dedupeCases([
    legalCase,
    ...getStoredLocalCases().filter(
      (storedCase) =>
        storedCase.id !== legalCase.id && storedCase.code !== legalCase.code
    )
  ]);

  storage.setItem(LOCAL_CASES_STORAGE_KEY, JSON.stringify(next));
  return legalCase;
}

export function findStoredLocalCase(caseId: string): Case | undefined {
  return getStoredLocalCases().find(
    (legalCase) => legalCase.id === caseId || legalCase.code === caseId
  );
}

export function isLocalOnlyCase(legalCase: Case): boolean {
  return (
    legalCase.id.startsWith("case-local-") ||
    legalCase.metadata?.origin === "local" ||
    legalCase.metadata?.syncStatus === "local_only"
  );
}

export function mergeCasesWithLocalCases(cases: Case[]): Case[] {
  return dedupeCases([...getStoredLocalCases(), ...cases]);
}

export function createLocalCaseFromWizard(
  input: LocalCaseWizardInput,
  now = new Date()
): Case {
  const primaryParty = input.parties.find((party) => party.nome.trim()) ?? input.parties[0];
  const clientName = primaryParty?.nome.trim() || "Cliente local";
  const product = input.produto;
  const activeModules = selectedModules(input.modulos);
  const productName = PRODUTOS[product].titulo;
  const nowIso = now.toISOString();
  const title = `${productName} - ${clientName}`;
  const caseId = makeLocalCaseId(now, primaryParty?.id ?? "wizard");
  const documentReady = input.arquivo?.status === "done";
  const status: CaseStatus =
    activeModules.length > 0
      ? "awaiting_triage"
      : documentReady
        ? "document_attached"
        : "created";
  const parties: CaseParty[] = input.parties
    .filter((party) => party.nome.trim())
    .map((party) => ({
      id: `${caseId}-${normalizeIdPart(party.id) || "party"}`,
      caseId,
      organizationId: "local",
      name: party.nome.trim(),
      document: "",
      documentMasked: maskDocument(party.documento),
      documentType: party.tipoPessoa === "pj" ? "cnpj" : "cpf",
      personType: party.tipoPessoa === "pj" ? "company" : "individual",
      type: party.papel,
      email: "",
      phone: "",
      notes: "",
      status: "not_started",
      riskLevel: "unknown",
      providerStatusSummary: null,
      metadata: {
        role: party.papel,
        source: "new_case_wizard",
        wizardPartyId: party.id
      },
      createdAt: nowIso,
      updatedAt: nowIso
    }));
  const progress = calculateOperationalFallbackProgress({
    documentReady,
    modulesCount: activeModules.length,
    partiesCount: parties.length
  });

  return {
    id: caseId,
    code: makeLocalCaseCode(now),
    organizationId: "local",
    clientId: primaryParty?.id ?? "local-client",
    clientName,
    caseType: caseTypeForProduct(product),
    product,
    productLabel: productName,
    status,
    priority: "normal" satisfies Priority,
    documentsCount: documentReady ? 1 : 0,
    progressPercent: progress,
    progress,
    riskLevel: "unknown",
    sourceMode: "local",
    isLocalSimulation: true,
    assignedTo: null,
    notes: "Fallback local explícito do fluxo Novo Pedido. Backend indisponível no momento da criação.",
    metadata: {
      modules: activeModules,
      moduleNames: activeModules.map((modulo) => MODULOS[modulo].titulo),
      origin: "local",
      product,
      productName,
      source: "new_case_wizard",
      sourceMode: "local",
      syncStatus: "local_only",
      title,
      wizardDocument: input.arquivo
        ? {
            filename: input.arquivo.name ?? "documento-local",
            mimeType: input.arquivo.type ?? "application/octet-stream",
            sizeBytes: input.arquivo.size ?? 0,
            sourceMode: "local",
            storageProvider: "local"
          }
        : null
    },
    parties,
    updatedAt: nowIso,
    createdAt: nowIso,
    submittedAt: nowIso
  };
}

export function saveLocalCaseFromWizard(input: LocalCaseWizardInput): Case {
  return saveStoredLocalCase(createLocalCaseFromWizard(input));
}
