import {
  Activity,
  Building2,
  Lock,
  Settings,
  Shield,
  TrendingUp,
  User,
  Users
} from "lucide-react";
import Link from "next/link";

import { AppLayout } from "@/components/AppLayout";
import { AuthGuard } from "@/components/AuthGuard";
import { Card } from "@/components/Card";
import { PageTitle } from "@/components/PageTitle";
import { StatusBadge } from "@/components/StatusBadge";
import { formatDate, formatDateTime } from "@/lib/formatters";
import {
  mockAuditLogs,
  mockCases,
  mockOrganizations,
  mockUsers
} from "@/lib/mockData";

const roleColors: Record<string, string> = {
  admin: "bg-brand-teal/10 text-brand-teal-dark border-brand-teal/20",
  analyst: "bg-brand-teal/10 text-brand-teal-light border-brand-teal/20",
  client: "bg-slate-100 text-slate-700 border-slate-200",
  viewer: "bg-slate-600/10 text-slate-600 border-slate-600/20",
  owner: "bg-purple-500/10 text-purple-300 border-purple-500/20",
  support: "bg-amber-50 text-amber-700 border-amber-500/20"
};

const roleLabels: Record<string, string> = {
  admin: "Admin",
  analyst: "Analista",
  client: "Cliente",
  viewer: "Viewer",
  owner: "Owner",
  support: "Suporte"
};

const auditActionLabel: Record<string, string> = {
  case_created: "Caso registrado no mock",
  case_submitted: "Caso marcado no mock",
  document_uploaded: "Documento anexado no mock",
  document_processed: "Documento marcado no mock",
  agent_started: "Agente demonstrativo iniciado",
  agent_completed: "Agente demonstrativo concluído",
  report_generated: "Relatório demonstrativo registrado",
  review_approved: "Registro positivo no mock",
  review_rejected: "Registro negativo no mock",
  review_adjustment: "Ajuste mockado solicitado",
  status_changed: "Status mockado alterado",
  user_login: "Login demonstrativo",
  user_logout: "Logout demonstrativo"
};

