"use client";

import {
  ArrowRight,
  Eye,
  EyeOff,
  Headphones,
  KeyRound,
  Lock,
  LogOut,
  Mail,
  Scale,
  Shield,
  ShieldCheck,
  Sparkles,
  User,
  Users
} from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";

import { Button } from "@/components/Button";
import { ThemeToggle } from "@/components/ThemeToggle";
import { cn } from "@/lib/cn";
import { logoutDevSession, saveDevSession } from "@/src/services/auth";
import { useDevSession } from "@/src/lib/useDevSession";
import { validateDevJwtForm } from "@/src/lib/validation";
import { DEV_ROLES, type DevRole } from "@/src/types/auth";

type RoleConfig = {
  desc: string;
  icon: typeof Shield;
  label: string;
};

const roleConfig: Record<DevRole, RoleConfig> = {
  admin: {
    desc: "Gestão completa da plataforma",
    icon: ShieldCheck,
    label: "Administrador"
  },
  analyst: {
    desc: "Revisão e aprovação de relatórios",
    icon: Users,
    label: "Analista"
  },
  client: {
    desc: "Criação e acompanhamento de casos",
    icon: User,
    label: "Cliente"
  },
  owner: {
    desc: "Acesso total ao sistema",
    icon: Shield,
    label: "Proprietário"
  },
  support: {
    desc: "Monitoramento e atendimento",
    icon: Headphones,
    label: "Suporte"
  }
};

const demoRoles: DevRole[] = [...DEV_ROLES];

