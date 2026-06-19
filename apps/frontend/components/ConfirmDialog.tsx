import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/Button";

type ConfirmDialogProps = {
  cancelLabel?: string;
  confirmLabel?: string;
  description: string;
  loading?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  open: boolean;
  title: string;
  variant?: "danger" | "primary";
};

export function ConfirmDialog({
  cancelLabel = "Cancelar",
  confirmLabel = "Confirmar",
  description,
  loading = false,
  onCancel,
  onConfirm,
  open,
  title,
  variant = "primary"
}: ConfirmDialogProps) {
  if (!open) {
    return null;
  }

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4 py-8 backdrop-blur-sm"
      role="dialog"
    >
      <section className="cv-card w-full max-w-md p-5 shadow-2xl">
        <div className="flex gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-[rgba(249,115,22,0.24)] bg-[var(--orange-dim)] text-[var(--orange)]">
            <AlertTriangle aria-hidden="true" size={18} />
          </span>
          <div>
            <h2 className="text-sm font-semibold text-[var(--text)]">{title}</h2>
            <p className="mt-1 text-xs leading-5 text-[var(--text2)]">{description}</p>
          </div>
        </div>

        <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button disabled={loading} onClick={onCancel} variant="secondary">
            {cancelLabel}
          </Button>
          <Button loading={loading} onClick={onConfirm} variant={variant === "danger" ? "danger" : "primary"}>
            {confirmLabel}
          </Button>
        </div>
      </section>
    </div>
  );
}
