"use client";

import { FileText, Info } from "lucide-react";
import type { ReactNode } from "react";

import {
  estimarPrazoHoras,
  estimarValor,
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

export function ReviewStep({ parties, arquivo, produto, modulos }: ReviewStepProps) {
  const matriz = MATRIZ[produto];
  const ativos = (Object.keys(modulos) as Modulo[]).filter((m) => modulos[m]);
  const inativos = (Object.keys(matriz) as Modulo[]).filter((m) => !modulos[m]);

  const valor = estimarValor(produto, ativos);
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

      <EstimateCard prazoHoras={prazo} valorCents={valor} />

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