export default function AdminPage() {
  const statusCounts = [
    {
      label: "Análise local/mock",
      count: mockCases.filter((c) =>
        ["processing", "analise_contratual", "compliance", "minuta_relatorio"].includes(c.status)
      ).length,
      color: "text-violet-700"
    },
    {
      label: "Revisão local",
      count: mockCases.filter((c) => c.status === "revisao_humana").length,
      color: "text-amber-700"
    },
    {
      label: "Entrega demonstrativa",
      count: mockCases.filter((c) => c.status === "delivered").length,
      color: "text-teal-400"
    },
    {
      label: "Rascunho local",
      count: mockCases.filter((c) => c.status === "draft").length,
      color: "text-slate-600"
    }
  ];

  return (
    <AuthGuard>
      <AppLayout>
        <PageTitle
          actions={
            <>
              <Link
                className="inline-flex items-center gap-2 rounded-lg bg-brand-teal px-4 py-2.5 text-sm font-semibold text-white shadow-glow-teal transition hover:bg-brand-teal-dark"
                href="/cases/new"
              >
                <Activity size={15} />
                Novo Pedido
              </Link>
              <Link
                className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surf)] px-3.5 py-2.5 text-sm font-medium text-[var(--text)] transition hover:border-brand-teal/40"
                href="/settings"
              >
                <Settings size={15} />
                Configurações locais
              </Link>
            </>
          }
          description="Visão de governança local para acompanhar organização, equipe, papéis e registros operacionais mockados do MVP. Os dados abaixo são demonstrativos e não representam administração, auth/RBAC, sessões, notificações ou auditoria reais."
          eyebrow="Administração"
          title="Governança operacional do MVP local"
        />

        <div className="mb-6 grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-lg border border-amber-500/25 bg-amber-500/10 p-5">
            <div className="flex items-start gap-3">
              <Lock className="mt-0.5 shrink-0 text-amber-400" size={18} />
              <div>
                <p className="text-sm font-semibold text-[var(--text)]">
                  Governança local, sem operação administrativa real
                </p>
                <p className="mt-2 text-xs leading-5 text-[var(--text2)]">
                  Esta tela organiza uma leitura do MVP local. Convites por
                  e-mail, criação real de usuário, alteração real de perfil/role,
                  RBAC real, sessões reais, localização, notificações, webhooks,
                  billing e auditoria real dependem de backend/auth/serviços
                  futuros.
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-[var(--border)] bg-[var(--surf)] p-5">
            <p className="text-sm font-semibold text-[var(--text)]">
              Conexões da operação
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {[
                { href: "/cases", label: "Casos" },
                { href: "/documents", label: "Documentos" },
                { href: "/analyst", label: "Analista" },
                { href: "/reports", label: "Relatórios" },
                { href: "/clients", label: "Clientes" }
              ].map((item) => (
                <Link
                  className="rounded-lg border border-[var(--border)] px-3 py-2 text-xs font-medium text-[var(--text)] transition hover:border-brand-teal/40"
                  href={item.href}
                  key={item.href}
                >
                  {item.label}
                </Link>
              ))}
            </div>
            <p className="mt-3 text-xs leading-5 text-[var(--text2)]">
              Use estes atalhos para revisar a operação; eles não criam vínculo
              administrativo novo nem acionam serviços externos.
            </p>
          </div>
        </div>

        {/* System overview */}
        <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[
            {
              label: "Membros ativos no mock",
              value: mockUsers.filter((u) => u.status === "active").length,
              hint: "Equipe demonstrativa; não cria usuário real.",
              icon: Users,
              color: "text-brand-teal-dark",
              bg: "bg-brand-teal/10 border-brand-teal/20"
            },
            {
              label: "Organizações demonstrativas",
              value: mockOrganizations.length,
              hint: "Tenants demonstrativos, sem tenant admin real.",
              icon: Building2,
              color: "text-brand-teal-light",
              bg: "bg-brand-teal/10 border-brand-teal/20"
            },
            {
              label: "Casos na base local",
              value: mockCases.length,
              hint: "Contagem derivada dos mocks existentes.",
              icon: Activity,
              color: "text-violet-700",
              bg: "bg-violet-500/10 border-violet-500/20"
            },
            {
              label: "Registros mockados de auditoria",
              value: mockAuditLogs.length,
              hint: "Referência visual; não é trilha auditável real.",
              icon: Shield,
              color: "text-amber-400",
              bg: "bg-amber-50 border-amber-500/20"
            }
          ].map((m) => {
            const Icon = m.icon;
            return (
              <Card key={m.label}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs text-[var(--text2)]">{m.label}</p>
                    <p className={`mt-2 text-3xl font-bold ${m.color}`}>
                      {m.value}
                    </p>
                    <p className="mt-2 text-xs leading-5 text-[var(--text2)]">
                      {m.hint}
                    </p>
                  </div>
                  <div
                    className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border ${m.bg}`}
                  >
                    <Icon className={m.color} size={18} />
                  </div>
                </div>
              </Card>
            );
          })}
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          {/* Users */}
          <Card
            title="Equipe local do MVP"
            description="Contas demonstrativas por papel. Não cria usuário real, convite, senha, verificação ou alteração real de perfil."
          >
            <div className="divide-y divide-white/[0.06]">
              {mockUsers.map((user) => (
                <div className="flex items-center gap-4 py-3" key={user.id}>
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-brand text-xs font-bold text-white">
                    {user.avatarInitials}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold text-[var(--text)]">
                      {user.name}
                    </p>
                    <p className="truncate text-[11px] text-[var(--text2)]">
                      {user.email}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span
                      className={`inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-semibold ${
                        roleColors[user.role] ?? "bg-slate-100 text-slate-700 border-slate-200"
                      }`}
                    >
                      {roleLabels[user.role] ?? user.role}
                    </span>
                    <StatusBadge status={user.status} className="text-[10px]" />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Organizations */}
          <Card
            title="Organizações demonstrativas / Tenants"
            description="Planos e limites demonstrativos. Não há billing, tenant admin real ou alteração de organização nesta tela."
          >
            <div className="space-y-4">
              {mockOrganizations.map((org) => (
                <div
                  className="rounded-lg border border-[var(--border)] bg-[var(--surf2)] p-4"
                  key={org.id}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-teal/10 border border-brand-teal/20">
                        <Building2 className="text-brand-teal-dark" size={16} />
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-[var(--text)]">
                          {org.name}
                        </p>
                        <p className="text-[11px] text-[var(--text2)]">{org.cnpj}</p>
                      </div>
                    </div>
                    <span className="rounded-full bg-brand-teal/10 px-2 py-0.5 text-[10px] font-semibold text-brand-teal-light capitalize">
                      {org.plan}
                    </span>
                  </div>
                  <div className="mt-3">
                    <div className="flex items-center justify-between mb-1.5 text-[11px]">
                      <span className="text-[var(--text2)]">Uso local demonstrativo</span>
                      <span className="font-semibold text-[var(--text)]">
                        {org.casesUsed}/{org.casesLimit}
                      </span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-slate-200">
                      <div
                        className="h-1.5 rounded-full bg-brand-blue transition-all"
                        style={{
                          width: `${(org.casesUsed / org.casesLimit) * 100}%`
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Cases by status */}
          <Card
            title="Casos por status mockado"
            description="Distribuição derivada dos mocks existentes para orientar a operação."
          >
            <div className="space-y-3">
              {statusCounts.map((item) => (
                <div key={item.label}>
                  <div className="flex items-center justify-between mb-1.5">
                    <p className="text-xs text-[var(--text2)]">{item.label}</p>
                    <p className={`text-sm font-bold ${item.color}`}>
                      {item.count}
                    </p>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className={`h-1.5 rounded-full ${
                        item.color.replace("text-", "bg-")
                      }`}
                      style={{
                        width: `${(item.count / mockCases.length) * 100}%`
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Audit logs */}
          <Card
            title="Registros de auditoria mockados"
            description="Trilha visual de referência. Logs reais, retenção e auditoria real dependem de backend/auth aprovados."
          >
            <div className="space-y-3">
              {mockAuditLogs.map((log) => (
                <div
                  className="flex items-start gap-3 rounded-lg border border-[var(--border)] bg-[var(--surf2)] p-3"
                  key={log.id}
                >
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-teal/10 border border-brand-teal/20">
                    <Shield className="text-brand-teal" size={12} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-[11px] font-semibold text-[var(--text)]">
                        {auditActionLabel[log.action] ?? log.action}
                      </p>
                      <span className="shrink-0 text-[10px] text-[var(--text2)]">
                        {formatDate(log.createdAt)}
                      </span>
                    </div>
                    <p className="text-[11px] text-[var(--text2)]">{log.description}</p>
                    <p className="text-[10px] text-[var(--text2)]">{log.userName}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Roles & permissions reference */}
        <div className="mt-6">
          <Card
            title="Roles e permissões como referência local"
            description="Leitura conceitual dos papéis do MVP. Não altera guards, claims, RBAC técnico ou permissões reais."
          >
            <div className="grid gap-3 sm:grid-cols-2">
              {[
                {
                  role: "admin",
                  desc: "Referência de governança: organiza a leitura local de equipe, organização e limites do MVP."
                },
                {
                  role: "analyst",
                  desc: "Referência operacional: acompanha triagem e revisão conceitual sem aprovação persistida."
                },
                {
                  role: "client",
                  desc: "Referência de relacionamento: inicia pedidos, acompanha casos e documentos quando o fluxo existir."
                },
                {
                  role: "viewer",
                  desc: "Referência de leitura: acompanha informações sem permissões técnicas novas nesta tela."
                }
              ].map((item) => (
                <div
                  className="flex items-start gap-3 rounded-lg border border-[var(--border)] bg-[var(--surf2)] p-4"
                  key={item.role}
                >
                  <span
                    className={`inline-flex items-center rounded border px-2.5 py-1 text-xs font-semibold shrink-0 ${
                      roleColors[item.role] ?? "bg-slate-100 text-slate-700 border-slate-200"
                    }`}
                  >
                    {roleLabels[item.role]}
                  </span>
                  <p className="text-xs leading-5 text-[var(--text2)]">{item.desc}</p>
                </div>
              ))}
            </div>

            <div className="mt-5 rounded-lg border border-[var(--border)] bg-[var(--surf2)] p-4">
              <div className="flex items-start gap-3">
                <TrendingUp className="mt-0.5 shrink-0 text-brand-teal" size={16} />
                <div>
                  <p className="text-xs font-semibold text-[var(--text)]">
                    Roadmap administrativo
                  </p>
                  <p className="mt-1 text-xs leading-5 text-[var(--text2)]">
                    Membros funcionais, convite/cadastro por e-mail, verificação
                    de e-mail, criação de senha, sessões reais com localização
                    aproximada e notificações por e-mail/WhatsApp ficam para uma
                    etapa com backend, auth e serviços externos definidos.
                  </p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </AppLayout>
    </AuthGuard>
  );
}
