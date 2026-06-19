import assert from "node:assert/strict";
import test from "node:test";

import type { Case } from "../../types";
import {
  LOCAL_CASES_STORAGE_KEY,
  createLocalCaseFromWizard,
  findStoredLocalCase,
  getStoredLocalCases,
  isLocalOnlyCase,
  mergeCasesWithLocalCases,
  saveStoredLocalCase
} from "./localCases";

class MemoryStorage {
  private values = new Map<string, string>();

  clear() {
    this.values.clear();
  }

  getItem(key: string) {
    return this.values.get(key) ?? null;
  }

  removeItem(key: string) {
    this.values.delete(key);
  }

  setItem(key: string, value: string) {
    this.values.set(key, value);
  }
}

const storage = new MemoryStorage();
Object.defineProperty(globalThis, "localStorage", {
  configurable: true,
  value: storage
});

function makeCase(overrides: Partial<Case> = {}): Case {
  return {
    id: "case-local-test",
    code: "CASO-LOCAL-TEST",
    clientId: "party-1",
    clientName: "Cliente Local",
    caseType: "contract_analysis",
    product: "analise_contratual",
    status: "submitted",
    priority: "normal",
    documentsCount: 1,
    progressPercent: 15,
    assignedTo: null,
    notes: "Fallback local explícito do fluxo Novo Pedido. Backend indisponível no momento da criação.",
    metadata: {
      origin: "local",
      source: "new_case_wizard",
      syncStatus: "local_only"
    },
    parties: [],
    updatedAt: "2026-06-01T10:00:00.000Z",
    createdAt: "2026-06-01T10:00:00.000Z",
    submittedAt: "2026-06-01T10:00:00.000Z",
    ...overrides
  };
}

test("createLocalCaseFromWizard builds a minimal local case without sensitive party data", () => {
  storage.clear();

  const legalCase = createLocalCaseFromWizard(
    {
      arquivo: { status: "done" },
      modulos: {
        analise_contratual_ia: true,
        escavador: false,
        ia_deepseek: true,
        revisao_humana: false,
        serasa_procon: false,
        targetdata: false
      },
      parties: [
        {
          documento: "123.456.789-00",
          email: "cliente@example.test",
          endereco: "Endereco completo",
          id: "party-123",
          nome: "Cliente Local",
          papel: "contratante",
          rg: "00.000.000-0",
          telefone: "+55 11 99999-0000"
        } as never
      ],
      produto: "analise_contratual"
    },
    new Date("2026-06-01T10:00:00.000Z")
  );

  assert.equal(legalCase.clientName, "Cliente Local");
  assert.equal(legalCase.status, "awaiting_triage");
  assert.equal(legalCase.documentsCount, 1);
  assert.equal(legalCase.progressPercent, 40);
  assert.equal(legalCase.parties.length, 1);
  assert.equal(legalCase.parties[0].name, "Cliente Local");
  assert.equal(legalCase.parties[0].document, "");
  assert.equal(legalCase.parties[0].documentMasked, "123****00");
  assert.equal(legalCase.metadata?.wizardDocument !== null, true);

  const serialized = JSON.stringify(legalCase);
  assert.equal(serialized.includes("123.456.789-00"), false);
  assert.equal(serialized.includes("00.000.000-0"), false);
  assert.equal(serialized.includes("cliente@example.test"), false);
  assert.equal(serialized.includes("+55 11 99999-0000"), false);
  assert.equal(serialized.includes("Endereco completo"), false);
});

test("local cases persist and are merged before existing cases without duplication", () => {
  storage.clear();
  const localCase = makeCase();
  const existingCase = makeCase({
    id: "case-001",
    code: "CASO-2026-001",
    clientName: "Caso demonstrativo"
  });

  saveStoredLocalCase(localCase);
  saveStoredLocalCase(localCase);

  assert.equal(getStoredLocalCases().length, 1);
  assert.equal(storage.getItem(LOCAL_CASES_STORAGE_KEY)?.includes(localCase.code), true);

  const merged = mergeCasesWithLocalCases([localCase, existingCase]);

  assert.equal(merged.length, 2);
  assert.equal(merged[0].id, localCase.id);
  assert.equal(merged[1].id, existingCase.id);
});

test("local cases can be found by id or code for direct detail routes", () => {
  storage.clear();
  const localCase = makeCase();

  saveStoredLocalCase(localCase);

  assert.equal(findStoredLocalCase(localCase.id)?.id, localCase.id);
  assert.equal(findStoredLocalCase(localCase.code)?.id, localCase.id);
  assert.equal(isLocalOnlyCase(localCase), true);
});
