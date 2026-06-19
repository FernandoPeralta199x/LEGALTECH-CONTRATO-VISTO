"use client";

import { Check, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "@/components/Button";
import { FormField, SelectInput, TextInput } from "@/components/FormField";
import {
  isValidCnpj,
  isValidCpf,
  isValidEmail,
  isValidPhone,
  maskDocumento,
  maskPhone
} from "@/lib/cpfCnpj";
import { PAPEIS } from "@/lib/produtoConfig";

import type { Party } from "./types";

type PartyFormProps = {
  party: Party;
  index: number;
  totalParties: number;
  onChange: (party: Party) => void;
  onSave: () => void;
  onRemove: () => void;
};

export function PartyForm({
  party,
  index,
  totalParties,
  onChange,
  onSave,
  onRemove
}: PartyFormProps) {
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const today = new Date().toISOString().slice(0, 10);

  const errors = useMemo(() => {
    const e: Record<string, string> = {};
    if (!party.nome.trim()) {
      e.nome =
        party.tipoPessoa === "pj"
          ? "Informe a razão social."
          : "Informe o nome completo.";
    }
    if (party.documento) {
      const ok =
        party.tipoPessoa === "pj"
          ? isValidCnpj(party.documento)
          : isValidCpf(party.documento);
      if (!ok) {
        e.documento = party.tipoPessoa === "pj" ? "CNPJ inválido." : "CPF inválido.";
      }
    }
    if (party.email && !isValidEmail(party.email)) {
      e.email = "E-mail inválido.";
    }
    if (party.telefone && !isValidPhone(party.telefone)) {
      e.telefone = "Telefone inválido.";
    }
    if (party.tipoPessoa === "pf" && party.birthDate && party.birthDate > today) {
      e.birthDate = "Data de nascimento não pode ser futura.";
    }
    return e;
  }, [party, today]);

  const canSave =
    !errors.nome &&
    !errors.documento &&
    !errors.email &&
    !errors.telefone &&
    !errors.birthDate;

  function update<K extends keyof Party>(key: K, value: Party[K]) {
    onChange({ ...party, [key]: value });
  }

  function setError(field: string) {
    setTouched((prev) => ({ ...prev, [field]: true }));
  }

  return (
    <div className="cv-form-card p-5">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-[var(--text2)]">
          Parte {index + 1}
        </p>
        {totalParties > 1 && (
          <button
            className="flex items-center gap-1.5 text-[11px] font-medium text-red-400 transition hover:text-red-300"
            onClick={onRemove}
            type="button"
          >
            <Trash2 size={12} />
            Remover
          </button>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label="Tipo de pessoa" required>
          <SelectInput
            onChange={(e) => {
              const value = e.target.value as Party["tipoPessoa"];
              onChange({ ...party, tipoPessoa: value, documento: "" });
            }}
            value={party.tipoPessoa}
          >
            <option value="pf">Pessoa física</option>
            <option value="pj">Pessoa jurídica</option>
          </SelectInput>
        </FormField>

        <FormField label="Papel no contrato" required>
          <SelectInput
            onChange={(e) => update("papel", e.target.value as Party["papel"])}
            value={party.papel}
          >
            {PAPEIS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </SelectInput>
        </FormField>

        <FormField
          error={touched.nome ? errors.nome : undefined}
          label={party.tipoPessoa === "pj" ? "Razão social" : "Nome completo"}
          required
        >
          <TextInput
            invalid={touched.nome && Boolean(errors.nome)}
            onBlur={() => setError("nome")}
            onChange={(e) => update("nome", e.target.value)}
            placeholder={
              party.tipoPessoa === "pj"
                ? "Ex: Acme Comércio Ltda"
                : "Ex: João da Silva"
            }
            value={party.nome}
          />
        </FormField>

        {party.tipoPessoa === "pj" && (
          <FormField label="Nome fantasia">
            <TextInput
              onChange={(e) => update("nomeFantasia", e.target.value)}
              placeholder="Opcional"
              value={party.nomeFantasia ?? ""}
            />
          </FormField>
        )}

        <FormField
          error={touched.documento ? errors.documento : undefined}
          label={party.tipoPessoa === "pj" ? "CNPJ" : "CPF"}
        >
          <TextInput
            inputMode="numeric"
            invalid={touched.documento && Boolean(errors.documento)}
            onBlur={() => setError("documento")}
            onChange={(e) => update("documento", maskDocumento(e.target.value, party.tipoPessoa))}
            placeholder={party.tipoPessoa === "pj" ? "00.000.000/0000-00" : "000.000.000-00"}
            value={party.documento}
          />
        </FormField>

        {party.tipoPessoa === "pf" && (
          <>
            <FormField label="RG">
              <TextInput
                onChange={(e) => update("rg", e.target.value)}
                placeholder="Informe o RG"
                value={party.rg ?? ""}
              />
            </FormField>

            <FormField
              error={touched.birthDate ? errors.birthDate : undefined}
              label="Data de nascimento"
            >
              <TextInput
                invalid={touched.birthDate && Boolean(errors.birthDate)}
                max={today}
                onBlur={() => setError("birthDate")}
                onChange={(e) => update("birthDate", e.target.value)}
                type="date"
                value={party.birthDate ?? ""}
              />
            </FormField>
          </>
        )}

        <FormField error={touched.email ? errors.email : undefined} label="E-mail">
          <TextInput
            invalid={touched.email && Boolean(errors.email)}
            onBlur={() => setError("email")}
            onChange={(e) => update("email", e.target.value)}
            placeholder="contato@exemplo.com"
            type="email"
            value={party.email}
          />
        </FormField>

        <FormField error={touched.telefone ? errors.telefone : undefined} label="Telefone">
          <TextInput
            inputMode="tel"
            invalid={touched.telefone && Boolean(errors.telefone)}
            onBlur={() => setError("telefone")}
            onChange={(e) => update("telefone", maskPhone(e.target.value))}
            placeholder="(11) 98888-7777"
            value={party.telefone}
          />
        </FormField>

        <div className="sm:col-span-2">
          <FormField label="Endereço">
            <TextInput
              onChange={(e) => update("endereco", e.target.value)}
              placeholder="Rua, número, bairro, cidade — UF"
              value={party.endereco}
            />
          </FormField>
        </div>
      </div>

      <div className="mt-5 flex items-center justify-end gap-2">
        <Button
          disabled={!canSave || !party.nome.trim()}
          icon={<Check size={15} />}
          onClick={onSave}
          size="sm"
          variant="primary"
        >
          Salvar parte
        </Button>
      </div>
    </div>
  );
}
