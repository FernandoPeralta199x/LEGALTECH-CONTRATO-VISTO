export type ValidationErrors = Record<string, string>;

export type ValidationResult = {
  errors: ValidationErrors;
  valid: boolean;
};

export type PasswordRequirementState = {
  hasLowercase: boolean;
  hasMinLength: boolean;
  hasSpecial: boolean;
  hasUppercase: boolean;
};

export type PasswordValidationResult = ValidationResult & {
  requirements: PasswordRequirementState;
};

type ClientFormValidationInput = {
  birthDate?: string | null;
  cnpj?: string | null;
  contractRole?: string | null;
  cpf?: string | null;
  document?: string | null;
  email?: string | null;
  fullName?: string | null;
  legalName?: string | null;
  name?: string | null;
  personType?: string | null;
  phone?: string | null;
};

const allowedPriorities = new Set(["low", "normal", "high", "urgent"]);
const allowedDocumentStatuses = new Set([
  "pending_upload",
  "uploaded",
  "processing",
  "processed"
]);
const allowedContentTypes = new Set([
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "image/jpeg",
  "image/png",
  "text/plain"
]);
const maxDocumentUploadSizeBytes = 10 * 1024 * 1024;
const allowedUploadMimeTypesByExtension: Record<string, ReadonlySet<string>> = {
  ".docx": new Set([
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  ]),
  ".jpeg": new Set(["image/jpeg"]),
  ".jpg": new Set(["image/jpeg"]),
  ".md": new Set(["text/markdown", "text/plain"]),
  ".pdf": new Set(["application/pdf"]),
  ".png": new Set(["image/png"]),
  ".txt": new Set(["text/plain"])
};
const tolerantUploadMimeTypes = new Set(["", "application/octet-stream"]);

function result(errors: ValidationErrors): ValidationResult {
  return {
    errors,
    valid: Object.keys(errors).length === 0
  };
}

function digitsOnly(value: string): string {
  return value.replace(/\D/g, "");
}

function fileExtension(filename: string): string {
  const lastDotIndex = filename.lastIndexOf(".");
  if (lastDotIndex < 0) {
    return "";
  }

  return filename.slice(lastDotIndex).toLowerCase();
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  const payload = token.split(".")[1];
  if (!payload) {
    return null;
  }

  try {
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
    const binary = atob(padded);
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));

    const decoded = JSON.parse(new TextDecoder().decode(bytes)) as unknown;
    return typeof decoded === "object" && decoded !== null
      ? (decoded as Record<string, unknown>)
      : null;
  } catch {
    return null;
  }
}

export function validateClientForm(input: ClientFormValidationInput): ValidationResult {
  const errors: ValidationErrors = {};
  const personType = input.personType ?? "individual";
  const contractRole = input.contractRole?.trim() ?? "";
  const fullName = input.fullName?.trim() ?? input.name?.trim() ?? "";
  const legalName = input.legalName?.trim() ?? input.name?.trim() ?? "";
  const cpf = input.cpf?.trim() ?? "";
  const cnpj = input.cnpj?.trim() ?? "";
  const legacyDocument = input.document?.trim() ?? "";
  const email = input.email?.trim() ?? "";
  const birthDate = input.birthDate?.trim() ?? "";
  const phone = input.phone?.trim() ?? "";

  if (!["individual", "company"].includes(personType)) {
    errors.personType = "Selecione um tipo de pessoa válido.";
  }

  if (!contractRole && input.personType) {
    errors.contractRole = "Selecione o papel no contrato.";
  }

  if (personType === "company") {
    if (!legalName) {
      errors.legalName = "Informe a razão social.";
    }
    if (cnpj && digitsOnly(cnpj).length !== 14) {
      errors.cnpj = "Informe um CNPJ com 14 dígitos.";
    }
  } else {
    if (!fullName) {
      errors.fullName = input.personType
        ? "Informe o nome completo."
        : "Informe o nome do cliente.";
      if (!input.personType) {
        errors.name = "Informe o nome do cliente.";
      }
    }
    if (cpf && digitsOnly(cpf).length !== 11) {
      errors.cpf = "Informe um CPF com 11 dígitos.";
    }
    if (birthDate) {
      const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(birthDate);
      const iso = match ? `${match[3]}-${match[2]}-${match[1]}` : "";
      const date = iso ? new Date(`${iso}T00:00:00.000Z`) : null;
      if (
        !match ||
        !date ||
        date.getUTCFullYear() !== Number(match[3]) ||
        date.getUTCMonth() + 1 !== Number(match[2]) ||
        date.getUTCDate() !== Number(match[1])
      ) {
        errors.birthDate = "Informe uma data válida no formato dd/mm/aaaa.";
      }
    }
  }

  if (legacyDocument && !/^[A-Za-z0-9./-]+$/.test(legacyDocument)) {
    errors.document = "Use apenas números, letras, pontos, barras ou hífens.";
  }

  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    errors.email = "Informe um e-mail válido ou deixe o campo vazio.";
  }

  if (phone) {
    const phoneLength = digitsOnly(phone).length;
    if (phoneLength < 10 || phoneLength > 11) {
      errors.phone = "Informe um telefone brasileiro com DDD.";
    }
  }

  return result(errors);
}

