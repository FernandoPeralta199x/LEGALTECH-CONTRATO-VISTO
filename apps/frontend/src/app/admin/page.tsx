import {
  Activity,
  Building2,
  DollarSign,
  Lock,
  Settings,
  Shield,
  TrendingUp,
  Users
} from "lucide-react";
import Link from "next/link";

import { AppLayout } from "@/components/AppLayout";
import { AuthGuard } from "@/components/AuthGuard";
import { Card } from "@/components/Card";
import { PageTitle } from "@/components/PageTitle";

const roleColors: Record<string, string> = {
  admin: "bg-brand-teal/10 text-brand-teal-dark border-brand-teal/20",
  analyst: "bg-brand-teal/10 text-brand-teal-light border-brand-teal/20",
  client: "bg-slate-100 text-slate-700 border-slate-200",
  owner: "bg-purple-500/10 text-purple-300 border-purple-500/20",
  support: "bg-amber-50 text-amber-700 border-amber-500/20",
  viewer: "bg-slate-600/10 text-slate-600 border-slate-600/20"
};

const roleLabels: Record<string, string> = {
  admin: "Admin",
  analyst: "Analista",
  client: "Cliente",
  owner: "Owner",
  support: "Suporte",
  viewer: "Viewer"
};

export default function AdminPage() {
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
                Configurações
              </Link>
              <Link
                className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surf)] px-3.5 py-2.5 text-sm font-medium text-[var(--text)] transition hover:border-brand-teal/40"
                href="/admin/pricing"
              >
                <DollarSign size={15} />
                Pricing
              </Link>
            </>
          }
          description="Visão de governança local do MVP. Convites, gerenciamento real de usuários, RBAC, sessões, auditoria e billing dependem de backend e auth aprovados para produção."
          eyebrow="Administração"
          title="Governança operacional"
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

        <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[
            {
              label: "Membros ativos",
              value: "—",
              hint: "Gerenciamento real de equipe em construção.",
              icon: Users,
              color: "text-brand-teal-dark",
              bg: "bg-brand-teal/10 border-brand-teal/20"
            },
            {
              label: "Organizações",
              value: "—",
              hint: "Tenant admin real em construção.",
              icon: Building2,
              color: "text-brand-teal-light",
              bg: "bg-brand-teal/10 border-brand-teal/20"
            },
            {
              label: "Casos ativos",
              value: "—",
              hint: "Métricas operacionais reais em construção.",
              icon: Activity,
              color: "text-violet-700",
              bg: "bg-violet-500/10 border-violet-500/20"
            },
            {
              label: "Registros de auditoria",
              value: "—",
              hint: "Trilha auditável real em construção.",
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
          <Card
            title="Equipe"
            description="Gerenciamento real de usuários, convites e papéis será habilitado quando auth/RBAC real for integrado."
          >
            <div className="rounded-lg border border-[var(--border)] bg-[var(--surf2)] p-6 text-center">
              <p className="text-sm text-[var(--text2)]">
                Nenhum dado de equipe disponível no MVP local.
              </p>
            </div>
          </Card>

          <Card
            title="Organizações / Tenants"
            description="Configuração real de organizações, planos e limites será habilitada quando tenant admin for integrado."
          >
            <div className="rounded-lg border border-[var(--border)] bg-[var(--surf2)] p-6 text-center">
              <p className="text-sm text-[var(--text2)]">
                Nenhuma organização administrável nesta tela.
              </p>
            </div>
          </Card>
        </div>

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
                    className={`inline-flex shrink-0 items-center rounded border px-2.5 py-1 text-xs font-semibold ${
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
