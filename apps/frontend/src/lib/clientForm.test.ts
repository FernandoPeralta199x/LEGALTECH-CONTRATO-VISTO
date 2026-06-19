import assert from "node:assert/strict";
import test from "node:test";

import {
  buildClientCreatePayload,
  buildClientUpdatePayload,
  maskBirthDate,
  maskCnpj,
  maskCpf,
  maskDocumentForDisplay,
  maskPhone,
  visibleClientFields,
  type ClientFormState
} from "./clientForm";
import type { Client } from "../../types";

const baseForm: ClientFormState = {
  address: "Rua Teste, 100",
  birthDate: "",
  cnpj: "",
  contractRole: "contractor",
  cpf: "",
  email: "contato@example.test",
  fullName: "",
  legalName: "",
  personType: "individual",
  phone: "(11) 98888-7777",
  rg: "",
  tradeName: ""
};

test("client form exposes individual fields without company document", () => {
  const fields = visibleClientFields("individual");

  assert.ok(fields.includes("fullName"));
  assert.ok(fields.includes("cpf"));
  assert.equal(fields.includes("cnpj"), false);
});

test("client form exposes company fields without individual document", () => {
  const fields = visibleClientFields("company");

  assert.ok(fields.includes("legalName"));
  assert.ok(fields.includes("cnpj"));
  assert.equal(fields.includes("cpf"), false);
});

test("client form masks CPF, CNPJ, phone and birth date", () => {
  assert.equal(maskCpf("12345678901"), "123.456.789-01");
  assert.equal(maskCnpj("12345678000199"), "12.345.678/0001-99");
  assert.equal(maskPhone("11988887777"), "(11) 98888-7777");
  assert.equal(maskBirthDate("01011990"), "01/01/1990");
});

test("individual payload sends CPF and never sends CNPJ", () => {
  const payload = buildClientCreatePayload({
    ...baseForm,
    birthDate: "01/01/1990",
    cpf: "123.456.789-01",
    fullName: "Cliente Pessoa Fisica",
    rg: "12.345.678-9"
  });

  assert.equal(payload.person_type, "individual");
  assert.equal(payload.contract_role, "contractor");
  assert.equal(payload.name, "Cliente Pessoa Fisica");
  assert.equal(payload.full_name, "Cliente Pessoa Fisica");
  assert.equal(payload.cpf, "123.456.789-01");
  assert.equal(payload.birth_date, "1990-01-01");
  assert.equal(payload.cnpj, undefined);
});

test("company payload sends CNPJ and never sends CPF", () => {
  const payload = buildClientCreatePayload({
    ...baseForm,
    cnpj: "12.345.678/0001-99",
    legalName: "Acme Comercio Ltda",
    personType: "company",
    tradeName: "Acme"
  });

  assert.equal(payload.person_type, "company");
  assert.equal(payload.name, "Acme Comercio Ltda");
  assert.equal(payload.legal_name, "Acme Comercio Ltda");
  assert.equal(payload.trade_name, "Acme");
  assert.equal(payload.cnpj, "12.345.678/0001-99");
  assert.equal(payload.cpf, undefined);
});

test("document display mask never returns a full CPF or CNPJ", () => {
  assert.equal(maskDocumentForDisplay("123.456.789-01"), "***.***.***-01");
  assert.equal(maskDocumentForDisplay("12.345.678/0001-99"), "**.***.***/****-99");
});

test("update payload preserves protected backend document when edit form has no raw document", () => {
  const currentClient: Client = {
    casesCount: 0,
    createdAt: "2026-05-25T10:00:00.000Z",
    displayName: "Cliente Pessoa Fisica",
    document: null,
    documentLabel: "***.***.***-01",
    documentMasked: "***.***.***-01",
    documentType: "cpf",
    email: "cliente@example.test",
    id: "client-api-1",
    name: "Cliente Pessoa Fisica",
    personType: "individual",
    phone: "(11) 98888-7777",
    riskLevel: "low",
    status: "active"
  };

  const payload = buildClientUpdatePayload(
    {
      ...baseForm,
      fullName: "Cliente Pessoa Fisica Atualizado",
      phone: "(11) 97777-6666"
    },
    currentClient
  );

  assert.equal(payload.name, "Cliente Pessoa Fisica Atualizado");
  assert.equal(payload.document, undefined);
  assert.equal(payload.document_number, undefined);
  assert.equal(payload.document_type, undefined);
  assert.equal(payload.cpf, undefined);
});
