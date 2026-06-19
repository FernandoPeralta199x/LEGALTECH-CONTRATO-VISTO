import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { ApiClientError } from "./apiClient";
import { createClient, listClients, updateClient } from "./clients";

async function withLocalStorage<T>(run: () => Promise<T> | T): Promise<T> {
  const storage = new Map<string, string>();
  const localStorage = {
    clear: () => storage.clear(),
    getItem: (key: string) => storage.get(key) ?? null,
    key: (index: number) => Array.from(storage.keys())[index] ?? null,
    get length() {
      return storage.size;
    },
    removeItem: (key: string) => storage.delete(key),
    setItem: (key: string, value: string) => storage.set(key, value)
  } as Storage;
  const descriptor = Object.getOwnPropertyDescriptor(globalThis, "localStorage");
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: localStorage
  });

  try {
    return await run();
  } finally {
    if (descriptor) {
      Object.defineProperty(globalThis, "localStorage", descriptor);
    } else {
      Reflect.deleteProperty(globalThis, "localStorage");
    }
  }
}

async function withMockFallback<T>(run: () => Promise<T>): Promise<T> {
  const originalMockFallback = process.env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK;
  process.env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK = "true";

  try {
    return await run();
  } finally {
    if (originalMockFallback === undefined) {
      delete process.env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK;
    } else {
      process.env.NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK = originalMockFallback;
    }
  }
}

test("listClients maps backend clients and reports api source", async () => {
  globalThis.fetch = (async () =>
    Response.json({
      success: true,
      data: [
        {
          id: "client-api-1",
          name: "Cliente API",
          document: "00000000000",
          document_masked: "***.***.***-00",
          person_type: "individual",
          contract_role: "contractor",
          display_name: "Cliente API",
          email: "cliente.api@example.test",
          phone: "+5500000000000",
          metadata: { source_mode: "mock" },
          source_mode: "mock",
          created_at: "2026-05-25T10:00:00.000Z",
          updated_at: "2026-05-25T10:00:00.000Z"
        }
      ]
    })) as typeof fetch;

  const result = await listClients();

  assert.equal(result.source, "api");
  assert.equal(result.data[0].id, "client-api-1");
  assert.equal(result.data[0].documentLabel, "***.***.***-00");
  assert.equal(result.data[0].personType, "individual");
  assert.equal(result.data[0].contractRole, "contractor");
  assert.equal(result.data[0].createdAt, "2026-05-25T10:00:00.000Z");
});

test("listClients shows empty explicit fallback when the API is unavailable", async () => {
  await withMockFallback(async () => {
    globalThis.fetch = (async () => {
      throw new TypeError("fetch failed");
    }) as typeof fetch;

    const result = await listClients();

    assert.equal(result.source, "mock");
    assert.ok(result.fallbackReason);
    assert.equal(result.data.length, 0);
  });
});

test("listClients does not hide authorization errors behind fallback", async () => {
  globalThis.fetch = (async () =>
    Response.json(
      {
        success: false,
        error: {
          code: "FORBIDDEN",
          message: "Usuário sem permissão.",
          details: {}
        }
      },
      { status: 403 }
    )) as typeof fetch;

  await assert.rejects(() => listClients(), ApiClientError);
});

test("createClient never sends organization_id from the frontend payload", async () => {
  let requestBody = "";

  globalThis.fetch = (async (_url, init) => {
    requestBody = String(init?.body ?? "");

    return Response.json(
      {
        success: true,
        data: {
          id: "client-created",
          name: "Cliente Criado",
          document: null,
          email: "criado@example.test",
          phone: null,
          metadata: {},
          created_at: "2026-05-25T10:00:00.000Z",
          updated_at: "2026-05-25T10:00:00.000Z"
        }
      },
      { status: 201 }
    );
  }) as typeof fetch;

  await createClient({
    contract_role: "contractor",
    email: "criado@example.test",
    full_name: "Cliente Criado",
    name: "Cliente Criado",
    person_type: "individual"
  });

  assert.equal(JSON.parse(requestBody).organization_id, undefined);
});

test("createClient sends individual payload without CNPJ", async () => {
  let requestBody = "";

  globalThis.fetch = (async (_url, init) => {
    requestBody = String(init?.body ?? "");

    return Response.json(
      {
        success: true,
        data: {
          id: "client-individual",
          name: "Cliente Individual",
          document: "123.456.789-01",
          document_masked: "***.***.***-01",
          person_type: "individual",
          contract_role: "contractor",
          email: "individual@example.test",
          phone: "(11) 98888-7777",
          metadata: {},
          created_at: "2026-05-25T10:00:00.000Z",
          updated_at: "2026-05-25T10:00:00.000Z"
        }
      },
      { status: 201 }
    );
  }) as typeof fetch;

  await createClient({
    birth_date: "1990-01-01",
    contract_role: "contractor",
    cpf: "123.456.789-01",
    document: "123.456.789-01",
    document_type: "cpf",
    email: "individual@example.test",
    full_name: "Cliente Individual",
    name: "Cliente Individual",
    person_type: "individual",
    phone: "(11) 98888-7777"
  });

  const payload = JSON.parse(requestBody);
  assert.equal(payload.person_type, "individual");
  assert.equal(payload.cpf, "123.456.789-01");
  assert.equal(payload.cnpj, undefined);
});

