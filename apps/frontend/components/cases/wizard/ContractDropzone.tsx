"use client";

import { FileText, Lock, Sparkles, Upload, X } from "lucide-react";
import { useCallback, useRef, useState } from "react";

import { cn } from "@/lib/cn";

import type { WizardFile } from "./types";

const ACCEPTED = ".pdf,.docx,.png,.jpg,.jpeg";
const MAX_BYTES = 25 * 1024 * 1024; // 25 MB

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

type ContractDropzoneProps = {
  file: WizardFile | null;
  onChange: (file: WizardFile | null) => void;
};

export function ContractDropzone({ file, onChange }: ContractDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startMockPipeline = useCallback(
    (next: WizardFile) => {
      onChange({ ...next, status: "uploading", progress: 25 });
      const step1 = setTimeout(() => {
        onChange({ ...next, status: "uploading", progress: 70 });
      }, 450);
      const step2 = setTimeout(() => {
        onChange({ ...next, status: "extracting", progress: 90 });
      }, 950);
      const step3 = setTimeout(() => {
        onChange({ ...next, status: "done", progress: 100 });
      }, 1700);
      return () => {
        clearTimeout(step1);
        clearTimeout(step2);
        clearTimeout(step3);
      };
    },
    [onChange]
  );

  function handleFile(picked: File | null) {
    if (!picked) return;
    if (picked.size > MAX_BYTES) {
      setError("Arquivo acima de 25 MB. Reduza o tamanho ou envie outro.");
      return;
    }
    setError(null);
    const next: WizardFile = {
      name: picked.name,
      size: picked.size,
      type: picked.type,
      status: "uploading",
      progress: 0
    };
    startMockPipeline(next);
  }

  if (file) {
    return (
      <FilePreview
        file={file}
        onRemove={() => {
          onChange(null);
          if (inputRef.current) inputRef.current.value = "";
        }}
      />
    );
  }

  return (
    <div className="space-y-3">
      <div
        className={cn(
          "relative flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-14 text-center transition-all",
          dragging
            ? "border-[var(--teal)] bg-[var(--teal-dim)] shadow-glow-teal"
            : "border-[var(--bd2)] bg-[var(--surf2)] hover:border-[rgba(32,201,151,0.34)] hover:bg-[var(--surf3)]"
        )}
        onClick={() => inputRef.current?.click()}
        onDragLeave={() => setDragging(false)}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handleFile(e.dataTransfer.files?.[0] ?? null);
        }}
      >
        <input
          accept={ACCEPTED}
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
          ref={inputRef}
          type="file"
        />
        <div
          className={cn(
            "mb-4 flex h-14 w-14 items-center justify-center rounded-full border transition",
            dragging
              ? "border-[rgba(32,201,151,0.34)] bg-[var(--teal-dim)]"
              : "border-[var(--bd)] bg-[var(--surf)]"
          )}
        >
          <Upload
            className={dragging ? "text-[var(--teal)]" : "text-[var(--text2)]"}
            size={22}
          />
        </div>
        <p className="text-sm font-semibold text-[var(--text)]">
          Anexe localmente o contrato ou{" "}
          <span className="text-[var(--teal)]">clique para selecionar</span>
        </p>
        <p className="mt-1 text-xs text-[var(--text2)]">
          PDF, DOCX, PNG, JPG ou JPEG — até 25 MB
        </p>
        <div className="mt-4 flex items-center gap-1.5 rounded-lg border border-[rgba(32,201,151,0.2)] bg-[var(--teal-dim)] px-3 py-2">
          <Lock className="shrink-0 text-[var(--teal)]" size={12} />
          <p className="text-[11px] text-[var(--text2)]">
            Simulação local: anexo usado apenas no Wizard, sem upload real para
            S3 ou backend nesta versão.
          </p>
        </div>
      </div>

      {error && (
        <p className="text-xs text-red-400" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

function FilePreview({
  file,
  onRemove
}: {
  file: WizardFile;
  onRemove: () => void;
}) {
  return (
    <div className="space-y-3">
      <div className="cv-form-card flex items-center gap-4 px-5 py-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[var(--teal-dim)] text-[var(--teal)]">
          <FileText size={20} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-[var(--text)]">{file.name}</p>
          <div className="mt-2 flex items-center gap-3">
            <div className="h-1 flex-1 overflow-hidden rounded-full bg-[var(--surf3)]">
              <div
                className={cn(
                  "h-1 rounded-full transition-all duration-500",
                  file.status === "error" ? "bg-red-500" : "bg-brand-teal"
                )}
                style={{ width: `${file.progress}%` }}
              />
            </div>
            <span className="shrink-0 text-[11px] font-semibold uppercase tracking-wider text-[var(--text2)]">
              {file.status === "uploading" && `Preparando ${file.progress}%`}
              {file.status === "extracting" && "Simulando leitura…"}
              {file.status === "done" && "Pronto para simulação"}
              {file.status === "error" && "Erro"}
            </span>
            <span className="shrink-0 text-[11px] text-[var(--text3)]">
              {formatSize(file.size)}
            </span>
          </div>
        </div>
        <button
          aria-label="Remover arquivo"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-[var(--text2)] transition hover:bg-red-500/10 hover:text-red-400"
          onClick={onRemove}
          type="button"
        >
          <X size={14} />
        </button>
      </div>

      {file.status === "done" && (
        <div className="flex items-start gap-2 rounded-lg border border-[rgba(96,165,250,0.2)] bg-[var(--blue-dim)] px-3 py-2.5">
          <Sparkles className="mt-0.5 shrink-0 text-[var(--blue)]" size={14} />
          <p className="text-xs leading-5 text-[var(--text2)]">
            Pré-leitura visual da simulação pronta. Esta versão não executa
            OCR, IA/RAG ou extração real de texto; esses recursos seguem no
            roadmap.
          </p>
        </div>
      )}
    </div>
  );
}
