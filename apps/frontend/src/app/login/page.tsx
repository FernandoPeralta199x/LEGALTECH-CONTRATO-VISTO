"use client";

import {
  ArrowRight,
  Check,
  Eye,
  EyeOff,
  Lock,
  Mail,
  ShieldCheck,
  Sparkles,
  User,
  X
} from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";

import { Button } from "@/components/Button";
import { ThemeToggle } from "@/components/ThemeToggle";
import { cn } from "@/lib/cn";
import { errorMessage } from "@/src/lib/errorMessage";
import { saveDevSession } from "@/src/services/auth";
import { login, register as registerUser, verifyEmail } from "@/src/services/authApi";
import { useDevSession } from "@/src/lib/useDevSession";
import { validatePasswordChange } from "@/src/lib/validation";
import { DEV_ROLES, type DevRole } from "@/src/types/auth";

type Tab = "login" | "register";
type ToastState = {
  message: string;
  tone: "error" | "success" | "warning";
} | null;

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = searchParams.get("next") || "/dashboard";
  const session = useDevSession();

  const [tab, setTab] = useState<Tab>("login");
  const [toast, setToast] = useState<ToastState>(null);
  const [loading, setLoading] = useState(false);

  // Login state
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [showLoginPassword, setShowLoginPassword] = useState(false);

  // Register state
  const [name, setName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerRole, setRegisterRole] = useState<DevRole>("analyst");
  const [registerPassword, setRegisterPassword] = useState("");
  const [showRegisterPassword, setShowRegisterPassword] = useState(false);
  const [verificationToken, setVerificationToken] = useState("");
  const [registeredEmail, setRegisteredEmail] = useState("");
  const [showVerification, setShowVerification] = useState(false);

  const passwordValidation = validatePasswordChange({
    confirmPassword: registerPassword,
    currentPassword: "",
    newPassword: registerPassword
  });

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading) return;

    setToast(null);
    setLoading(true);

    try {
      const result = await login({
        email: loginEmail,
        password: loginPassword
      });

      await saveDevSession({
        email: result.user.email,
        role: (DEV_ROLES.includes(result.user.role as DevRole)
          ? result.user.role
          : "client") as DevRole,
        token: result.access_token
      });

      setToast({
        message: "Login realizado. Redirecionando...",
        tone: "success"
      });
      await new Promise((resolve) => setTimeout(resolve, 450));
      router.replace(nextPath.startsWith("/") ? nextPath : "/dashboard");
    } catch (err) {
      setToast({
        message: errorMessage(err, "E-mail ou senha inválidos."),
        tone: "error"
      });
      setLoading(false);
    }
  }

  async function handleRegister(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading) return;

    if (!passwordValidation.valid) {
      setToast({
        message:
          passwordValidation.errors.newPassword ??
          "A senha não atende aos requisitos mínimos.",
        tone: "error"
      });
      return;
    }

    setToast(null);
    setLoading(true);

    try {
      const result = await registerUser({
        email: registerEmail,
        name,
        password: registerPassword,
        role: registerRole
      });

      setRegisteredEmail(result.email);
      setVerificationToken(result.verification_token || "");
      setShowVerification(true);
      setToast({
        message:
          "Cadastro criado. Confirme o e-mail para ativar a conta. No ambiente local o token aparece abaixo.",
        tone: "success"
      });
    } catch (err) {
      setToast({
        message: errorMessage(err, "Não foi possível criar o cadastro."),
        tone: "error"
      });
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading) return;

    setToast(null);
    setLoading(true);

    try {
      const result = await verifyEmail({
        email: registeredEmail,
        token: verificationToken
      });

      await saveDevSession({
        email: result.user.email,
        role: (DEV_ROLES.includes(result.user.role as DevRole)
          ? result.user.role
          : "client") as DevRole,
        token: result.access_token
      });

      setToast({
        message: "E-mail confirmado. Redirecionando...",
        tone: "success"
      });
      await new Promise((resolve) => setTimeout(resolve, 450));
      router.replace(nextPath.startsWith("/") ? nextPath : "/dashboard");
    } catch (err) {
      setToast({
        message: errorMessage(err, "Token de verificação inválido."),
        tone: "error"
      });
      setLoading(false);
    }
  }

  function switchTab(nextTab: Tab) {
    setTab(nextTab);
    setToast(null);
    setShowVerification(false);
  }

  return (
    <main className="cv-login-shell relative flex items-start justify-center overflow-hidden px-4 py-10">
      <div className="pointer-events-none absolute inset-0 opacity-45 noise" />
      <Link
        className="absolute left-5 top-5 z-10 flex items-center gap-2 text-xs font-semibold text-[var(--text2)] transition hover:text-[var(--teal)]"
        href="/"
      >
        <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--bd)] bg-[var(--surf2)]">
          <ShieldCheck size={16} />
        </span>
        Contrato Visto
      </Link>
      <ThemeToggle className="absolute right-5 top-5 z-10" />

      <section
        aria-label="Autenticação"
        className="cv-login-card relative z-10 w-full max-w-md px-4 pb-8 pt-14 sm:px-10 sm:pb-12 sm:pt-16"
      >
        <div aria-hidden="true" className="absolute -top-11 left-1/2 h-[88px] w-[88px] -translate-x-1/2">
          <div className="absolute -inset-3 animate-pulse rounded-full bg-[radial-gradient(circle,rgba(95,200,152,0.24)_0%,transparent_68%)]" />
          <div className="absolute -inset-[3px] animate-spin-slow rounded-full bg-[conic-gradient(from_0deg,transparent_0%,transparent_28%,rgba(95,200,152,.12)_40%,rgba(95,200,152,.88)_53%,rgba(190,255,225,1)_57%,rgba(95,200,152,.88)_61%,rgba(95,200,152,.12)_72%,transparent_84%,transparent_100%)]" />
          <div className="cv-login-avatar absolute inset-0 flex items-center justify-center rounded-full bg-[linear-gradient(148deg,#2a6068,#021f23)] text-emerald-100">
            <ShieldCheck size={34} />
          </div>
        </div>

        <div className="mb-5 flex flex-wrap items-center justify-between gap-2">
          <p className="text-[10px] font-bold uppercase text-[var(--text3)]">
            Acesso à plataforma
          </p>
          <span className="cv-badge cv-badge-teal">
            <Sparkles size={12} />
            Ambiente local
          </span>
        </div>

        <div className="mb-6 grid grid-cols-2 gap-1 rounded-lg border border-[var(--bd)] bg-[var(--surf2)] p-1">
          <button
            className={cn(
              "rounded-md px-3 py-2 text-xs font-semibold transition",
              tab === "login"
                ? "bg-brand-teal text-white shadow"
                : "text-[var(--text2)] hover:text-[var(--text)]"
            )}
            onClick={() => switchTab("login")}
            type="button"
          >
            Login
          </button>
          <button
            className={cn(
              "rounded-md px-3 py-2 text-xs font-semibold transition",
              tab === "register"
                ? "bg-brand-teal text-white shadow"
                : "text-[var(--text2)] hover:text-[var(--text)]"
            )}
            onClick={() => switchTab("register")}
            type="button"
          >
            Cadastro
          </button>
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
            {toast.tone === "success" && <Check size={14} className="mt-0.5 shrink-0" />}
            {toast.tone === "error" && <X size={14} className="mt-0.5 shrink-0" />}
            <span className="flex-1">{toast.message}</span>
          </div>
        )}

        {tab === "login" ? (
          <form className="space-y-4" onSubmit={handleLogin}>
            <Field label="E-mail" icon={<Mail size={15} />}>
              <input
                autoComplete="email"
                className={inputClass}
                onChange={(event) => setLoginEmail(event.target.value)}
                placeholder="seu@email.com"
                required
                type="email"
                value={loginEmail}
              />
            </Field>

            <Field label="Senha" icon={<Lock size={15} />}>
              <div className="relative">
                <input
                  autoComplete="current-password"
                  className={`${inputClass} pr-10`}
                  onChange={(event) => setLoginPassword(event.target.value)}
                  placeholder="Sua senha forte"
                  required
                  type={showLoginPassword ? "text" : "password"}
                  value={loginPassword}
                />
                <button
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--text3)] hover:text-[var(--text)]"
                  onClick={() => setShowLoginPassword((current) => !current)}
                  tabIndex={-1}
                  type="button"
                >
                  {showLoginPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </Field>

            <Button
              className="w-full"
              icon={<ArrowRight size={16} />}
              loading={loading}
              type="submit"
              variant="primary"
            >
              Entrar
            </Button>
          </form>
        ) : showVerification ? (
          <form className="space-y-4" onSubmit={handleVerify}>
            <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3 text-xs text-emerald-200">
              Cadastro criado para <strong>{registeredEmail}</strong>. Em produção o
              link seria enviado por e-mail; no ambiente local digite qualquer
              token não vazio para confirmar.
            </div>

            <Field label="Token de confirmação" icon={<Lock size={15} />}>
              <input
                className={inputClass}
                onChange={(event) => setVerificationToken(event.target.value)}
                placeholder="Digite o token de confirmação"
                required
                type="text"
                value={verificationToken}
              />
            </Field>

            <Button
              className="w-full"
              icon={<Check size={16} />}
              loading={loading}
              type="submit"
              variant="primary"
            >
              Confirmar e acessar
            </Button>

            <Button
              className="w-full"
              onClick={() => {
                setShowVerification(false);
                setTab("login");
              }}
              type="button"
              variant="ghost"
            >
              Já tenho uma conta
            </Button>
          </form>
        ) : (
          <form className="space-y-4" onSubmit={handleRegister}>
            <Field label="Nome completo" icon={<User size={15} />}>
              <input
                autoComplete="name"
                className={inputClass}
                onChange={(event) => setName(event.target.value)}
                placeholder="Seu nome"
                required
                type="text"
                value={name}
              />
            </Field>

            <Field label="E-mail" icon={<Mail size={15} />}>
              <input
                autoComplete="email"
                className={inputClass}
                onChange={(event) => setRegisterEmail(event.target.value)}
                placeholder="seu@email.com"
                required
                type="email"
                value={registerEmail}
              />
            </Field>

            <Field label="Função" icon={<User size={15} />}>
              <select
                className={inputClass}
                onChange={(event) => setRegisterRole(event.target.value as DevRole)}
                required
                value={registerRole}
              >
                <option value="analyst">Analista</option>
                <option value="manager">Gerenciador</option>
                <option value="admin">Administrador</option>
              </select>
            </Field>

            <Field label="Senha" icon={<Lock size={15} />}>
              <div className="relative">
                <input
                  autoComplete="new-password"
                  className={`${inputClass} pr-10`}
                  onChange={(event) => setRegisterPassword(event.target.value)}
                  placeholder="Mínimo 8 caracteres"
                  required
                  type={showRegisterPassword ? "text" : "password"}
                  value={registerPassword}
                />
                <button
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--text3)] hover:text-[var(--text)]"
                  onClick={() => setShowRegisterPassword((current) => !current)}
                  tabIndex={-1}
                  type="button"
                >
                  {showRegisterPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </Field>

            <div className="space-y-1.5">
              {passwordRequirements.map(([key, label]) => {
                const met =
                  passwordValidation.requirements[
                    key as keyof typeof passwordValidation.requirements
                  ];
                return (
                  <div className="flex items-center gap-2 text-xs" key={key}>
                    <span
                      className={cn(
                        "flex h-4 w-4 items-center justify-center rounded-full border text-[10px] font-bold",
                        met
                          ? "border-emerald-500/40 bg-emerald-500/15 text-emerald-600 dark:text-emerald-300"
                          : "border-slate-300 bg-slate-100 text-slate-400 dark:border-slate-700 dark:bg-slate-900"
                      )}
                    >
                      {met ? <Check size={10} /> : "·"}
                    </span>
                    <span
                      className={cn(
                        met
                          ? "text-emerald-700 dark:text-emerald-300"
                          : "text-slate-600 dark:text-slate-400"
                      )}
                    >
                      {label}
                    </span>
                  </div>
                );
              })}
            </div>

            <Button
              className="w-full"
              icon={<ArrowRight size={16} />}
              loading={loading}
              type="submit"
              variant="primary"
            >
              Criar conta
            </Button>
          </form>
        )}

        <div className="mt-6 rounded-lg border border-amber-500/20 bg-amber-500/10 p-3 text-[11px] leading-5 text-amber-200">
          <strong className="text-amber-100">Ambiente local:</strong>{" "}
          o acesso é feito por e-mail e senha. A confirmação de cadastro é
          simulada localmente; em produção o link será enviado por e-mail. O
          token de sessão fica apenas no navegador.
        </div>
      </section>
    </main>
  );
}

function Field({
  children,
  icon,
  label
}: {
  children: React.ReactNode;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <label className="block space-y-1.5">
      <span className="flex items-center gap-1.5 text-xs font-medium text-[var(--text)]">
        {icon}
        {label}
      </span>
      {children}
    </label>
  );
}

const passwordRequirements = [
  ["hasMinLength", "Mínimo de 8 caracteres"],
  ["hasMaxLength", "Máximo de 16 caracteres"],
  ["hasLowercase", "Pelo menos 1 letra minúscula"],
  ["hasUppercase", "Pelo menos 1 letra maiúscula"],
  ["hasSpecial", "Pelo menos 1 caractere especial"]
] as const;

const inputClass =
  "w-full rounded-lg border border-[var(--border)] bg-[var(--surf2)] px-3 py-2.5 text-sm text-[var(--text)] placeholder:text-[var(--text3)] focus:outline-none focus:ring-2 focus:ring-brand-teal/30";

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center text-[var(--text2)]">
          Carregando...
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
