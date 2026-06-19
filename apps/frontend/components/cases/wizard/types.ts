import type { Modulo, Papel, Produto, TipoPessoa } from "@/lib/produtoConfig";

export type Party = {
  id: string;
  tipoPessoa: TipoPessoa;
  papel: Papel;
  nome: string;
  nomeFantasia?: string;
  documento: string;
  rg?: string;
  birthDate?: string;
  email: string;
  telefone: string;
  endereco: string;
  _editing: boolean;
};

export type WizardFile = {
  name: string;
  size: number;
  type: string;
  /** Indicador de extração — mock até integrarmos com presigned upload + OCR. */
  status: "uploading" | "extracting" | "done" | "error";
  progress: number;
};

export type WizardState = {
  parties: Party[];
  arquivo: WizardFile | null;
  produto: Produto | null;
  modulos: Record<Modulo, boolean>;
};

let counter = 0;

export function newPartyId(): string {
  counter += 1;
  return `party-${Date.now().toString(36)}-${counter}`;
}

export function newParty(papel: Papel = "contratante"): Party {
  return {
    id: newPartyId(),
    tipoPessoa: "pf",
    papel,
    nome: "",
    documento: "",
    rg: "",
    birthDate: "",
    email: "",
    telefone: "",
    endereco: "",
    _editing: true
  };
}

export function partyIsComplete(party: Party): boolean {
  return Boolean(party.nome.trim() && party.papel && party.tipoPessoa);
}
