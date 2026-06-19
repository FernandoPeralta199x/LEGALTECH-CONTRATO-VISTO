"use client";

import {
  Bell,
  Building2,
  Check,
  CheckCircle2,
  Laptop,
  Lock,
  Mail,
  MessageCircle,
  Moon,
  Palette,
  Save,
  Shield,
  Sun,
  User,
  Users
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { AppLayout } from "@/components/AppLayout";
import { AuthGuard } from "@/components/AuthGuard";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Notification } from "@/components/Notification";
import { PageTitle } from "@/components/PageTitle";
import { cn } from "@/lib/cn";
import { useDevSession } from "@/src/lib/useDevSession";
import {
  applyThemePreference,
  getStoredNotificationPreferences,
  getStoredThemePreference,
  saveNotificationPreferences,
  saveThemePreference,
  type NotificationChannelPreference,
  type NotificationPreferenceKey,
  type NotificationPreferences,
  type ThemePreference
} from "@/src/lib/preferences";
import { validatePasswordChange } from "@/src/lib/validation";

const TABS = [
  { id: "org", label: "Organização", icon: Building2 },
  { id: "members", label: "Equipe", icon: Users },
  { id: "security", label: "Segurança", icon: Shield },
  { id: "notifications", label: "Notificações", icon: Bell },
  { id: "appearance", label: "Aparência", icon: Palette }
] as const;

const roleLabels: Record<string, string> = {
  admin: "Administrador",
  analyst: "Analista",
  client: "Cliente",
  owner: "Proprietário",
  support: "Suporte"
};

const notificationItems: Array<{
  desc: string;
  key: NotificationPreferenceKey;
  label: string;
}> = [
  {
    desc: "Quando um novo caso é registrado.",
    key: "new_case_created",
    label: "Novo caso"
  },
  {
    desc: "Quando a análise é concluída.",
    key: "analysis_completed",
    label: "Análise concluída"
  },
  {
    desc: "Quando um relatório entra em revisão.",
    key: "review_pending",
    label: "Revisão pendente"
  },
  {
    desc: "Quando um relatório é aprovado.",
    key: "report_approved",
    label: "Relatório aprovado"
  },
  {
    desc: "Quando um módulo precisa de atenção.",
    key: "agent_failed",
    label: "Falha em módulo"
  }
];

const requirementLabels = [
  ["hasMinLength", "Mínimo de 8 caracteres"],
  ["hasLowercase", "Pelo menos 1 letra minúscula"],
  ["hasUppercase", "Pelo menos 1 letra maiúscula"],
  ["hasSpecial", "Pelo menos 1 caractere especial"]
] as const;