test("createClient sends company payload without CPF", async () => {
  let requestBody = "";

  globalThis.fetch = (async (_url, init) => {
    requestBody = String(init?.body ?? "");

    return Response.json(
      {
        success: true,
        data: {
          id: "client-company",
          name: "Empresa Teste Ltda",
          document: "12.345.678/0001-99",
          document_masked: "**.***.***/****-99",
          person_type: "company",
          contract_role: "contractor",
          email: "empresa@example.test",
          phone: "(11) 98888-7777",
          metadata: {},
          created_at: "2026-05-25T10:00:00.000Z",
          updated_at: "2026-05-25T10:00:00.000Z"
        }
      },
      { status: 201 }
    );
  }) as typeof fetch;

  await createClient({
    cnpj: "12.345.678/0001-99",
    contract_role: "contractor",
    document: "12.345.678/0001-99",
    document_type: "cnpj",
    email: "empresa@example.test",
    legal_name: "Empresa Teste Ltda",
    name: "Empresa Teste Ltda",
    person_type: "company",
    phone: "(11) 98888-7777",
    trade_name: "Empresa Teste"
  });

  const payload = JSON.parse(requestBody);
  assert.equal(payload.person_type, "company");
  assert.equal(payload.cnpj, "12.345.678/0001-99");
  assert.equal(payload.cpf, undefined);
});

test("updateClient sends PATCH and omits organization_id from the frontend payload", async () => {
  let requestBody = "";
  let requestMethod = "";
  let requestUrl = "";

  globalThis.fetch = (async (url, init) => {
    requestUrl = String(url);
    requestMethod = String(init?.method);
    requestBody = String(init?.body ?? "");

    return Response.json({
      success: true,
      data: {
        id: "client-updated",
        name: "Cliente Atualizado",
        document: null,
        email: "atualizado@example.test",
        phone: "+5500000000000",
        metadata: {},
        created_at: "2026-05-25T10:00:00.000Z",
        updated_at: "2026-05-25T11:00:00.000Z"
      }
    });
  }) as typeof fetch;

  const result = await updateClient(
    "client-updated",
    {
      email: "atualizado@example.test",
      name: "Cliente Atualizado",
      organization_id: "nao-deve-sair-do-frontend"
    } as Parameters<typeof updateClient>[1] & { organization_id: string }
  );

  const payload = JSON.parse(requestBody);
  assert.equal(requestMethod, "PATCH");
  assert.equal(requestUrl.endsWith("/api/v1/clients/client-updated"), true);
  assert.equal(payload.name, "Cliente Atualizado");
  assert.equal(payload.organization_id, undefined);
  assert.equal(result.source, "api");
  assert.equal(result.data.name, "Cliente Atualizado");
});

test("client fallback persists create and list with masked document", async () => {
  await withMockFallback(async () =>
    withLocalStorage(async () => {
      globalThis.fetch = (async () => {
        throw new TypeError("fetch failed");
      }) as typeof fetch;

      const created = await createClient({
        contract_role: "contractor",
        cpf: "123.456.789-01",
        document: "123.456.789-01",
        document_type: "cpf",
        full_name: "Cliente Local",
        name: "Cliente Local",
        person_type: "individual"
      });
      const listed = await listClients();

      assert.equal(created.source, "mock");
      assert.equal(created.data.sourceMode, "local");
      assert.equal(listed.source, "mock");
      assert.equal(listed.data.length, 1);
      assert.equal(listed.data[0].id, created.data.id);
      assert.equal(listed.data[0].documentLabel, "***.***.***-01");
    })
  );
});

test("client fallback updates local clients when the API is unavailable", async () => {
  await withMockFallback(async () =>
    withLocalStorage(async () => {
      globalThis.fetch = (async () => {
        throw new TypeError("fetch failed");
      }) as typeof fetch;

      const created = await createClient({
        cnpj: "12.345.678/0001-99",
        contract_role: "contractor",
        document: "12.345.678/0001-99",
        document_type: "cnpj",
        legal_name: "Empresa Local Ltda",
        name: "Empresa Local Ltda",
        person_type: "company"
      });
      const updated = await updateClient(created.data.id, {
        cnpj: "12.345.678/0001-00",
        contract_role: "contracted",
        document: "12.345.678/0001-00",
        document_type: "cnpj",
        legal_name: "Empresa Local Atualizada Ltda",
        name: "Empresa Local Atualizada Ltda",
        person_type: "company"
      });
      const listed = await listClients();

      assert.equal(updated.source, "mock");
      assert.equal(updated.data.name, "Empresa Local Atualizada Ltda");
      assert.equal(updated.data.contractRole, "contracted");
      assert.equal(updated.data.documentLabel, "**.***.***/****-00");
      assert.equal(listed.data[0].name, "Empresa Local Atualizada Ltda");
    })
  );
});

test("clients page uses the dark SelectInput component for person and role fields", () => {
  const source = readFileSync(
    new URL("../app/clients/page.tsx", import.meta.url),
    "utf8"
  );

  assert.match(source, /import \{ FormField, SelectInput, TextInput \}/);
  assert.equal((source.match(/<SelectInput/g) ?? []).length >= 2, true);
});
