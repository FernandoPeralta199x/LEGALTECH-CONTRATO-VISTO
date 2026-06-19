import assert from "node:assert/strict";
import test from "node:test";

import {
  validateCaseForm,
  validateClientForm,
  validateDevJwtForm,
  validateDocumentForm,
  validateDocumentUploadForm,
  validatePasswordChange
} from "./validation";

function makeJwt(payload: Record<string, unknown>): string {
  const encode = (value: Record<string, unknown>) =>
    Buffer.from(JSON.stringify(value)).toString("base64url");

  return `${encode({ alg: "HS256", typ: "JWT" })}.${encode(payload)}.signature`;
}

test("validateClientForm requires a client name", () => {
  const result = validateClientForm({ name: "   " });

  assert.equal(result.valid, false);
  assert.equal(result.errors.name, "Informe o nome do cliente.");
});

test("validateClientForm requires individual full name and contract role", () => {
  const result = validateClientForm({
    contractRole: "",
    fullName: "",
    personType: "individual"
  });

  assert.equal(result.valid, false);
  assert.equal(result.errors.fullName, "Informe o nome completo.");
  assert.equal(result.errors.contractRole, "Selecione o papel no contrato.");
});

test("validateClientForm requires company legal name", () => {
  const result = validateClientForm({
    contractRole: "contractor",
    legalName: "",
    personType: "company"
  });

  assert.equal(result.valid, false);
  assert.equal(result.errors.legalName, "Informe a razão social.");
});

test("validateClientForm validates CPF, CNPJ, phone and birth date lightly", () => {
  const individual = validateClientForm({
    birthDate: "31/02/1990",
    contractRole: "contractor",
    cpf: "123",
    fullName: "Cliente Teste",
    personType: "individual",
    phone: "119"
  });
  const company = validateClientForm({
    cnpj: "12",
    contractRole: "contractor",
    legalName: "Empresa Teste",
    personType: "company"
  });

  assert.equal(individual.valid, false);
  assert.equal(individual.errors.cpf, "Informe um CPF com 11 dígitos.");
  assert.equal(individual.errors.birthDate, "Informe uma data válida no formato dd/mm/aaaa.");
  assert.equal(individual.errors.phone, "Informe um telefone brasileiro com DDD.");
  assert.equal(company.valid, false);
  assert.equal(company.errors.cnpj, "Informe um CNPJ com 14 dígitos.");
});

test("validateClientForm validates optional document format lightly", () => {
  const result = validateClientForm({ document: "abc@", name: "Cliente Dev" });

  assert.equal(result.valid, false);
  assert.equal(result.errors.document, "Use apenas números, letras, pontos, barras ou hífens.");
});

test("validateCaseForm requires title and linked client", () => {
  const result = validateCaseForm({
    caseType: "contract_analysis",
    clientId: "",
    priority: "normal",
    title: ""
  });

  assert.equal(result.valid, false);
  assert.equal(result.errors.title, "Informe o título do caso.");
  assert.equal(result.errors.clientId, "Selecione um cliente vinculado.");
});

test("validateCaseForm rejects uncontrolled priority values", () => {
  const result = validateCaseForm({
    caseType: "contract_analysis",
    clientId: "client-1",
    priority: "critical",
    title: "Análise contratual"
  });

  assert.equal(result.valid, false);
  assert.equal(result.errors.priority, "Selecione uma prioridade válida.");
});

test("validateDocumentForm requires case, filename and positive size", () => {
  const result = validateDocumentForm({
    caseId: "",
    contentType: "application/pdf",
    filename: "",
    sizeBytes: "0",
    status: "pending_upload"
  });

  assert.equal(result.valid, false);
  assert.equal(result.errors.caseId, "Selecione um caso vinculado.");
  assert.equal(result.errors.filename, "Informe o nome do documento.");
  assert.equal(result.errors.sizeBytes, "Informe um tamanho válido em bytes.");
});

test("validateDocumentForm rejects uncontrolled status values", () => {
  const result = validateDocumentForm({
    caseId: "case-1",
    contentType: "application/pdf",
    filename: "contrato.pdf",
    sizeBytes: "1024",
    status: "unknown"
  });

  assert.equal(result.valid, false);
  assert.equal(result.errors.status, "Selecione um status válido.");
});