type ToastState = {
  message: string;
  tone: "error" | "success" | "warning";
} | null;

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = searchParams.get("next") || "/dashboard";
  const session = useDevSession();
  const [role, setRole] = useState<DevRole>(session?.role ?? "owner");
  const [email, setEmail] = useState(session?.email ?? "");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState("");
  const [toast, setToast] = useState<ToastState>(null);

  const selectedRole = roleConfig[role];

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading) {
      return;
    }

    const validation = validateDevJwtForm(token);
    if (!validation.valid) {
      setToast({
        message:
          validation.errors.token ??
          "Cole um JWT dev válido gerado pelo backend para acessar.",
        tone: "error"
      });
      return;
    }

    setLoading(true);
    try {
      await saveDevSession({ role, token: token.trim() });
      setToast({
        message: "JWT dev aceito. Redirecionando para a plataforma...",
        tone: "success"
      });
      await new Promise((resolve) => setTimeout(resolve, 450));
      router.replace(nextPath.startsWith("/") ? nextPath : "/dashboard");
    } catch {
      setToast({
        message:
          "JWT dev recusado pela API local. Gere um novo token no backend e tente novamente.",
        tone: "error"
      });
      setLoading(false);
    }
  }

  function handleLogout() {
    logoutDevSession();
    setToken("");
    setPassword("");
    setToast({
      message: "Sessão local encerrada.",
      tone: "success"
    });
  }

  return (
    <main className="cv-login-shell relative flex items-start justify-center overflow-hidden">
      <div className="pointer-events-none absolute inset-0 opacity-45 noise" />
      <Link
        className="absolute left-5 top-5 z-10 flex items-center gap-2 text-xs font-semibold text-[var(--text2)] transition hover:text-[var(--teal)]"
        href="/"
      >
        <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--bd)] bg-[var(--surf2)]">
          <Scale size={16} />
        </span>
        Contrato Visto
      </Link>
      <ThemeToggle className="absolute right-5 top-5 z-10" />

      <section
        aria-label="Login de desenvolvimento"
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
            Perfil de acesso dev
          </p>
          <span className="cv-badge cv-badge-teal">
            <Sparkles size={12} />
            Ambiente local
          </span>
        </div>

        <div className="mb-5 space-y-1.5" role="radiogroup" aria-label="Selecionar perfil visual">
          {demoRoles.map((candidateRole) => {
            const cfg = roleConfig[candidateRole];
            const Icon = cfg.icon;
            const active = role === candidateRole;

            return (
              <button
                aria-checked={active}
                className={cn(
                  "flex min-h-12 w-full items-center gap-3 rounded-md border px-3 py-2.5 text-left transition active:scale-[0.983]",
                  active
                    ? "border-[rgba(32,201,151,0.36)] bg-[var(--teal-dim)]"
                    : "border-[var(--bd)] bg-[var(--surf2)] hover:border-[var(--bd2)] hover:bg-[var(--surf3)]"
                )}
                key={candidateRole}
                onClick={() => {
                  setRole(candidateRole);
                  setToast(null);
                }}
                role="radio"
                type="button"
              >
                <span
                  className={cn(
                    "flex h-9 w-9 shrink-0 items-center justify-center rounded-md border transition",
                    active
                      ? "border-emerald-300/40 bg-emerald-500/20 text-emerald-200"
                      : "border-[var(--bd)] bg-[var(--surf3)] text-[var(--text3)]"
                  )}
                >
                  <Icon size={16} />
                </span>
                <span className="min-w-0 flex-1">
                  <span
                    className={cn(
                      "block truncate text-[13.5px] font-semibold",
                      active ? "text-[var(--teal)]" : "text-[var(--text)]"
                    )}
                  >
                    {cfg.label}
                  </span>
                  <span className="block truncate text-[11px] text-[var(--text2)]">
                    {cfg.desc}
                  </span>
                </span>
                <span
                  className={cn(
                    "h-2 w-2 shrink-0 rounded-full bg-[var(--teal)] transition",
                    active ? "scale-100 opacity-100" : "scale-0 opacity-0"
                  )}
                />
              </button>
            );
          })}
        </div>

        <div className="my-5 border-t border-[var(--bd)]" />

        {session && (
          <div className="mb-5 rounded-md border border-[rgba(32,201,151,0.24)] bg-[var(--teal-dim)] px-3 py-3">
            <div className="flex items-start gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-[rgba(32,201,151,0.24)] bg-[var(--surf2)] text-[var(--teal)]">
                <KeyRound size={17} />
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-[var(--text)]">Sessão dev ativa</p>
                <p className="mt-1 break-words text-[11px] leading-5 text-[var(--text2)]">
                  {session.email} · {roleConfig[session.role].label} ·{" "}
                  JWT dev salvo localmente
                </p>
              </div>
              <Button icon={<LogOut size={14} />} onClick={handleLogout} size="sm" variant="secondary">
                Sair
              </Button>
            </div>
          </div>
        )}

        <div className="mb-5 rounded-md border border-[rgba(249,115,22,0.24)] bg-[var(--orange-dim)] px-3 py-3">
          <p className="text-xs font-semibold text-[var(--orange)]">
            Acesso local por JWT dev
          </p>
          <p className="mt-1 text-[11px] leading-5 text-[var(--text2)]">
            E-mail e senha ainda não autenticam neste MVP local. Gere um JWT dev no
            backend e cole no campo principal para acessar dashboard, casos e
            configurações.
          </p>
        </div>

        <form className="space-y-4" noValidate onSubmit={handleSubmit}>
          <div>
            <label className="mb-2 block text-[10px] font-bold uppercase text-[var(--teal)]">
              JWT dev do backend
            </label>
            <textarea
              autoCapitalize="off"
              autoComplete="off"
              autoCorrect="off"
              className="cv-input min-h-28 w-full resize-y px-3 py-3 text-sm leading-6"
              onChange={(event) => {
                setToken(event.target.value);
                if (toast?.tone === "error") {
                  setToast(null);
                }
              }}
              placeholder={"Cole o JWT dev gerado pelo backend.\nObrigatório para entrar no ambiente local."}
              spellCheck={false}
              value={token}
            />
            <p className="mt-1.5 text-[11px] leading-5 text-[var(--text2)]">
              O token fica salvo apenas no navegador local e será enviado como
              Authorization: Bearer nas chamadas para a API.
            </p>
          </div>

          <LoginField
            hint="Auxiliar visual/dev. Este campo não autentica no backend local."
            icon={<Mail size={17} />}
            label="E-mail visual/dev"
          >
            <input
              autoComplete="email"
              className={loginInputClass}
              inputMode="email"
              onChange={(event) => {
                setEmail(event.target.value);
                if (toast?.tone === "error") {
                  setToast(null);
                }
              }}
              placeholder="seu@email.com"
              spellCheck={false}
              type="text"
              value={email}
            />
          </LoginField>

          <LoginField
            hint="Campo visual/dev. Não use senha real; Cognito ainda não está ativo."
            icon={<Lock size={17} />}
            label="Senha visual/dev"
          >
            <input
              autoComplete="off"
              className={cn(loginInputClass, "pr-12")}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="••••••••"
              type={showPassword ? "text" : "password"}
              value={password}
            />
            <button
              aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
              className="absolute right-2.5 flex h-9 min-h-9 w-9 min-w-9 items-center justify-center rounded-md text-[var(--text3)] transition hover:bg-[var(--surf3)] hover:text-[var(--text)]"
              onClick={() => setShowPassword((current) => !current)}
              type="button"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </LoginField>

          <button
            className="cv-btn cv-btn-primary group relative mt-2 flex min-h-[52px] w-full items-center justify-center gap-2 px-4 text-xs font-bold uppercase disabled:cursor-not-allowed disabled:opacity-60"
            disabled={loading}
            type="submit"
          >
            <span className="absolute inset-0 bg-gradient-to-b from-white/10 to-transparent" />
            <span className="relative">
              {loading ? "Validando JWT..." : `Entrar com JWT dev · ${selectedRole.label}`}
            </span>
            <ArrowRight className="relative transition group-hover:translate-x-1" size={18} />
          </button>
        </form>

        {toast && (
          <div
            className={cn(
              "mt-4 rounded-md border px-4 py-3 text-center text-xs leading-5",
              toast.tone === "success" &&
                "border-emerald-300/30 bg-emerald-400/15 text-emerald-200",
              toast.tone === "warning" &&
                "border-amber-300/30 bg-amber-400/15 text-amber-100",
              toast.tone === "error" && "border-red-300/30 bg-red-400/15 text-red-200"
            )}
            aria-live="polite"
            role="alert"
          >
            {toast.message}
          </div>
        )}

        <div className="mt-5 space-y-2 rounded-md border border-[var(--bd)] bg-[var(--surf2)] px-3 py-3">
          <p className="text-[11px] leading-5 text-[var(--text2)]">
            Ambiente local de desenvolvimento. Cognito real ainda não está ativo.
          </p>
          <p className="text-[11px] leading-5 text-[var(--text2)]">
            O perfil selecionado é apenas visual/dev; a autorização real continua vindo
            do JWT/backend e do RBAC da API.
          </p>
        </div>

        <div className="mt-3 rounded-md border border-[var(--bd)] bg-[var(--surf2)] px-3 py-3">
          <p className="text-[11px] font-semibold text-[var(--text2)]">
            Gerar JWT dev no backend
          </p>
          <pre className="mt-2 max-h-32 overflow-auto whitespace-pre-wrap rounded-md border border-[var(--bd)] bg-[var(--surf3)] p-2 text-[10px] leading-5 text-[var(--text2)]">
{`cd legaltech-aws\\apps\\api
.\\.venv\\Scripts\\python.exe -m src.modules.admin.dev_jwt --organization-id 11111111-1111-4111-8111-111111111111 --user-id 22222222-2222-4222-8222-222222222222 --email dev.local@example.test --role admin`}
          </pre>
        </div>
      </section>
    </main>
  );
}

function LoginField({
  children,
  hint,
  icon,
  label
}: {
  children: React.ReactNode;
  hint?: string;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-[10px] font-bold uppercase text-[var(--text3)]">
        {label}
      </span>
      <span className="relative flex items-center">
        <span className="pointer-events-none absolute left-3 z-10 text-[var(--text3)]">
          {icon}
        </span>
        {children}
      </span>
      {hint && <span className="mt-1.5 block text-[11px] leading-5 text-[var(--text2)]">{hint}</span>}
    </label>
  );
}

const loginInputClass =
  "cv-input h-12 w-full pl-10 pr-3 text-base";

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center bg-[#02272b]">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-emerald-200/40 border-t-emerald-200" />
        </main>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
