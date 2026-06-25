"use client";

import { FileText, Info } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

import { usePricingMatrix } from "@/components/pricing/PricingCatalogContext";
import { errorMessage } from "@/src/lib/errorMessage";
import { estimatePricing } from "@/src/services/pricing";
import {
  computeProductBasePrice,
  estimarPrazoHoras,
  MATRIZ,
  MODULOS,
  PAPEIS,
  PRODUTOS,
  type Modulo,
  type Produto
} from "@/lib/produtoConfig";

import { EstimateCard } from "./EstimateCard";
import type { Party, WizardFile } from "./types";

type ReviewStepProps = {
  parties: Party[];
  arquivo: WizardFile | null;
  produto: Produto;
  modulos: Record<Modulo, boolean>;
};

function papelLabel(id: Party["papel"]): string {
  return PAPEIS.find((p) => p.id === id)?.label ?? id;
}

function Section({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="cv-form-card px-5 py-4">
      <p className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-[var(--text2)]">
        {label}
      </p>
      {children}
    </div>
  );
}

export function ReviewStep({
  parties,
  arquivo,
  produto,
  modulos
}: ReviewStepProps) {
  const matriz = MATRIZ[produto];
  const ativos = (Object.keys(modulos) as Modulo[]).filter((m) => modulos[m]);
  const inativos = (Object.keys(matriz) as Modulo[]).filter((m) => !modulos[m]);
  const matrix = usePricingMatrix();

  const activeModuleCodes = useMemo(
    () => ativos.map((m) => MODULOS[m].code),
    [ativos]
  );

  // Chave dos inputs do cálculo oficial. Quando muda, o resultado armazenado
  // deixa de corresponder à requisição atual e o "loading" é derivado no render
  // (sem setState síncrono no corpo do effect — react-hooks/set-state-in-effect).
  const requestKey = useMemo(
    () => `${produto}|${activeModuleCodes.join(",")}`,
    [produto, activeModuleCodes]
  );

  const [result, setResult] = useState<{
    key: string;
    totalCents: number;
    error: string | null;
  } | null>(null);

  useEffect(() => {
    let cancelled = false;

    estimatePricing(produto, activeModuleCodes)
      .then((data) => {
        if (cancelled) return;
        setResult({
          key: requestKey,
          totalCents: data.total_price_cents,
          error: null
        });
      })
      .catch((err) => {
        if (cancelled) return;
        setResult({
          key: requestKey,
          totalCents: 0,
          error: errorMessage(err, "Erro ao calcular preço oficial.")
        });
      });

    return () => {
      cancelled = true;
    };
  }, [produto, activeModuleCodes, requestKey]);

  const loading = result?.key !== requestKey;
  const error = loading ? null : result?.error ?? null;

  // Fallback local: se a API ainda não respondeu ou falhou, use o cálculo
  // local baseado no catálogo estático para não deixar a tela sem valor.
  const localFallbackCents = useMemo(() => {
    const productCents = computeProductBasePrice(produto);
    const includeRequired = produto === "reuniao_equipe";
    const optionalTotal = ativos.reduce((sum, modulo) => {
      const remote = matrix[produto]?.[modulo];
      const isRequired =
        remote?.required === true || remote?.obrigatorio === true || matriz[modulo]?.obrigatorio === true;
      if (!includeRequired && isRequired) return sum;
      return sum + MODULOS[modulo].precoCents;
    }, 0);
    return productCents + optionalTotal;
  }, [produto, ativos, matrix, matriz]);

  const valor = loading || error ? localFallbackCents : result?.totalCents ?? 0;
  const prazo = estimarPrazoHoras(produto, ativos);

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-[var(--text)]">
          Revisão do Novo Pedido
        </h2>
        <p className="mt-1 text-sm text-[var(--text2)]">
          Confira os dados antes de registrar o pedido operacional. O backend
          local vai criar o request, o caso e os recursos vinculados ao mesmo
          case_id.
        </p>
      </div>

      <Section label="Produto jurídico">
        <p className="text-sm font-semibold text-[var(--text)]">
          {PRODUTOS[produto].titulo}
        </p>
        <p className="mt-1 text-xs text-[var(--text2)]">{PRODUTOS[produto].descricao}</p>
      </Section>

      <Section label={`Partes / Cliente (${parties.length})`}>
        <ul className="space-y-2">
          {parties.map((p) => (
            <li className="flex items-start gap-3 text-xs" key={p.id}>
              <span className="mt-0.5 inline-flex h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--teal)]" />
              <div className="min-w-0 flex-1">
                <p className="font-medium text-[var(--text)]">
                  {p.nome || "(sem nome)"}{" "}
                  <span className="font-normal text-[var(--text2)]">
                    · {papelLabel(p.papel)}
                  </span>
                </p>
                {(p.documento || p.email) && (
                  <p className="text-[var(--text3)]">
                    {[p.documento, p.email].filter(Boolean).join(" · ")}
                  </p>
                )}
              </div>
            </li>
          ))}
        </ul>
      </Section>

      <Section label="Contrato ou documento">
        {arquivo ? (
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--teal-dim)] text-[var(--teal)]">
              <FileText size={16} />
            </div>
            <div className="min-w-0">
              <p className="truncate text-xs font-semibold text-[var(--text)]">
                {arquivo.name}
              </p>
              <p className="text-[11px] text-[var(--text3)]">
                {(arquivo.size / 1024 / 1024).toFixed(2)} MB ·{" "}
                {arquivo.status === "done" ? "Pronto para simulação" : "Preparando…"}
              </p>
            </div>
          </div>
        ) : (
          <p className="text-xs text-[var(--text2)]">
            Nenhum contrato selecionado.
          </p>
        )}
      </Section>

      <Section label="Módulos simulados">
        <div className="space-y-3 text-xs">
          <div>
            <p className="font-semibold text-[var(--text)]">
              Incluídos na simulação ({ativos.length})
            </p>
            <p className="mt-1 text-[var(--text2)]">
              {ativos.length
                ? ativos.map((m) => MODULOS[m].titulo).join(", ")
                : "Nenhum módulo incluído na simulação."}
            </p>
          </div>
          {inativos.length > 0 && (
            <div>
              <p className="font-semibold text-[var(--text2)]">
                Fora da simulação ({inativos.length})
              </p>
              <p className="mt-1 text-[var(--text3)]">
                {inativos.map((m) => MODULOS[m].titulo).join(", ")}
              </p>
            </div>
          )}
        </div>
      </Section>

      <EstimateCard
        error={error}
        loading={loading}
        prazoHoras={prazo}
        valorCents={valor}
      />

      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2.5 text-xs text-red-200">
          <Info className="mt-0.5 shrink-0" size={14} />
          <span>{error} Valor exibido é uma referência local.</span>
        </div>
      )}

      <div className="flex items-start gap-2 rounded-lg border border-[var(--bd)] bg-[var(--surf2)] px-3 py-2.5">
        <Info className="mt-0.5 shrink-0 text-[var(--text2)]" size={14} />
        <p className="text-xs leading-5 text-[var(--text2)]">
          O registro cria dados operacionais no backend local/mock e não aciona
          IA, OCR ou integrações externas reais. Após concluir, a operação abre
          o caso criado pelo mesmo case_id.
        </p>
      </div>
    </div>
  );
}
