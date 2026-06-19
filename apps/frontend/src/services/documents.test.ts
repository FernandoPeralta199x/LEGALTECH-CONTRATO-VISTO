import assert from "node:assert/strict";
import test from "node:test";

import { createDocument, listDocuments, uploadDocument } from "./documents";

test("listDocuments maps backend documents and reports api source", async () => {
  globalThis.fetch = (async () =>
    Response.json({
      success: true,
      data: [
        {
          id: "doc-api-1",
          case_id: "case-api-1",
          filename: "contrato.pdf",
          content_type: "application/pdf",
          size_bytes: 2048,
          file_hash: null,
          status: "uploaded",
          uploaded_by: null,
          uploaded_at: "2026-05-25T10:00:00.000Z",
          metadata: {},
          created_at: "2026-05-25T10:00:00.000Z",
          updated_at: "2026-05-25T10:00:00.000Z"
        }
      ]
    })) as typeof fetch;

  const result = await listDocuments();

  assert.equal(result.source, "api");
  assert.equal(result.data[0].id, "doc-api-1");
  assert.equal(result.data[0].sizeLabel, "2 KB");
  assert.equal(result.data[0].caseCode, "CASE-API-1");
});

test("createDocument sends metadata-only backend payload without organization_id", async () => {
  let requestBody = "";

  globalThis.fetch = (async (_url, init) => {
    requestBody = String(init?.body ?? "");

    return Response.json(
      {
        success: true,
        data: {
          id: "doc-created",
          case_id: "case-api-1",
          filename: "contrato.pdf",
          content_type: "application/pdf",
          size_bytes: 1024,
          file_hash: null,
          status: "pending_upload",
          uploaded_by: null,
          uploaded_at: null,
          metadata: {},
          created_at: "2026-05-25T10:00:00.000Z",
          updated_at: "2026-05-25T10:00:00.000Z"
        }
      },
      { status: 201 }
    );
  }) as typeof fetch;

  await createDocument({
    case_id: "case-api-1",
    content_type: "application/pdf",
    filename: "contrato.pdf",
    size_bytes: 1024
  });

  const payload = JSON.parse(requestBody);
  assert.equal(payload.case_id, "case-api-1");
  assert.equal(payload.organization_id, undefined);
});

test("uploadDocument sends multipart payload through apiClient without organization_id", async () => {
  let requestUrl = "";
  let requestBody: BodyInit | null | undefined;
  let authorizationHeader: string | null = null;

  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: {
      getItem: (key: string) =>
        key === "legaltech.dev.session.v1"
          ? JSON.stringify({
              email: "dev.local@example.test",
              issuedAt: "2026-05-30T12:00:00.000Z",
              organizationId: "11111111-1111-4111-8111-111111111111",
              role: "admin",
              source: "pasted",
              token: "valid.dev.jwt",
              userId: "22222222-2222-4222-8222-222222222222"
            })
          : null,
      removeItem: () => undefined,
      setItem: () => undefined
    }
  });

  globalThis.fetch = (async (url, init) => {
    requestUrl = String(url);
    requestBody = init?.body;
    authorizationHeader = new Headers(init?.headers).get("Authorization");

    return Response.json(
      {
        success: true,
        data: {
          id: "doc-uploaded",
          case_id: "case-api-1",
          filename: "contrato.pdf",
          content_type: "application/pdf",
          size_bytes: 1024,
          file_hash: "sha256:abc123",
          status: "uploaded",
          uploaded_by: "22222222-2222-4222-8222-222222222222",
          uploaded_at: "2026-05-30T12:00:00.000Z",
          metadata: { notes: "Teste local", source: "frontend_local_upload" },
          created_at: "2026-05-30T12:00:00.000Z",
          updated_at: "2026-05-30T12:00:00.000Z"
        }
      },
      { status: 201 }
    );
  }) as typeof fetch;

  const file = new File(["conteudo"], "contrato.pdf", {
    type: "application/pdf"
  });

  const result = await uploadDocument({
    caseId: "case-api-1",
    file,
    metadata: { notes: "Teste local", organization_id: "frontend-ignored" }
  });

  assert.equal(result.source, "api");
  assert.equal(result.data.status, "uploaded");
  assert.match(requestUrl, /\/api\/v1\/documents\/upload$/);
  assert.equal(authorizationHeader, "Bearer valid.dev.jwt");
  assert.ok(requestBody instanceof FormData);
  assert.equal(requestBody.get("case_id"), "case-api-1");
  assert.equal(requestBody.get("file"), file);
  assert.equal(requestBody.get("organization_id"), null);
  assert.deepEqual(JSON.parse(String(requestBody.get("metadata"))), {
    notes: "Teste local"
  });
});
