"use client";

import { ArrowLeft, ArrowRight, Check } from "lucide-react";

import { Button } from "@/components/Button";

type WizardActionsProps = {
  step: number;
  totalSteps: number;
  canAdvance: boolean;
  submitting?: boolean;
  onBack: () => void;
  onNext: () => void;
  onSubmit: () => void;
  nextLabel?: string;
  submitLabel?: string;
};

export function WizardActions({
  step,
  totalSteps,
  canAdvance,
  submitting,
  onBack,
  onNext,
  onSubmit,
  nextLabel = "Continuar",
  submitLabel = "Registrar pedido"
}: WizardActionsProps) {
  const isLast = step === totalSteps;

  return (
    <div className="mt-8 flex items-center justify-between gap-3 border-t border-[var(--bd)] pt-6">
      <Button
        disabled={step === 1}
        icon={<ArrowLeft size={15} />}
        onClick={onBack}
        variant="secondary"
      >
        Voltar
      </Button>

      {isLast ? (
        <Button
          disabled={!canAdvance || submitting}
          iconRight={<Check size={16} />}
          loading={submitting}
          onClick={onSubmit}
          size="lg"
          variant="primary"
        >
          {submitting ? "Registrando pedido..." : submitLabel}
        </Button>
      ) : (
        <Button
          disabled={!canAdvance}
          iconRight={<ArrowRight size={15} />}
          onClick={onNext}
          variant="primary"
        >
          {nextLabel}
        </Button>
      )}
    </div>
  );
}