export default function SettingsPage() {
  const session = useDevSession();
  const [activeTab, setActiveTab] = useState<(typeof TABS)[number]["id"]>("org");
  const [saved, setSaved] = useState(false);
  const [theme, setTheme] = useState<ThemePreference>(() => getStoredThemePreference());
  const [notificationPreferences, setNotificationPreferences] =
    useState<NotificationPreferences>(() => getStoredNotificationPreferences());
  const [passwordForm, setPasswordForm] = useState({
    confirmPassword: "",
    currentPassword: "",
    newPassword: ""
  });
  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");

  const passwordValidation = validatePasswordChange(passwordForm);

  useEffect(() => {
    applyThemePreference(theme);
  }, [theme]);

  const sessions = useMemo(() => {
    const currentName = session?.email
      ? formatUserNameFromEmail(session.email)
      : "Usuário local";
    const currentEmail = session?.email ?? "dev.local@example.test";
    const currentRole = session
      ? roleLabels[session.role] ?? session.role
      : "Perfil local";
    const currentTime = session?.issuedAt
      ? new Intl.DateTimeFormat("pt-BR", {
          dateStyle: "short",
          timeStyle: "short"
        }).format(new Date(session.issuedAt))
      : "Sessão atual";

    return [
      {
        current: true,
        device: "Windows — Navegador local",
        email: currentEmail,
        lastSeen: currentTime,
        location: "Local não informado",
        name: currentName,
        role: currentRole
      }
    ];
  }, [session]);

  function handleSave() {
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2000);
  }

  function handleThemeChange(nextTheme: ThemePreference) {
    setTheme(nextTheme);
    saveThemePreference(nextTheme);
    applyThemePreference(nextTheme);
  }

  function toggleNotificationChannel(
    key: NotificationPreferenceKey,
    channel: keyof NotificationChannelPreference
  ) {
    setNotificationPreferences((current) => {
      const next = {
        ...current,
        [key]: {
          ...current[key],
          [channel]: !current[key][channel]
        }
      };

      saveNotificationPreferences(next);
      return next;
    });
  }

  function handlePasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPasswordError("");
    setPasswordSuccess("");

    if (!passwordValidation.valid) {
      setPasswordError(
        passwordValidation.errors.newPassword ??
          passwordValidation.errors.confirmPassword ??
          passwordValidation.errors.currentPassword ??
          "Revise os requisitos da senha."
      );
      return;
    }

    setPasswordSuccess(
      "Senha validada localmente. A troca real depende de autenticação/Cognito em etapa futura."
    );
    setPasswordForm({
      confirmPassword: "",
      currentPassword: "",
      newPassword: ""
    });
  }

  return (
    <AuthGuard>
      <AppLayout>
        <PageTitle
          description="Ajuste configurações locais de organização, segurança, notificações e aparência. Configurações reais de tenant, equipe e billing dependem de backend integrado."
          eyebrow="Configurações"
          title="Configurações"
        />

        <div className="flex flex-col gap-6 lg:flex-row">
          <nav className="flex shrink-0 gap-1 overflow-x-auto lg:w-52 lg:flex-col">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;

              return (
                <button
                  className={cn(
                    "flex items-center gap-2.5 whitespace-nowrap rounded-lg px-3 py-2.5 text-xs font-medium transition",
                    active
                      ? "bg-emerald-50 text-brand-teal-dark dark:bg-emerald-950/40 dark:text-emerald-100"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-800 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-slate-100"
                  )}
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  type="button"
                >
                  <Icon className={active ? "text-brand-teal" : ""} size={14} />
                  {tab.label}
                </button>
              );
            })}
          </nav>

          <div className="min-w-0 flex-1">
            {activeTab === "org" && (
              <Card title="Dados da organização">
                <div className="max-w-lg space-y-4">
                  <Field label="Nome da organização">
                    <input
                      className={inputClass}
                      defaultValue="Organização MVP"
                      type="text"
                    />
                  </Field>
                  <Field label="CNPJ">
                    <input
                      className={`${inputClass} cursor-not-allowed opacity-60`}
                      disabled
                      value="00.000.000/0000-00"
                    />
                  </Field>
                  <Field label="Plano">
                    <div className="flex items-center gap-3">
                      <input
                        className={`${inputClass} flex-1 cursor-not-allowed opacity-60`}
                        disabled
                        value="MVP Local"
                      />
                      <Button type="button" variant="secondary">
                        Upgrade em roadmap
                      </Button>
                    </div>
                  </Field>
                  <Button
                    icon={<Save size={14} />}
                    onClick={handleSave}
                    type="button"
                    variant={saved ? "secondary" : "primary"}
                  >
                    {saved ? "Registrado localmente" : "Registrar configuração local"}
                  </Button>
                </div>
              </Card>
            )}

            {activeTab === "members" && (
              <Card
                description="Gerenciamento real de equipe, convites e permissões ficam no roadmap."
                title="Equipe"
              >
                <div className="rounded-lg border border-[var(--border)] bg-[var(--surf2)] p-6 text-center">
                  <p className="text-sm text-[var(--text2)]">
                    Nenhum membro administrável nesta tela.
                  </p>
                </div>
                <div className="mt-4 border-t border-slate-200 pt-4 dark:border-slate-800">
                  <Button icon={<User size={13} />} type="button" variant="secondary">
                    Convite em roadmap
                  </Button>
                </div>
              </Card>
            )}

            {activeTab === "security" && (
              <div className="space-y-4">
                <Card
                  description="Validação local para desenvolvimento. Não aciona Cognito nem endpoint real."
                  title="Segurança da conta"
                >
                  {passwordError && (
                    <Notification tone="error" title="Senha local não validada">
                      {passwordError}
                    </Notification>
                  )}
                  {passwordSuccess && (
                    <Notification tone="success" title="Validação local concluída">
                      {passwordSuccess}
                    </Notification>
                  )}

                  <form className="max-w-lg space-y-4" onSubmit={handlePasswordSubmit}>
                    <Field label="Senha atual">
                      <input
                        className={inputClass}
                        onChange={(event) =>
                          setPasswordForm((current) => ({
                            ...current,
                            currentPassword: event.target.value
                          }))
                        }
                        placeholder="Obrigatória nesta simulação local"
                        type="password"
                        value={passwordForm.currentPassword}
                      />
                    </Field>
                    <Field label="Nova senha">
                      <input
                        className={inputClass}
                        onChange={(event) =>
                          setPasswordForm((current) => ({
                            ...current,
                            newPassword: event.target.value
                          }))
                        }
                        placeholder="Mínimo 8, maiúscula, minúscula e especial"
                        type="password"
                        value={passwordForm.newPassword}
                      />
                    </Field>
                    <Field label="Confirmar nova senha">
                      <input
                        className={inputClass}
                        onChange={(event) =>
                          setPasswordForm((current) => ({
                            ...current,
                            confirmPassword: event.target.value
                          }))
                        }
                        placeholder="Repita a nova senha"
                        type="password"
                        value={passwordForm.confirmPassword}
                      />
                    </Field>

                    <div className="space-y-1.5">
                      {requirementLabels.map(([key, label]) => {
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

                    <Button type="submit" variant="primary">
                      Validar alteração local
                    </Button>
                  </form>
                </Card>

                <Card
                  description="Sessões ativas reconhecidas localmente."
                  title="Sessões ativas"
                >
                  <div className="divide-y divide-slate-200 dark:divide-slate-800">
                    {sessions.map((s) => (
                      <div className="flex items-center gap-4 py-4" key={s.email}>
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-brand text-xs font-bold text-white">
                          {s.name.slice(0, 2).toUpperCase()}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                            {s.name}
                          </p>
                          <p className="truncate text-[11px] text-slate-600 dark:text-slate-400">
                            {s.email}
                          </p>
                        </div>
                        <div className="flex flex-col items-end gap-1">
                          <span className="inline-flex items-center rounded border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-600 dark:text-emerald-300">
                            {s.role}
                          </span>
                          <span className="text-[10px] text-slate-500">
                            {s.current ? "Atual" : s.lastSeen}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            )}

            {activeTab === "notifications" && (
              <Card
                description="Preferências armazenadas localmente. Notificações reais por e-mail/WhatsApp dependem de serviços externos."
                title="Canais de notificação"
              >
                <div className="space-y-4">
                  {notificationItems.map((item) => (
                    <div
                      className="flex items-start justify-between gap-4 rounded-lg border border-[var(--border)] bg-[var(--surf2)] p-4"
                      key={item.key}
                    >
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-[var(--text)]">
                          {item.label}
                        </p>
                        <p className="mt-0.5 text-xs text-[var(--text2)]">{item.desc}</p>
                      </div>
                      <div className="flex shrink-0 gap-2">
                        <ChannelButton
                          active={notificationPreferences[item.key]?.email ?? false}
                          icon={<Mail size={14} />}
                          label="E-mail"
                          onClick={() => toggleNotificationChannel(item.key, "email")}
                        />
                        <ChannelButton
                          active={notificationPreferences[item.key]?.whatsapp ?? false}
                          icon={<MessageCircle size={14} />}
                          label="WhatsApp"
                          onClick={() => toggleNotificationChannel(item.key, "whatsapp")}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {activeTab === "appearance" && (
              <Card title="Aparência">
                <p className="mb-4 text-sm text-[var(--text2)]">
                  Escolha como a interface é exibida neste dispositivo.
                </p>
                <div className="grid gap-3 sm:grid-cols-3">
                  {[
                    {
                      id: "light" as ThemePreference,
                      icon: Sun,
                      label: "Claro"
                    },
                    {
                      id: "dark" as ThemePreference,
                      icon: Moon,
                      label: "Escuro"
                    },
                    {
                      id: "system" as ThemePreference,
                      icon: Laptop,
                      label: "Sistema"
                    }
                  ].map((option) => {
                    const Icon = option.icon;
                    const active = theme === option.id;

                    return (
                      <button
                        className={cn(
                          "flex flex-col items-center gap-2 rounded-lg border p-4 transition",
                          active
                            ? "border-brand-teal bg-brand-teal/10 text-brand-teal-dark"
                            : "border-[var(--border)] bg-[var(--surf2)] text-[var(--text2)] hover:border-brand-teal/40"
                        )}
                        key={option.id}
                        onClick={() => handleThemeChange(option.id)}
                        type="button"
                      >
                        <Icon size={20} />
                        <span className="text-xs font-medium">{option.label}</span>
                        {active && (
                          <CheckCircle2 className="text-brand-teal" size={16} />
                        )}
                      </button>
                    );
                  })}
                </div>
              </Card>
            )}
          </div>
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

function Field({
  children,
  label
}: {
  children: React.ReactNode;
  label: string;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium text-[var(--text)]">{label}</span>
      {children}
    </label>
  );
}

function ChannelButton({
  active,
  icon,
  label,
  onClick
}: {
  active: boolean;
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      className={cn(
        "flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-medium transition",
        active
          ? "border-brand-teal bg-brand-teal/10 text-brand-teal-dark"
          : "border-[var(--border)] bg-[var(--surf)] text-[var(--text2)] hover:border-brand-teal/40"
      )}
      onClick={onClick}
      type="button"
    >
      {icon}
      {label}
    </button>
  );
}

function formatUserNameFromEmail(email: string): string {
  const [localPart] = email.split("@");
  return localPart
    .split(".")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

const inputClass =
  "w-full rounded-lg border border-[var(--border)] bg-[var(--surf2)] px-3 py-2 text-sm text-[var(--text)] placeholder:text-[var(--text3)] focus:outline-none focus:ring-2 focus:ring-brand-teal/30";