test("validateDocumentUploadForm requires linked case and file", () => {
  const result = validateDocumentUploadForm({
    caseId: "",
    file: null
  });

  assert.equal(result.valid, false);
  assert.equal(result.errors.caseId, "Selecione um caso vinculado.");
  assert.equal(result.errors.file, "Selecione um arquivo para upload.");
});

test("validateDocumentUploadForm blocks unsupported type and oversized file", () => {
  const result = validateDocumentUploadForm({
    caseId: "case-1",
    file: {
      name: "payload.exe",
      size: 11 * 1024 * 1024,
      type: "application/octet-stream"
    }
  });

  assert.equal(result.valid, false);
  assert.equal(
    result.errors.file,
    "Use PDF, PNG, JPG, JPEG, DOCX, TXT ou MD com no máximo 10 MB."
  );
});

test("validateDocumentUploadForm accepts local MVP image and pdf uploads", () => {
  assert.equal(
    validateDocumentUploadForm({
      caseId: "case-1",
      file: { name: "contrato.pdf", size: 1024, type: "application/pdf" }
    }).valid,
    true
  );
  assert.equal(
    validateDocumentUploadForm({
      caseId: "case-1",
      file: { name: "evidencia.png", size: 2048, type: "image/png" }
    }).valid,
    true
  );
});

test("validateDevJwtForm requires a pasted dev JWT", () => {
  const result = validateDevJwtForm("");

  assert.equal(result.valid, false);
  assert.equal(
    result.errors.token,
    "Cole o JWT dev gerado pelo backend para acessar o ambiente local."
  );
});

test("validateDevJwtForm rejects malformed or expired JWTs", () => {
  const validToken = makeJwt({
    aud: "legaltech-local-api",
    email: "dev.local@example.test",
    exp: Math.floor(Date.now() / 1000) + 60,
    iat: Math.floor(Date.now() / 1000),
    iss: "legaltech-local-dev",
    sub: "22222222-2222-4222-8222-222222222222",
    token_use: "dev",
    "custom:organization_id": "11111111-1111-4111-8111-111111111111",
    "custom:role": "admin"
  });

  assert.equal(validateDevJwtForm(validToken).valid, true);

  const invalid = validateDevJwtForm("token-invalido");
  assert.equal(invalid.valid, false);
  assert.equal(
    invalid.errors.token,
    "Cole um JWT dev válido com três partes no formato header.payload.signature."
  );

  const invalidPayload = validateDevJwtForm("header.payload.signature");
  assert.equal(invalidPayload.valid, false);
  assert.equal(invalidPayload.errors.token, "O payload do JWT dev não pôde ser lido.");

  const expired = validateDevJwtForm(
    makeJwt({
      aud: "legaltech-local-api",
      email: "dev.local@example.test",
      exp: Math.floor(Date.now() / 1000) - 60,
      iat: Math.floor(Date.now() / 1000) - 120,
      iss: "legaltech-local-dev",
      sub: "22222222-2222-4222-8222-222222222222",
      token_use: "dev",
      "custom:organization_id": "11111111-1111-4111-8111-111111111111",
      "custom:role": "admin"
    })
  );
  assert.equal(expired.valid, false);
  assert.equal(expired.errors.token, "JWT dev expirado. Gere um novo token no backend.");
});

test("validatePasswordChange requires a strong new password and matching confirmation", () => {
  const result = validatePasswordChange({
    confirmPassword: "Senha-fraca-2",
    currentPassword: "",
    newPassword: "senha"
  });

  assert.equal(result.valid, false);
  assert.equal(result.errors.currentPassword, "Informe a senha atual.");
  assert.equal(result.errors.newPassword, "A senha deve atender todos os requisitos.");
  assert.equal(result.errors.confirmPassword, "A confirmação deve ser igual à nova senha.");
  assert.deepEqual(result.requirements, {
    hasLowercase: true,
    hasMinLength: false,
    hasSpecial: false,
    hasUppercase: false
  });
});

test("validatePasswordChange accepts valid local password change input", () => {
  const result = validatePasswordChange({
    confirmPassword: "Senha@123",
    currentPassword: "Atual@123",
    newPassword: "Senha@123"
  });

  assert.equal(result.valid, true);
  assert.deepEqual(result.errors, {});
  assert.deepEqual(result.requirements, {
    hasLowercase: true,
    hasMinLength: true,
    hasSpecial: true,
    hasUppercase: true
  });
});
