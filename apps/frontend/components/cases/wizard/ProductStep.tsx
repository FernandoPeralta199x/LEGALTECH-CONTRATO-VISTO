"use client";

import { PRODUTOS, type Produto } from "@/lib/produtoConfig";

import { ProductCard } from "./ProductCard";

type ProductStepProps = {
  produto: Produto | null;
  onChange: (produto: Produto) => void;
};

export function ProductStep({ produto, onChange }: ProductStepProps) {
  const produtos = Object.keys(PRODUTOS) as Produto[];

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-[var(--text)]">
          Qual produto jurídico orienta este pedido?
        </h2>
        <p className="mt-1 text-sm text-[var(--text2)]">
          A escolha define o tipo de análise simulada e os módulos sugeridos. Nenhuma
          consulta externa ou IA real será acionada nesta etapa.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {produtos.map((p) => (
          <ProductCard
            key={p}
            onSelect={() => onChange(p)}
            produto={p}
            selected={produto === p}
          />
        ))}
      </div>
    </div>
  );
}
