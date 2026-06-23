"use client";

import { useMemo } from "react";

import {
  usePricingLookup,
  usePricingMatrix,
} from "@/components/pricing/PricingCatalogContext";
import {
  computeProductBasePrice,
  estimarPrazoHoras,
  MATRIZ,
  MODULOS,
  PRODUTOS,
  type Modulo,
  type Produto
} from "@/lib/produtoConfig";

import { EstimateCard } from "./EstimateCard";
import { ModuleRow } from "./ModuleRow";

type ModulesStepProps = {
  produto: Produto;
  state: Record<Modulo, boolean>;
  onChange: (state: Record<Modulo, boolean>) => void;
};

export function ModulesStep({ produto, state, onChange }: ModulesStepProps) {
  const matriz = MATRIZ[produto];
  const modulos = Object.keys(matriz) as Modulo[];
  const { products, modules } = usePricingLookup();
  const matrix = usePricingMatrix();

  const isRequired = (modulo: Modulo): boolean => {
    const remote = matrix[produto]?.[modulo];
    if (remote) return remote.required === true || remote.obrigatorio === true;
    return matriz[modulo]?.obrigatorio === true;
  };

  const ativos = useMemo(
    () => modulos.filter((m) => state[m]),
    [modulos, state]
  );

  const productCents = products.get(PRODUTOS[produto].code)?.base_price_cents
    ?? computeProductBasePrice(produto);

  const valor = useMemo(() => {
    // O preço base do produto já engloba os módulos obrigatórios (bloqueados).
    // Somente módulos opcionais ativados pelo usuário incrementam o valor.
    //
    // Exceção: para `reuniao_equipe`, base = 0 e os módulos "fixo no roteiro"
    // são opt-in — eles também devem somar quando ativos.
    const includeRequired = produto === "reuniao_equipe";
    const optionalTotal = ativos.reduce((sum, modulo) => {
      if (!includeRequired && isRequired(modulo)) return sum;
      const code = MODULOS[modulo].code;
      const price = modules.get(code)?.price_cents ?? MODULOS[modulo].precoCents;
      return sum + price;
    }, 0);
    return productCents + optionalTotal;
  }, [ativos, modules, produto, productCents]);

  const prazo = useMemo(() => estimarPrazoHoras(produto, ativos), [produto, ativos]);

  function toggle(modulo: Modulo, value: boolean) {
    onChange({ ...state, [modulo]: value });
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-[var(--text)]">
          Ajuste a composição simulada
        </h2>
        <p className="mt-1 text-sm text-[var(--text2)]">
          Inclua módulos na simulação do pedido. Eles compõem o roteiro local
          e não acionam consulta externa, IA/OCR/RAG ou integração real nesta
          versão; essas capacidades seguem no roadmap.
        </p>
      </div>

      <div className="space-y-3">
        {modulos.map((m) => (
          <ModuleRow
            checked={state[m] ?? false}
            config={matriz[m]}
            key={m}
            modulo={m}
            onCheckedChange={(value) => toggle(m, value)}
          />
        ))}
      </div>

      <EstimateCard prazoHoras={prazo} valorCents={valor} />
    </div>
  );
}
