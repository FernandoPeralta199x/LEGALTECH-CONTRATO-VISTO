"use client";

import { Copy, Pencil, Trash2 } from "lucide-react";

import { PAPEIS } from "@/lib/produtoConfig";

import type { Party } from "./types";

type PartyCardProps = {
  party: Party;
  index: number;
  onEdit: () => void;
  onDuplicate: () => void;
  onRemove: () => void;
};

function papelLabel(id: Party["papel"]): string {
  return PAPEIS.find((p) => p.id === id)?.label ?? id;
}

function initials(name: string): string {
  return (
    name
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((p) => p[0]?.toUpperCase() ?? "")
      .join("") || "??"
  );
}

export function PartyCard({
  party,
  index,
  onEdit,
  onDuplicate,
  onRemove
}: PartyCardProps) {
  return (
    <div className="cv-list-row flex items-center gap-4 px-5 py-4">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--teal-dim)] text-xs font-bold text-[var(--teal)]">
        {initials(party.nome)}
      </div>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-[var(--text)]">
          {party.nome}
        </p>
        <p className="mt-0.5 truncate text-[11px] text-[var(--text2)]">
          <span className="font-medium text-[var(--text2)]">{papelLabel(party.papel)}</span>
          {party.documento && <> · {party.documento}</>}
          {party.email && <> · {party.email}</>}
        </p>
      </div>

      <div className="flex shrink-0 items-center gap-1">
        <button
          aria-label={`Editar parte ${index + 1}`}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-[var(--text2)] transition hover:bg-[var(--surf3)] hover:text-[var(--text)]"
          onClick={onEdit}
          type="button"
        >
          <Pencil size={14} />
        </button>
        <button
          aria-label={`Duplicar parte ${index + 1}`}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-[var(--text2)] transition hover:bg-[var(--surf3)] hover:text-[var(--text)]"
          onClick={onDuplicate}
          type="button"
        >
          <Copy size={14} />
        </button>
        <button
          aria-label={`Remover parte ${index + 1}`}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-[var(--text2)] transition hover:bg-red-500/10 hover:text-red-400"
          onClick={onRemove}
          type="button"
        >
          <Trash2 size={14} />
        </button>
      </div>
    </div>
  );
}
