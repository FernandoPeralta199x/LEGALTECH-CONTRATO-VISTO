"use client";

import { FileText, Lock, Upload, X } from "lucide-react";
import { useCallback, useRef, useState } from "react";

import { cn } from "@/lib/cn";

type UploadFile = {
  id: string;
  name: string;
  size: string;
  status: "waiting" | "uploading" | "done" | "error";
  progress: number;
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function UploadBox() {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback((newFiles: FileList | null) => {
    if (!newFiles) return;
    const added: UploadFile[] = Array.from(newFiles).map((f) => ({
      id: `${Date.now()}-${f.name}`,
      name: f.name,
      size: formatFileSize(f.size),
      status: "waiting" as const,
      progress: 0
    }));
    setFiles((prev) => [...prev, ...added]);

    added.forEach((file) => {
      setTimeout(() => {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id ? { ...f, status: "uploading", progress: 40 } : f
          )
        );
      }, 600);
      setTimeout(() => {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id ? { ...f, status: "uploading", progress: 80 } : f
          )
        );
      }, 1200);
      setTimeout(() => {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id ? { ...f, status: "done", progress: 100 } : f
          )
        );
      }, 1800);
    });
  }, []);

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    addFiles(e.dataTransfer.files);
  }

  function handleRemove(id: string) {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  }

  return (
    <div className="space-y-4">
      <div
        className={cn(
          "relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-12 text-center transition-all cursor-pointer",
          dragging
            ? "border-[var(--teal)] bg-[var(--teal-dim)] shadow-glow-teal"
            : "border-[var(--bd2)] bg-[var(--surf2)] hover:border-[rgba(32,201,151,0.34)] hover:bg-[var(--surf3)]"
        )}
        onDragLeave={() => setDragging(false)}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
          className="hidden"
          id="file-input"
          multiple
          onChange={(e) => addFiles(e.target.files)}
          ref={fileInputRef}
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
            size={24}
          />
        </div>
        <p className="text-sm font-semibold text-[var(--text)]">
          Arraste documentos aqui ou{" "}
          <span className="text-[var(--teal)]">clique para selecionar</span>
        </p>
        <p className="mt-1 text-xs text-[var(--text2)]">
          PDF, DOCX, TXT, JPG, PNG — até 50 MB por arquivo
        </p>
        <div className="mt-4 flex items-center gap-1.5 rounded-lg border border-[rgba(32,201,151,0.2)] bg-[var(--teal-dim)] px-3 py-2">
          <Lock className="shrink-0 text-[var(--teal)]" size={12} />
          <p className="text-[11px] text-[var(--text2)]">
            Os documentos serão processados em ambiente seguro e criptografado
          </p>
        </div>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((file) => (
            <div
              className="cv-list-row flex items-center gap-3 px-4 py-3"
              key={file.id}
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--surf3)]">
                <FileText size={16} className="text-[var(--text2)]" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-medium text-[var(--text)]">
                  {file.name}
                </p>
                <div className="mt-1.5 flex items-center gap-3">
                  <div className="h-1 flex-1 overflow-hidden rounded-full bg-[var(--surf3)]">
                    <div
                      className={cn(
                        "h-1 rounded-full transition-all duration-500",
                        file.status === "done"
                          ? "bg-brand-teal"
                          : file.status === "error"
                          ? "bg-red-500"
                          : "bg-brand-teal"
                      )}
                      style={{ width: `${file.progress}%` }}
                    />
                  </div>
                  <span
                    className={cn(
                      "shrink-0 text-[10px] font-semibold",
                      file.status === "done"
                        ? "text-[var(--teal)]"
                        : file.status === "error"
                        ? "text-red-400"
                        : file.status === "uploading"
                        ? "text-brand-teal"
                        : "text-[var(--text2)]"
                    )}
                  >
                    {file.status === "waiting" && "Aguardando"}
                    {file.status === "uploading" && `${file.progress}%`}
                    {file.status === "done" && "Enviado"}
                    {file.status === "error" && "Erro"}
                  </span>
                  <span className="shrink-0 text-[10px] text-[var(--text3)]">
                    {file.size}
                  </span>
                </div>
              </div>
              <button
                aria-label={`Remover ${file.name}`}
                className="flex h-9 min-h-9 w-9 min-w-9 shrink-0 items-center justify-center rounded-lg text-[var(--text2)] transition hover:bg-red-500/10 hover:text-red-500"
                onClick={() => handleRemove(file.id)}
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
