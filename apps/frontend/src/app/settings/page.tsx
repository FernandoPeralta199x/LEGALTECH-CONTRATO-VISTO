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
import { mockOrganizations, mockUsers } from "@/lib/mockData";
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
  { id: "org", label: "Configuração local", icon: Building2 },
  { id: "members", label: "Equipe demo", icon: Users },
  { id: "security", label: "Segurança local", icon: Shield },
  { id: "notifications", label: "Preferências locais", icon: Bell },
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
    desc: "Quando um registro local de caso é indicado no MVP.",
    key: "new_case_created",
    label: "Registro local de caso"
  },
  {
    desc: "Quando a análise demonstrativa local é marcada no roteiro.",
    key: "analysis_completed",
    label: "Análise demonstrativa"
  },
  {
    desc: "Quando um resumo demonstrativo fica em revisão local planejada.",
    key: "review_pending",
    label: "Revisão local planejada"
  },
  {
    desc: "Quando um relatório demonstrativo recebe validação local.",
    key: "report_approved",
    label: "Validação local de relatório"
  },
  {
    desc: "Quando um módulo planejado exige atenção operacional local.",
    key: "agent_failed",
    label: "Atenção em módulo local"
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

  const org = mockOrganizations[0];
  const passwordValidation = validatePasswordChange(passwordForm);

  useEffect(() => {
    applyThemePreference(theme);
  }, [theme]);

  const sessions = useMemo(() => {
    const currentName = session?.email
      ? formatUserNameFromEmail(session.email)
      : "Usuário local";
    const currentEmail = session?.email ?? "dev.local@example.test";
    const currentRole = session ? roleLabels[session.role] ?? session.role : "Perfil local";
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
      },
      {
        current: false,
        device: "Ambiente de homologação — navegador fictício",
        email: "analista.local@example.test",
        lastSeen: "Acesso demonstrativo",
        location: "Local não informado",
        name: "Usuário local",
        role: "Analista"
      }
    ];
  }, [session]);

  function handleSave() {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
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
          description="Ajuste configurações locais e demonstrativas de organização, segurança, canais planejados e aparência."
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
              <Card title="Dados locais da organização">
                <div className="max-w-lg space-y-4">
                  <Field label="Nome local da organização">
                    <input className={inputClass} defaultValue={org.name} type="text" />
                  </Field>
                  <Field label="CNPJ">
                    <input
                      className={`${inputClass} cursor-not-allowed opacity-60`}
                      disabled
                      value={org.cnpj}
                    />
                  </Field>
                  <Field label="Plano">
                    <div className="flex items-center gap-3">
                      <input
                        className={`${inputClass} flex-1 cursor-not-allowed opacity-60`}
                        disabled
                        value={org.plan.charAt(0).toUpperCase() + org.plan.slice(1)}
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
                description="Visualize referências de equipe do MVP local. Convites reais e permissões ficam no roadmap."
                title="Equipe demonstrativa"
              >
                <div className="divide-y divide-slate-200 dark:divide-slate-800">
                  {mockUsers.map((user) => (
                    <div className="flex items-center gap-4 py-4" key={user.id}>
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-brand text-xs font-bold text-white">
                        {user.avatarInitials}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                          {user.name}
                        </p>
                        <p className="truncate text-[11px] text-slate-600 dark:text-slate-400">
                          {user.email}
                        </p>
                      </div>
                      <select className={selectClass}>
                        <option value="admin">Admin</option>
                        <option value="analyst">Analista</option>
                        <option value="client">Cliente</option>
                        <option value="viewer">Viewer</option>
                      </select>
                    </div>
                  ))}
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
                  title="Segurança local da conta"
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

                    <div className="grid gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950">
                      {requirementLabels.map(([key, label]) => {
                        const met = passwordValidation.requirements[key];
                        return (
                          <div
                            className={cn(
                              "flex items-center gap-2 text-[11px]",
                              met
                                ? "text-emerald-700 dark:text-emerald-300"
                                : "text-slate-500 dark:text-slate-400"
                            )}
                            key={key}
                          >
                            <span
                              className={cn(
                                "flex h-4 w-4 items-center justify-center rounded-full border",
                                met
                                  ? "border-emerald-300 bg-emerald-50 dark:border-emerald-700 dark:bg-emerald-950"
                                  : "border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-900"
                              )}
                            >
                              {met && <Check size={10} />}
                            </span>
                            {label}
                          </div>
                        );
                      })}
                    </div>

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
                    <Button icon={<Lock size={14} />} type="submit">
                      Validar senha local
                    </Button>
                  </form>
                </Card>

                <Card
                  description="Dispositivos demonstrativos com acesso à sessão local. Tokens não são exibidos."
                  title="Sessões demonstrativas"
                >
                  <div className="divide-y divide-slate-200 dark:divide-slate-800">
                    {sessions.map((activeSession) => (
                      <div
                        className="flex flex-col gap-3 py-4 first:pt-0 sm:flex-row sm:items-center sm:justify-between"
                        key={`${activeSession.email}-${activeSession.device}`}
                      >
                        <div className="flex gap-3">
                          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300">
                            <Laptop size={18} />
                          </span>
                          <div>
                            <p className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                              {activeSession.name}
                            </p>
                            <p className="text-[11px] text-slate-500 dark:text-slate-400">
                              {activeSession.email} · {activeSession.role}
                            </p>
                            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                              {activeSession.device} · {activeSession.location}
                            </p>
                          </div>
                        </div>
                        {activeSession.current ? (
                          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[10px] font-semibold text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-300">
                            <CheckCircle2 size={12} />
                            Sessão local atual · {activeSession.lastSeen}
                          </span>
                        ) : (
                          <button className="text-left text-[10px] font-semibold text-red-700 transition hover:text-red-800 dark:text-red-300 dark:hover:text-red-200">
                            Encerramento em roadmap
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            )}

            {activeTab === "notifications" && (
              <Card
                description="Preferências demonstrativas salvas localmente até existir endpoint real de envio."
                title="Preferências locais de notificação"
              >
                <Notification tone="info" title="Canais ainda demonstrativos">
                  E-mail planejado e WhatsApp planejado ficam configurados apenas
                  no navegador. Nenhum SMTP, WhatsApp ou API externa é chamado
                  nesta etapa.
                </Notification>

                <div className="space-y-3">
                  {notificationItems.map((item) => (
                    <div
                      className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950"
                      key={item.key}
                    >
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                          <p className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                            {item.label}
                          </p>
                          <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                            {item.desc}
                          </p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <ChannelToggle
                            active={notificationPreferences[item.key].email}
                            icon={<Mail size={13} />}
                            label="E-mail planejado"
                            onClick={() => toggleNotificationChannel(item.key, "email")}
                          />
                          <ChannelToggle
                            active={notificationPreferences[item.key].whatsapp}
                            icon={<MessageCircle size={13} />}
                            label="WhatsApp planejado"
                            onClick={() => toggleNotificationChannel(item.key, "whatsapp")}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {activeTab === "appearance" && (
              <Card
                description="A escolha é aplicada imediatamente e fica salva neste navegador."
                title="Aparência"
              >
                <div className="grid gap-3 sm:grid-cols-2">
                  {[
                    {
                      desc: "Interface clara refinada para leitura em ambientes iluminados.",
                      icon: Sun,
                      id: "light" as const,
                      label: "Claro"
                    },
                    {
                      desc: "Tema premium principal, com camadas escuras e acento teal.",
                      icon: Moon,
                      id: "dark" as const,
                      label: "Escuro"
                    }
                  ].map((option) => {
                    const Icon = option.icon;
                    const active = theme === option.id;

                    return (
                      <button
                        className={cn(
                          "flex items-start gap-3 rounded-lg border p-4 text-left transition",
                          active
                            ? "border-brand-teal/50 bg-brand-teal/10 shadow-glow-teal dark:bg-emerald-950/40"
                            : "border-slate-200 bg-white hover:border-emerald-200 hover:bg-emerald-50 dark:border-slate-800 dark:bg-slate-950 dark:hover:border-emerald-800 dark:hover:bg-emerald-950/20"
                        )}
                        key={option.id}
                        onClick={() => handleThemeChange(option.id)}
                        type="button"
                      >
                        <span
                          className={cn(
                            "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border",
                            active
                              ? "border-brand-teal/40 bg-white text-brand-teal dark:bg-slate-900"
                              : "border-slate-200 bg-slate-50 text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400"
                          )}
                        >
                          <Icon size={18} />
                        </span>
                        <span>
                          <span className="block text-xs font-semibold text-slate-900 dark:text-slate-100">
                            {option.label}
                          </span>
                          <span className="mt-1 block text-[11px] leading-5 text-slate-500 dark:text-slate-400">
                            {option.desc}
                          </span>
                          {active && (
                            <span className="mt-2 inline-flex items-center gap-1.5 text-[10px] font-semibold text-brand-teal">
                              <CheckCircle2 size={12} />
                              Tema ativo
                            </span>
                          )}
                        </span>
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

function ChannelToggle({
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
        "inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-[11px] font-semibold transition",
        active
          ? "border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300"
          : "border-slate-200 bg-white text-slate-500 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400 dark:hover:bg-slate-800"
      )}
      onClick={onClick}
      type="button"
    >
      {icon}
      {label}
      <span
        className={cn(
          "ml-1 h-2 w-2 rounded-full",
          active ? "bg-emerald-500" : "bg-slate-300 dark:bg-slate-600"
        )}
      />
    </button>
  );
}

const inputClass =
  "cv-input w-full px-3 text-sm";

const selectClass =
  "cv-input min-h-11 rounded-lg px-2 text-[11px]";

function Field({ label, children }: { children: React.ReactNode; label: string }) {
  return (
    <div>
      <label className="mb-1.5 block text-xs font-semibold text-[var(--text2)]">
        {label}
      </label>
      {children}
    </div>
  );
}

function formatUserNameFromEmail(email: string): string {
  const localPart = email.split("@")[0] ?? "";
  const normalized = localPart
    .replace(/[._-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .trim();

  return normalized || "Usuário local";
}
