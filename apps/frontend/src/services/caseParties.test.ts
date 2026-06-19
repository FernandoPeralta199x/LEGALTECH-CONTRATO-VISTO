import assert from "node:assert/strict";
import test from "node:test";

import { createCaseParty, listCaseParties, updateCaseParty } from "./caseParties";

test("listCaseParties maps backend parties and reports api source", async () => {
  globalThis.fetch = (async () =>
    Response.json({
      success: true,
      data: [
        {
          id: "party-api-1",
          case_id: "case-api-1",
          party_type: "cliente",
          name: "Parte API",
          document: "00000000000",
          email: "parte@example.test",
          phone: "+5500000000000",
          notes: "Observacao local ficticia",
          metadata: {},
          created_at: "2026-05-25T10:00:00.000Z",
          updated_at: "2026-05-25T10:00:00.000Z"
        }
      ]
    })) as typeof fetch;

  const result = await listCaseParties("case-api-1");

  assert.equal(result.source, "api");
  assert.equal(result.data[0].id, "party-api-1");
  assert.equal(result.data[0].caseId, "case-api-1");
  assert.equal(result.data[0].type, "cliente");
  assert.equal(result.data[0].email, "parte@example.test");
});

test("createCaseParty sends backend field names and omits organization_id", async () => {
  let requestBody = "";

  globalThis.fetch = (async (_url, init) => {
    requestBody = String(init?.body ?? "");

    return Response.json(
      {
        success: true,
        data: {
          id: "party-created",
          case_id: "case-api-1",
          party_type: "contraparte",
          name: "Parte Criada",
          document: null,
          email: null,
          phone: null,
          notes: null,
          metadata: {},
          created_at: "2026-05-25T10:00:00.000Z",
          updated_at: "2026-05-25T10:00:00.000Z"
        }
      },
      { status: 201 }
    );
  }) as typeof fetch;

  await createCaseParty(
    "case-api-1",
    {
      name: "Parte Criada",
      party_type: "contraparte",
      organization_id: "nao-deve-sair-do-frontend"
    } as Parameters<typeof createCaseParty>[1] & { organization_id: string }
  );

  const payload = JSON.parse(requestBody);
  assert.equal(payload.party_type, "contraparte");
  assert.equal(payload.organization_id, undefined);
});

test("updateCaseParty sends PATCH and omits organization_id", async () => {
  let requestBody = "";
  let requestMethod = "";

  globalThis.fetch = (async (_url, init) => {
    requestMethod = String(init?.method);
    requestBody = String(init?.body ?? "");

    return Response.json({
      success: true,
      data: {
        id: "party-api-1",
        case_id: "case-api-1",
        party_type: "testemunha",
        name: "Parte Atualizada",
        document: null,
        email: "parte.atualizada@example.test",
        phone: null,
        notes: null,
        metadata: {},
        created_at: "2026-05-25T10:00:00.000Z",
        updated_at: "2026-05-25T11:00:00.000Z"
      }
    });
  }) as typeof fetch;

  const result = await updateCaseParty(
    "case-api-1",
    "party-api-1",
    {
      email: "parte.atualizada@example.test",
      name: "Parte Atualizada",
      organization_id: "nao-deve-sair-do-frontend"
    } as Parameters<typeof updateCaseParty>[2] & { organization_id: string }
  );

  const payload = JSON.parse(requestBody);
  assert.equal(requestMethod, "PATCH");
  assert.equal(payload.organization_id, undefined);
  assert.equal(result.data.name, "Parte Atualizada");
  assert.equal(result.data.email, "parte.atualizada@example.test");
});
