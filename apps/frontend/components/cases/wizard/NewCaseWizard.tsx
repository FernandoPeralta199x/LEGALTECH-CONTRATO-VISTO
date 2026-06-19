"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { WizardActions, WizardShell } from "@/components/wizard";
import { Notification } from "@/components/Notification";
import {
  MATRIZ,
  type Modulo,
  type Produto
} from "@/lib/produtoConfig";
import { submitWizardRequest } from "@/src/services/cases";

import { ContractStep } from "./ContractStep";
import { ModulesStep } from "./ModulesStep";
import { PartiesStep } from "./PartiesStep";
import { ProductStep } from "./ProductStep";
import { ReviewStep } from "./ReviewStep";
import {
  newParty,
  partyIsComplete,
  type Party,
  type WizardFile
} from "./types";

const TOTAL_STEPS = 5;

const STEP_TITLES: Record<number, string> = {
  1: "Identifique partes e cliente",
  2: "Anexe contrato ou documento",
  3: "Escolha o produto jurídico",
  4: "Ajuste os módulos da simulação",
  5: "Revise a simulação"
};

function makeIdempotencyKey(): string {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }

  return `wizard-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function defaultModulesFor(produto: Produto): Record<Modulo, boolean> {
  const matriz = MATRIZ[produto];
  const next = {} as Record<Modulo, boolean>;
  (Object.keys(matriz) as Modulo[]).forEach((m) => {
    next[m] = matriz[m].default;
  });
  return next;
}

export function NewCaseWizard() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [submitNotice, setSubmitNotice] = useState<{
    tone: "error" | "success" | "warning";
    title: string;
    description: string;
  } | null>(null);
  const [idempotencyKey] = useState(makeIdempotencyKey);

  const [parties, setParties] = useState<Party[]>(() => [newParty()]);
  const [arquivo, setArquivo] = useState<WizardFile | null>(null);
  const [produto, setProduto] = useState<Produto | null>(null);
  const [modulos, setModulos] = useState<Record<Modulo, boolean>>(
    () => ({}) as Record<Modulo, boolean>
  );

  function handleProductChange(next: Produto) {
    setProduto(next);
    if (next !== produto) {
      setModulos(defaultModulesFor(next));
    }
  }

  const canAdvance = useMemo(() => {
    if (step === 1) {
      return parties.length > 0 && parties.every(partyIsComplete);
    }
    if (step === 2) {
      return Boolean(arquivo && arquivo.status === "done");
    }
    if (step === 3) {
      return Boolean(produto);
    }
    if (step === 4) {
      return Boolean(produto);
    }
    if (step === 5) {
      return Boolean(produto && arquivo?.status === "done");
    }
    return false;
  }, [step, parties, arquivo, produto]);

  async function handleSubmit() {
    if (!canAdvance || !produto || submitting) return;
    setSubmitting(true);
    setSubmitNotice(null);

    try {
      const result = await submitWizardRequest({
        arquivo,
        idempotencyKey,
        modulos,
        parties,
        produto
      });

      if (!result.data.caseId) {
        throw new Error("A API não retornou case_id para o pedido.");
      }

      setSubmitNotice({
        tone: result.source === "api" ? "success" : "warning",
        title:
          result.source === "api"
            ? "Pedido operacional criado"
            : "Fallback local registrado",
        description:
          result.source === "api"
            ? `Caso ${result.data.caseCode} criado no backend operacional local. Abrindo a operação do caso.`
            : `Backend indisponível; caso ${result.data.caseCode} salvo neste navegador como fallback local. Abrindo a operação do caso local.`
      });
      await new Promise((resolve) => setTimeout(resolve, 600));
      router.push(`/cases/${result.data.caseId}`);
    } catch (error) {
      setSubmitting(false);
      setSubmitNotice({
        tone: "error",
        title: "Não foi possível registrar o pedido",
        description:
          error instanceof Error
            ? error.message
            : "O backend não concluiu a criação operacional do caso."
      });
    }
  }

  return (
    <WizardShell
      backHref="/cases"
      description="Preencha as informações do pedido. Ao concluir, o backend operacional cria o request, o caso e os recursos locais vinculados ao mesmo case_id."
      step={step}
      title={STEP_TITLES[step]}
      totalSteps={TOTAL_STEPS}
    >
      {submitNotice && (
        <Notification compact tone={submitNotice.tone} title={submitNotice.title}>
          {submitNotice.description}
        </Notification>
      )}

      {step === 1 && <PartiesStep onChange={setParties} parties={parties} />}
      {step === 2 && <ContractStep arquivo={arquivo} onChange={setArquivo} />}
      {step === 3 && <ProductStep onChange={handleProductChange} produto={produto} />}
      {step === 4 && produto && (
        <ModulesStep onChange={setModulos} produto={produto} state={modulos} />
      )}
      {step === 5 && produto && (
        <ReviewStep
          arquivo={arquivo}
          modulos={modulos}
          parties={parties}
          produto={produto}
        />
      )}

      <WizardActions
        canAdvance={canAdvance}
        onBack={() => setStep((s) => Math.max(1, s - 1))}
        onNext={() => setStep((s) => Math.min(TOTAL_STEPS, s + 1))}
        onSubmit={handleSubmit}
        submitLabel="Registrar pedido"
        step={step}
        submitting={submitting}
        totalSteps={TOTAL_STEPS}
      />
    </WizardShell>
  );
}
