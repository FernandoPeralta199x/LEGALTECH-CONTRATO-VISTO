"use client";

import { Plus } from "lucide-react";

import { Button } from "@/components/Button";

import { PartyCard } from "./PartyCard";
import { PartyForm } from "./PartyForm";
import { newParty, type Party } from "./types";

type PartiesStepProps = {
  parties: Party[];
  onChange: (parties: Party[]) => void;
};

export function PartiesStep({ parties, onChange }: PartiesStepProps) {
  function updateAt(idx: number, party: Party) {
    onChange(parties.map((p, i) => (i === idx ? party : p)));
  }

  function removeAt(idx: number) {
    onChange(parties.filter((_, i) => i !== idx));
  }

  function duplicateAt(idx: number) {
    const source = parties[idx];
    const clone: Party = {
      ...source,
      id: newParty().id,
      nome: `${source.nome} (cópia)`,
      _editing: true
    };
    const next = [...parties];
    next.splice(idx + 1, 0, clone);
    onChange(next);
  }

  function setEditing(idx: number, editing: boolean) {
    onChange(parties.map((p, i) => (i === idx ? { ...p, _editing: editing } : p)));
  }

  function addParty() {
    const fallbackPapel = parties.length === 0 ? "contratante" : "contratada";
    onChange([...parties, newParty(fallbackPapel)]);
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-[var(--text)]">Dados das partes</h2>
        <p className="mt-1 text-sm text-[var(--text2)]">
          Adicione todas as partes envolvidas no contrato. Você pode editar, duplicar
          ou remover a qualquer momento.
        </p>
      </div>

      <div className="space-y-3">
        {parties.map((party, idx) =>
          party._editing ? (
            <PartyForm
              index={idx}
              key={party.id}
              onChange={(updated) => updateAt(idx, updated)}
              onRemove={() => removeAt(idx)}
              onSave={() => setEditing(idx, false)}
              party={party}
              totalParties={parties.length}
            />
          ) : (
            <PartyCard
              index={idx}
              key={party.id}
              onDuplicate={() => duplicateAt(idx)}
              onEdit={() => setEditing(idx, true)}
              onRemove={() => removeAt(idx)}
              party={party}
            />
          )
        )}
      </div>

      <Button
        fullWidth
        icon={<Plus size={15} />}
        onClick={addParty}
        variant="secondary"
      >
        Adicionar outra parte
      </Button>
    </div>
  );
}
