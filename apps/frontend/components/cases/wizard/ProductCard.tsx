"use client";

import { Bot, BriefcaseBusiness, Check, FileSearch, Users } from "lucide-react";
import type { ComponentType } from "react";

import { cn } from "@/lib/cn";
import { PRODUTOS, type Produto } from "@/lib/produtoConfig";

const ICONS: Record<Produto, ComponentType<{ size?: number; className?: string }>> = {
  dados_partes: Users,
  consulta_objeto: FileSearch,
  analise_contratual: BriefcaseBusiness,
  reuniao_equipe: Bot
};

type ProductCardProps = {
  produto: Produto;
  selected: boolean;
  onSelect: () => void;
};

export function ProductCard({ produto, selected, onSelect }: ProductCardProps) {
  const meta = PRODUTOS[produto];
  const Icon = ICONS[produto];

  return (
    <button
      aria-pressed={selected}
      className={cn(
        "group relative flex h-full flex-col gap-4 rounded-2xl border p-5 text-left transition-all duration-[200ms] ease-smooth",
        selected
          ? "border-[var(--teal)] bg-[var(--teal-dim)] shadow-glow-teal"
          : "border-[var(--bd2)] bg-[var(--surf2)] hover:-translate-y-0.5 hover:border-[rgba(32,201,151,0.34)] hover:bg-[var(--surf3)]"
      )}
      onClick={onSelect}
      type="button"
    >
      {selected && (
        <span className="absolute right-4 top-4 flex h-6 w-6 items-center justify-center rounded-full bg-[var(--teal-d)] text-white shadow-md">
          <Check size={14} />
        </span>
      )}

      <div
        className={cn(
          "flex h-11 w-11 items-center justify-center rounded-xl border transition",
          selected
            ? "border-[rgba(32,201,151,0.34)] bg-[var(--surf)] text-[var(--teal)]"
            : "border-[var(--bd)] bg-[var(--surf)] text-[var(--text2)] group-hover:text-[var(--teal)]"
        )}
      >
        <Icon size={20} />
      </div>

      <div className="flex-1">
        <h3 className="text-base font-semibold text-[var(--text)]">{meta.titulo}</h3>
        <p className="mt-1 text-xs leading-5 text-[var(--text2)]">{meta.descricao}</p>
      </div>

      <ul className="space-y-1.5">
        {meta.inclui.map((item) => (
          <li
            className="flex items-start gap-2 text-xs text-[var(--text2)]"
            key={item}
          >
            <Check className="mt-0.5 shrink-0 text-[var(--teal)]" size={13} />
            <span>{item}</span>
          </li>
        ))}
      </ul>

      <div className="mt-1 flex items-center justify-between border-t border-[var(--bd)] pt-3 text-[11px] text-[var(--text2)]">
        <span>
          Referência simulada{" "}
          <span className="font-semibold text-[var(--text)]">
            R$ {(meta.precoBaseCents / 100).toFixed(2).replace(".", ",")}
          </span>
        </span>
        <span>Prazo ref.: {meta.slaHoras}h</span>
      </div>
    </button>
  );
}
