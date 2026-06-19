import type {
  Client,
  ClientContractRole,
  ClientCreate,
  ClientUpdate,
  ClientPersonType
} from "../../types";

export type ClientFormState = {
  address: string;
  birthDate: string;
  cnpj: string;
  contractRole: ClientContractRole | "";
  cpf: string;
  email: string;
  fullName: string;
  legalName: string;
  personType: ClientPersonType;
  phone: string;
  rg: string;
  tradeName: string;
};

export const clientContractRoleLabels: Record<ClientContractRole, string> = {
  contracted: "Contratada",
  contractor: "Contratante",
  guarantor: "Garantidor",
  intervening: "Interveniente",
  other: "Outro",
  witness: "Testemunha"
};

export const clientPersonTypeLabels: Record<ClientPersonType, string> = {
  company: "Pessoa jurídica",
  individual: "Pessoa física"
};

export const emptyClientForm: ClientFormState = {
  address: "",
  birthDate: "",
  cnpj: "",
  contractRole: "",
  cpf: "",
  email: "",
  fullName: "",
  legalName: "",
  personType: "individual",
  phone: "",
  rg: "",
  tradeName: ""
};

export function onlyDigits(value: string): string {
  return value.replace(/\D/g, "");
}

export function maskCpf(value: string): string {
  const digits = onlyDigits(value).slice(0, 11);
  return digits
    .replace(/^(\d{3})(\d)/, "$1.$2")
    .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
    .replace(/^(\d{3})\.(\d{3})\.(\d{3})(\d)/, "$1.$2.$3-$4");
}

export function maskCnpj(value: string): string {
  const digits = onlyDigits(value).slice(0, 14);
  return digits
    .replace(/^(\d{2})(\d)/, "$1.$2")
    .replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3")
    .replace(/^(\d{2})\.(\d{3})\.(\d{3})(\d)/, "$1.$2.$3/$4")
    .replace(/^(\d{2})\.(\d{3})\.(\d{3})\/(\d{4})(\d)/, "$1.$2.$3/$4-$5");
}

export function maskPhone(value: string): string {
  const digits = onlyDigits(value).slice(0, 11);
  if (digits.length <= 2) return digits;
  if (digits.length <= 6) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
  if (digits.length <= 10) {
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
  }

  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
}

export function maskBirthDate(value: string): string {
  const digits = onlyDigits(value).slice(0, 8);
  return digits
    .replace(/^(\d{2})(\d)/, "$1/$2")
    .replace(/^(\d{2})\/(\d{2})(\d)/, "$1/$2/$3");
}

export function brazilianDateToIso(value: string): string | null {
  const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(value.trim());
  if (!match) return null;

  const [, day, month, year] = match;
  const iso = `${year}-${month}-${day}`;
  const date = new Date(`${iso}T00:00:00.000Z`);
  if (
    date.getUTCFullYear() !== Number(year) ||
    date.getUTCMonth() + 1 !== Number(month) ||
    date.getUTCDate() !== Number(day)
  ) {
    return null;
  }

  return iso;
}

export function isoDateToBrazilian(value: string | null | undefined): string {
  if (!value) return "";
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  return match ? `${match[3]}/${match[2]}/${match[1]}` : "";
}

export function maskDocumentForDisplay(value: string | null | undefined): string {
  const digits = onlyDigits(value ?? "");
  if (digits.length === 11) {
    return `***.***.***-${digits.slice(-2)}`;
  }
  if (digits.length === 14) {
    return `**.***.***/****-${digits.slice(-2)}`;
  }
  if (value?.trim()) {
    return "Documento protegido";
  }

  return "Documento não informado";
}

export function visibleClientFields(personType: ClientPersonType): string[] {
  const common = ["personType", "contractRole", "email", "phone", "address"];
  if (personType === "company") {
    return ["personType", "contractRole", "legalName", "tradeName", "cnpj", "email", "phone", "address"];
  }

  return ["personType", "contractRole", "fullName", "cpf", "rg", "birthDate", ...common.slice(2)];
}

function clean(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

export function buildClientCreatePayload(form: ClientFormState): ClientCreate {
  const email = clean(form.email);
  const phone = clean(form.phone);
  const address = clean(form.address);
  const role = form.contractRole || "other";

  if (form.personType === "company") {
    const legalName = clean(form.legalName) ?? "";
    const tradeName = clean(form.tradeName);
    const cnpj = clean(form.cnpj);
    return {
      address,
      cnpj,
      company_name: legalName,
      contract_role: role,
      display_name: tradeName ?? legalName,
      document: cnpj,
      document_number: cnpj,
      document_type: cnpj ? "cnpj" : "unknown",
      email,
      legal_name: legalName,
      metadata: {
        source: "clients_form",
        submitted_fields: visibleClientFields("company")
      },
      name: legalName,
      person_type: "company",
      phone,
      source_mode: "mock",
      trade_name: tradeName
    };
  }

  const fullName = clean(form.fullName) ?? "";
  const cpf = clean(form.cpf);
  const rg = clean(form.rg);
  const birthDate = brazilianDateToIso(form.birthDate);

  return {
    address,
    birth_date: birthDate,
    contract_role: role,
    cpf,
    display_name: fullName,
    document: cpf ?? rg,
    document_number: cpf ?? rg,
    document_type: cpf ? "cpf" : rg ? "rg" : "unknown",
    email,
    full_name: fullName,
    metadata: {
      source: "clients_form",
      submitted_fields: visibleClientFields("individual")
    },
    name: fullName,
    person_type: "individual",
    phone,
    rg,
    source_mode: "mock"
  };
}

function hasProtectedDocumentLabel(client: Client): boolean {
  const label = client.documentMasked ?? client.documentLabel;
  return Boolean(label && label !== "Documento não informado");
}

export function buildClientUpdatePayload(
  form: ClientFormState,
  currentClient: Client
): ClientUpdate {
  const payload: ClientUpdate = buildClientCreatePayload(form);
  const samePersonType = (currentClient.personType ?? form.personType) === form.personType;
  const hasDocumentInput =
    form.personType === "company"
      ? Boolean(clean(form.cnpj))
      : Boolean(clean(form.cpf) || clean(form.rg));

  if (samePersonType && !hasDocumentInput && hasProtectedDocumentLabel(currentClient)) {
    delete payload.cnpj;
    delete payload.cpf;
    delete payload.document;
    delete payload.document_number;
    delete payload.document_type;
    delete payload.rg;
  }

  return payload;
}

function metadataString(client: Client, key: string): string {
  const value = client.metadata?.[key];
  return typeof value === "string" ? value : "";
}

export function clientFormFromClient(client: Client): ClientFormState {
  const personType = client.personType ?? (
    client.documentType === "cnpj" ? "company" : "individual"
  );

  return {
    address: client.address ?? metadataString(client, "address"),
    birthDate: isoDateToBrazilian(client.birthDate ?? metadataString(client, "birth_date")),
    cnpj: client.cnpj ?? (client.documentType === "cnpj" ? client.document ?? "" : ""),
    contractRole: client.contractRole ?? "",
    cpf: client.cpf ?? (client.documentType === "cpf" ? client.document ?? "" : ""),
    email: client.email,
    fullName: client.fullName ?? (personType === "individual" ? client.name : ""),
    legalName: client.legalName ?? client.companyName ?? (personType === "company" ? client.name : ""),
    personType,
    phone: client.phone,
    rg: client.rg ?? (client.documentType === "rg" ? client.document ?? "" : ""),
    tradeName: client.tradeName ?? metadataString(client, "trade_name")
  };
}