export function validateCaseForm(input: {
  caseType?: string | null;
  clientId?: string | null;
  priority?: string | null;
  title?: string | null;
}): ValidationResult {
  const errors: ValidationErrors = {};

  if (!input.title?.trim()) {
    errors.title = "Informe o título do caso.";
  }

  if (!input.clientId?.trim()) {
    errors.clientId = "Selecione um cliente vinculado.";
  }

  if (!input.caseType?.trim()) {
    errors.caseType = "Selecione um tipo de caso.";
  }

  if (!input.priority || !allowedPriorities.has(input.priority)) {
    errors.priority = "Selecione uma prioridade válida.";
  }

  return result(errors);
}

export function validateDocumentForm(input: {
  caseId?: string | null;
  contentType?: string | null;
  filename?: string | null;
  sizeBytes?: number | string | null;
  status?: string | null;
}): ValidationResult {
  const errors: ValidationErrors = {};
  const filename = input.filename?.trim() ?? "";
  const sizeBytes = Number(input.sizeBytes);

  if (!input.caseId?.trim()) {
    errors.caseId = "Selecione um caso vinculado.";
  }

  if (!filename) {
    errors.filename = "Informe o nome do documento.";
  }

  if (!Number.isFinite(sizeBytes) || sizeBytes <= 0) {
    errors.sizeBytes = "Informe um tamanho válido em bytes.";
  }

  if (!input.contentType || !allowedContentTypes.has(input.contentType)) {
    errors.contentType = "Selecione um tipo de arquivo válido.";
  }

  if (!input.status || !allowedDocumentStatuses.has(input.status)) {
    errors.status = "Selecione um status válido.";
  }

  return result(errors);
}

export function validateDocumentUploadForm(input: {
  caseId?: string | null;
  file?: Pick<File, "name" | "size" | "type"> | null;
}): ValidationResult {
  const errors: ValidationErrors = {};
  const file = input.file ?? null;

  if (!input.caseId?.trim()) {
    errors.caseId = "Selecione um caso vinculado.";
  }

  if (!file) {
    errors.file = "Selecione um arquivo para upload.";
    return result(errors);
  }

  const extension = fileExtension(file.name);
  const allowedMimeTypes = allowedUploadMimeTypesByExtension[extension];
  const contentType = file.type.toLowerCase();
  const mimeTypeIsAcceptable =
    tolerantUploadMimeTypes.has(contentType) ||
    Boolean(allowedMimeTypes?.has(contentType));

  if (
    file.size <= 0 ||
    file.size > maxDocumentUploadSizeBytes ||
    !allowedMimeTypes ||
    !mimeTypeIsAcceptable
  ) {
    errors.file = "Use PDF, PNG, JPG, JPEG, DOCX, TXT ou MD com no máximo 10 MB.";
  }

  return result(errors);
}

export function validateDevJwtForm(token: string): ValidationResult {
  const trimmedToken = token.trim();

  if (!trimmedToken) {
    return result({
      token: "Cole o JWT dev gerado pelo backend para acessar o ambiente local."
    });
  }

  if (
    trimmedToken.split(".").length !== 3 ||
    trimmedToken.split(".").some((part) => part.length === 0)
  ) {
    return result({
      token:
        "Cole um JWT dev válido com três partes no formato header.payload.signature."
    });
  }

  const payload = decodeJwtPayload(trimmedToken);
  if (!payload) {
    return result({
      token: "O payload do JWT dev não pôde ser lido."
    });
  }

  if (typeof payload.exp === "number" && payload.exp <= Math.floor(Date.now() / 1000)) {
    return result({
      token: "JWT dev expirado. Gere um novo token no backend."
    });
  }

  const role = payload["custom:role"] ?? payload.role;
  const organizationId = payload["custom:organization_id"] ?? payload.organization_id;
  if (
    payload.token_use !== "dev" ||
    typeof payload.sub !== "string" ||
    typeof organizationId !== "string" ||
    typeof role !== "string"
  ) {
    return result({
      token:
        "JWT dev sem claims obrigatórias. Gere um token dev válido no backend."
    });
  }

  return result({});
}

export function getPasswordRequirements(password: string): PasswordRequirementState {
  return {
    hasLowercase: /[a-z]/.test(password),
    hasMinLength: password.length >= 8,
    hasSpecial: /[^A-Za-z0-9]/.test(password),
    hasUppercase: /[A-Z]/.test(password)
  };
}

export function validatePasswordChange(input: {
  confirmPassword?: string | null;
  currentPassword?: string | null;
  newPassword?: string | null;
}): PasswordValidationResult {
  const errors: ValidationErrors = {};
  const currentPassword = input.currentPassword ?? "";
  const newPassword = input.newPassword ?? "";
  const confirmPassword = input.confirmPassword ?? "";
  const requirements = getPasswordRequirements(newPassword);
  const meetsAllRequirements = Object.values(requirements).every(Boolean);

  if (!currentPassword) {
    errors.currentPassword = "Informe a senha atual.";
  }

  if (!newPassword) {
    errors.newPassword = "Informe a nova senha.";
  } else if (!meetsAllRequirements) {
    errors.newPassword = "A senha deve atender todos os requisitos.";
  }

  if (!confirmPassword) {
    errors.confirmPassword = "Confirme a nova senha.";
  } else if (confirmPassword !== newPassword) {
    errors.confirmPassword = "A confirmação deve ser igual à nova senha.";
  }

  return {
    ...result(errors),
    requirements
  };
}
