"use client";

import { Check, X } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";

import { Button } from "@/components/Button";
import { ThemeToggle } from "@/components/ThemeToggle";
import { cn } from "@/lib/cn";
import { errorMessage } from "@/src/lib/errorMessage";
import { saveDevSession } from "@/src/services/auth";
import { verifyEmail } from "@/src/services/authApi";
import { DEV_ROLES, type DevRole } from "@/src/types/auth";

type ToastState = {
  message: string;
  tone: "error" | "success" | "warning";
} | null;

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "";
  const token = searchParams.get("token") || "";

  const [toast, setToast] = useState<ToastState>(null);
  const [loading, setLoading] = useState(false);
  const [manualToken, setManualToken] = useState(token);
  const [manualEmail, setManualEmail] = useState(email);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading) return;

    setToast(null);
    setLoading(true);

    try {
      const result = await verifyEmail({
        email: manualEmail,
        token: manualToken,
      });

      await saveDevSession({
        email: result.user.email,
        role: (DEV_ROLES.includes(result.user.role as DevRole)
          ? result.user.role
          : "client") as DevRole,
        token: result.access_token,
      });

      setToast({
        message: "E-mail confirmado. Redirecionando...",
        tone: "success",
      });
      await new Promise((resolve) => setTimeout(resolve, 450));
      router.replace("/dashboard");
    } catch (err) {
      setToast({
        message: errorMessage(err, "Token de verificação inválido."),
        tone: "error",
      });
      setLoading(false);
    }
  }

  return (
    <main className="cv-login-shell relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-10">
      <div className="pointer-events-none absolute inset-0 opacity-45 noise" />
      <Link
        className="absolute left-5 top-5 z-10 flex items-center gap-2 text-xs font-semibold text-[var(--text2)] transition hover:text-[var(--teal)]"
        href="/login"
      >
        <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--bd)] bg-[var(--surf2)]">
          <X size={16} />
        </span>
        Voltar para login
      </Link>
      <ThemeToggle className="absolute right-5 top-5 z-10" />

      <section
        aria-label="Verificação de e-mail"
        className="cv-login-card relative z-10 w-full max-w-md px-4 pb-8 pt-14 sm:px-10 sm:pb-12 sm:pt-16"
      >
        <div className="mb-6 text-center">
          <h1 className="text-lg font-semibold text-[var(--text)]">
            Confirme seu e-mail
          </h1>
          <p className="mt-1 text-xs text-[var(--text2)]">
            Insira seu e-mail e o token de confirmação.
          </p>
        </div>

        {toast && (
          <div
            className={cn(
              "mb-5 flex items-start gap-2 rounded-lg border px-3 py-2.5 text-xs",
              toast.tone === "error" &&
                "border-red-500/30 bg-red-500/10 text-red-200",
              toast.tone === "success" &&
                "border-emerald-500/30 bg-emerald-500/10 text-emerald-200",
              toast.tone === "warning" &&
                "border-amber-500/30 bg-amber-500/10 text-amber-200"
            )}
            role="alert"
          >
            {toast.tone === "success" && (
              <Check size={14} className="mt-0.5 shrink-0" />
            )}
            {toast.tone === "error" && (
              <X size={14} className="mt-0.5 shrink-0" />
            )}
            <span className="flex-1">{toast.message}</span>
          </div>
        )}

        <form className="space-y-4" onSubmit={handleSubmit}>
          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-[var(--text)]">E-mail</span>
            <input
              autoComplete="email"
              className={inputClass}
              onChange={(event) => setManualEmail(event.target.value)}
              placeholder="seu@email.com"
              required
              type="email"
              value={manualEmail}
            />
          </label>

          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-[var(--text)]">
              Token de confirmação
            </span>
            <input
              className={inputClass}
              onChange={(event) => setManualToken(event.target.value)}
              placeholder="Cole o token do link ou do log"
              required
              type="text"
              value={manualToken}
            />
          </label>

          <Button
            className="w-full"
            icon={<Check size={16} />}
            loading={loading}
            type="submit"
            variant="primary"
          >
            Confirmar e acessar
          </Button>
        </form>

        <div className="mt-6 rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3 text-[11px] leading-5 text-emerald-200">
          <strong className="text-emerald-100">Ambiente local:</strong>{" "}
          o token de confirmação é enviado apenas em log. Em produção o link é
          enviado por e-mail. O token nunca fica armazenado no navegador antes
          da confirmação.
        </div>
      </section>
    </main>
  );
}

const inputClass =
  "w-full rounded-lg border border-[var(--border)] bg-[var(--surf2)] px-3 py-2.5 text-sm text-[var(--text)] placeholder:text-[var(--text3)] focus:outline-none focus:ring-2 focus:ring-brand-teal/30";

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center text-[var(--text2)]">
          Carregando...
        </div>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  );
}
