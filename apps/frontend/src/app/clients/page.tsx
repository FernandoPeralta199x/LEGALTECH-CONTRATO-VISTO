"use client";

import {
  BriefcaseBusiness,
  Pencil,
  Mail,
  Phone,
  Plus,
  RefreshCw,
  Search,
  UsersRound
} from "lucide-react";
import type { FormEvent } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AppLayout } from "@/components/AppLayout";
import { AuthGuard } from "@/components/AuthGuard";
import { Button } from "@/components/Button";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { FormField, SelectInput, TextInput } from "@/components/FormField";
import { LoadingState } from "@/components/LoadingState";
import { Notification } from "@/components/Notification";
import { PageTitle } from "@/components/PageTitle";
import { StatusBadge } from "@/components/StatusBadge";
import { formatDate } from "@/lib/formatters";
import { errorMessage } from "@/src/lib/errorMessage";
import { createClient, listClients, updateClient } from "@/src/services/clients";
import { validateClientForm, type ValidationErrors } from "@/src/lib/validation";
import {
  buildClientCreatePayload,
  buildClientUpdatePayload,
  clientContractRoleLabels,
  clientFormFromClient,
  clientPersonTypeLabels,
  emptyClientForm,
  maskBirthDate,
  maskCnpj,
  maskCpf,
  maskPhone,
  type ClientFormState
} from "@/src/lib/clientForm";
import type { Client } from "@/types";

const riskConfig: Record<string, { label: string; className: string }> = {
  high: { label: "Indicador local alto", className: "text-red-700 bg-red-50 border-red-200" },
  low: { label: "Indicador local baixo", className: "text-green-700 bg-green-50 border-green-200" },
  medium: { label: "Indicador local médio", className: "text-amber-700 bg-amber-50 border-amber-200" }
};

const contractRoleOptions = Object.entries(clientContractRoleLabels);

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [error, setError] = useState("");
  const [fallbackReason, setFallbackReason] = useState("");
  const [editingClient, setEditingClient] = useState<Client | null>(null);
  const [form, setForm] = useState<ClientFormState>(emptyClientForm);
  const [formErrors, setFormErrors] = useState<ValidationErrors>({});
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  const refreshClients = useCallback(async () => {
    setLoading(true);
    setError("");
    setSuccessMessage("");

    try {
      const result = await listClients();
      setClients(result.data);
      setFallbackReason(result.source === "mock" ? result.fallbackReason ?? "" : "");
    } catch (err) {
      setError(errorMessage(err, "Não foi possível carregar clientes."));
      setFallbackReason("");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refreshClients();
    }, 0);

    return () => window.clearTimeout(timer);
  }, [refreshClients]);

  const filteredClients = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      return clients;
    }

    return clients.filter((client) =>
      [
        client.displayName,
        client.name,
        client.email,
        client.phone,
        client.documentLabel,
        clientContractRoleLabels[client.contractRole ?? "other"],
        client.personType ? clientPersonTypeLabels[client.personType] : ""
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalized)
    );
  }, [clients, query]);

  function updateForm<K extends keyof ClientFormState>(
    field: K,
    value: ClientFormState[K]
  ) {
    const maskedValue =
      field === "cpf"
        ? maskCpf(String(value))
        : field === "cnpj"
          ? maskCnpj(String(value))
          : field === "phone"
            ? maskPhone(String(value))
            : field === "birthDate"
              ? maskBirthDate(String(value))
              : value;

    setForm((current) => ({ ...current, [field]: maskedValue }));
    setFormErrors((current) => ({ ...current, [field]: "" }));
    setError("");
    setSuccessMessage("");
  }

  function resetFormState() {
    setEditingClient(null);
    setForm(emptyClientForm);
    setFormErrors({});
    setShowForm(false);
  }

  function startCreateClient() {
    setEditingClient(null);
    setForm(emptyClientForm);
    setFormErrors({});
    setShowForm(true);
    setError("");
    setSuccessMessage("");
  }

  function startEditClient(client: Client) {
    setEditingClient(client);
    setForm(clientFormFromClient(client));
    setFormErrors({});
    setShowForm(true);
    setError("");
    setSuccessMessage("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting) {
      return;
    }

    const validation = validateClientForm(form);
    setFormErrors(validation.errors);
    if (!validation.valid) {
      setError("Revise os campos destacados antes de salvar o cliente.");
      return;
    }

    setSubmitting(true);
    setError("");
    setSuccessMessage("");

    try {
      const result = editingClient
        ? await updateClient(
            editingClient.id,
            buildClientUpdatePayload(form, editingClient)
          )
        : await createClient(buildClientCreatePayload(form));
      setClients((current) =>
        editingClient
          ? current.map((client) =>
              client.id === result.data.id ? result.data : client
            )
          : [result.data, ...current]
      );
      setFallbackReason(result.source === "mock" ? result.fallbackReason ?? "" : "");
      setSuccessMessage(
        result.source === "mock"
          ? editingClient
            ? "Registro local atualizado no fallback de desenvolvimento."
            : "Fallback local explícito criado no navegador de desenvolvimento."
          : editingClient
            ? "Registro de cliente atualizado pela API local."
            : "Registro de cliente criado pela API local."
      );
      resetFormState();
    } catch (err) {
      setError(errorMessage(err, "Não foi possível salvar cliente."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthGuard>
      <AppLayout>
        <PageTitle
          actions={
            <div className="flex flex-wrap items-center gap-2">
              <Button
                href="/cases/new"
                icon={<Plus aria-hidden="true" size={15} />}
              >
                Novo Pedido
              </Button>
              <Button
                icon={<RefreshCw aria-hidden="true" size={15} />}
                loading={loading}
                onClick={() => void refreshClients()}
                variant="secondary"
              >
                Atualizar
              </Button>
              <Button
                icon={<Plus aria-hidden="true" size={15} />}
                onClick={startCreateClient}
                variant="secondary"
              >
                Novo cliente
              </Button>
            </div>
          }
          description="Organize a base de relacionamento jurídico do MVP local e use esses dados como referência para Novo Pedido, Casos, Documentos e Relatórios."
          eyebrow="Clientes"
          title="Base de relacionamento jurídico"
        />

        {fallbackReason && (
          <Notification title="Fallback local ativo" tone="warning">
            A API não respondeu. A lista não usa clientes demonstrativos; novos cadastros em fallback ficam explícitos neste navegador de desenvolvimento.
          </Notification>
        )}
        {successMessage && (
          <Notification onDismiss={() => setSuccessMessage("")} title="Ação local registrada" tone="success">
            {successMessage}
          </Notification>
        )}
        {error && !loading && (
          <Notification onDismiss={() => setError("")} title="Atenção" tone="error">
            {error}
          </Notification>
        )}

        {showForm && (
          <form
            className="cv-form-card mb-6 p-4 sm:p-5"
            onSubmit={handleSubmit}
          >
            <div className="mb-4 flex flex-col gap-1">
              <h2 className="text-sm font-semibold text-[var(--text)]">
                {editingClient ? "Editar cliente" : "Novo cliente"}
              </h2>
              <p className="text-xs leading-5 text-[var(--text2)]">
                {editingClient
                  ? "Edite apenas dados cadastrais. Organização e permissões continuam vindo do JWT/contexto da API local."
                  : "Cadastre um cliente local para organizar partes e iniciar pedidos no MVP local. Organização e permissões continuam vindo do JWT/contexto da API local."}
              </p>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField error={formErrors.personType} label="Tipo de pessoa" required>
                <SelectInput
                  className="text-sm"
                  onChange={(event) =>
                    updateForm(
                      "personType",
                      event.target.value as ClientFormState["personType"]
                    )
                  }
                  value={form.personType}
                >
                  <option value="individual">Pessoa física</option>
                  <option value="company">Pessoa jurídica</option>
                </SelectInput>
              </FormField>
              <FormField error={formErrors.contractRole} label="Papel no contrato" required>
                <SelectInput
                  className="text-sm"
                  onChange={(event) =>
                    updateForm(
                      "contractRole",
                      event.target.value as ClientFormState["contractRole"]
                    )
                  }
                  value={form.contractRole}
                >
                  <option value="">Selecione</option>
                  {contractRoleOptions.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </SelectInput>
              </FormField>

              {form.personType === "individual" ? (
                <>
                  <FormField error={formErrors.fullName} label="Nome completo" required>
                    <TextInput
                      invalid={Boolean(formErrors.fullName)}
                      onChange={(event) => updateForm("fullName", event.target.value)}
                      placeholder="João da Silva"
                      value={form.fullName}
                    />
                  </FormField>
                  <FormField error={formErrors.cpf} label="CPF">
                    <TextInput
                      inputMode="numeric"
                      invalid={Boolean(formErrors.cpf)}
                      onChange={(event) => updateForm("cpf", event.target.value)}
                      placeholder="000.000.000-00"
                      value={form.cpf}
                    />
                  </FormField>
                  <FormField label="RG">
                    <TextInput
                      onChange={(event) => updateForm("rg", event.target.value)}
                      placeholder="00.000.000-0"
                      value={form.rg}
                    />
                  </FormField>
                  <FormField error={formErrors.birthDate} label="Data de nascimento">
                    <TextInput
                      inputMode="numeric"
                      invalid={Boolean(formErrors.birthDate)}
                      onChange={(event) => updateForm("birthDate", event.target.value)}
                      placeholder="dd/mm/aaaa"
                      value={form.birthDate}
                    />
                  </FormField>
                </>
              ) : (
                <>
                  <FormField error={formErrors.legalName} label="Razão social" required>
                    <TextInput
                      invalid={Boolean(formErrors.legalName)}
                      onChange={(event) => updateForm("legalName", event.target.value)}
                      placeholder="Acme Comércio Ltda"
                      value={form.legalName}
                    />
                  </FormField>
                  <FormField label="Nome fantasia">
                    <TextInput
                      onChange={(event) => updateForm("tradeName", event.target.value)}
                      placeholder="Acme"
                      value={form.tradeName}
                    />
                  </FormField>
                  <FormField error={formErrors.cnpj} label="CNPJ">
                    <TextInput
                      inputMode="numeric"
                      invalid={Boolean(formErrors.cnpj)}
                      onChange={(event) => updateForm("cnpj", event.target.value)}
                      placeholder="00.000.000/0000-00"
                      value={form.cnpj}
                    />
                  </FormField>
                </>
              )}

              <FormField error={formErrors.email} label="E-mail">
                <TextInput
                  invalid={Boolean(formErrors.email)}
                  onChange={(event) => updateForm("email", event.target.value)}
                  placeholder="contato@example.test"
                  type="email"
                  value={form.email}
                />
              </FormField>
              <FormField error={formErrors.phone} label="Telefone">
                <TextInput
                  inputMode="tel"
                  invalid={Boolean(formErrors.phone)}
                  onChange={(event) => updateForm("phone", event.target.value)}
                  placeholder="(11) 98888-7777"
                  value={form.phone}
                />
              </FormField>
              <div className="md:col-span-2">
                <FormField label="Endereço">
                  <textarea
                    className="cv-input min-h-24 w-full resize-y text-sm"
                    onChange={(event) => updateForm("address", event.target.value)}
                    placeholder="Rua, número, bairro, cidade - UF"
                    value={form.address}
                  />
                </FormField>
              </div>
            </div>
            <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <Button disabled={submitting} onClick={resetFormState} variant="secondary">
                Cancelar
              </Button>
              <Button loading={submitting} type="submit">
                {editingClient ? "Atualizar cliente" : "Salvar cliente"}
              </Button>
            </div>
          </form>
        )}

        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div className="relative w-full max-w-sm">
            <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text3)]" size={14} />
            <input
              className="cv-input w-full pl-9 pr-3 text-sm"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar por nome, documento, e-mail ou telefone..."
              type="search"
              value={query}
            />
          </div>
          {!loading && (
            <p className="text-xs text-[var(--text2)]">
              {filteredClients.length} cliente{filteredClients.length !== 1 ? "s" : ""} exibido{filteredClients.length !== 1 ? "s" : ""}
            </p>
          )}
        </div>

        {loading ? (
          <LoadingState
            description="Consultando a base local ou a API configurada para clientes."
            label="Carregando clientes"
          />
        ) : error && clients.length === 0 ? (
          <ErrorState
            action={
              <Button icon={<RefreshCw size={15} />} onClick={() => void refreshClients()} variant="secondary">
                Tentar novamente
              </Button>
            }
            description="A listagem de clientes não pôde ser carregada. Erros de autorização e validação da API local são exibidos sem fallback."
            details={error}
          />
        ) : filteredClients.length === 0 ? (
          <EmptyState
            action={
              query ? (
                <Button icon={<Search size={15} />} onClick={() => setQuery("")} variant="secondary">
                  Limpar busca
                </Button>
              ) : (
                <Button href="/cases/new" icon={<Plus size={15} />}>
                  Novo Pedido
                </Button>
              )
            }
            secondaryAction={
              <Button icon={<Plus size={15} />} onClick={startCreateClient} variant="secondary">
                Novo cliente
              </Button>
            }
            description={
              query
                ? "Nenhum cliente corresponde à busca atual. Limpe a busca ou inicie um Novo Pedido quando o atendimento precisar seguir."
                : "Cadastre clientes locais para organizar contatos e partes, ou inicie Novo Pedido como fluxo principal do MVP local."
            }
            icon={<UsersRound size={20} />}
            title={query ? "Busca sem resultados" : "Sem clientes na base local"}
          />
        ) : (
          <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
            {filteredClients.map((client) => {
              const risk = riskConfig[client.riskLevel] ?? riskConfig.low;
              const displayName = client.displayName ?? client.name;
              const personTypeLabel = client.personType
                ? clientPersonTypeLabels[client.personType]
                : "Tipo não informado";
              const contractRoleLabel = client.contractRole
                ? clientContractRoleLabels[client.contractRole]
                : "Papel não informado";
              return (
                <div
                  className="cv-card cv-card-hover p-5"
                  key={client.id}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex min-w-0 items-center gap-3">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-brand text-sm font-bold text-white">
                        {displayName.slice(0, 2).toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-[var(--text)]">{displayName}</p>
                        <p className="truncate text-[11px] text-[var(--text3)]">{client.documentLabel}</p>
                      </div>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      <Button
                        aria-label={`Editar cliente ${displayName}`}
                        icon={<Pencil aria-hidden="true" size={14} />}
                        onClick={() => startEditClient(client)}
                        size="sm"
                        variant="secondary"
                      >
                        Editar
                      </Button>
                      <StatusBadge status={client.status} />
                    </div>
                  </div>

                  <dl className="mt-4 space-y-2 text-xs">
                    <div className="flex min-w-0 items-center gap-2 text-[var(--text2)]">
                      <UsersRound size={12} className="shrink-0 text-[var(--text3)]" />
                      <span className="truncate">
                        {personTypeLabel} · {contractRoleLabel}
                      </span>
                    </div>
                    <div className="flex min-w-0 items-center gap-2 text-[var(--text2)]">
                      <Mail size={12} className="shrink-0 text-[var(--text3)]" />
                      <span className="truncate">{client.email || "E-mail não informado"}</span>
                    </div>
                    <div className="flex min-w-0 items-center gap-2 text-[var(--text2)]">
                      <Phone size={12} className="shrink-0 text-[var(--text3)]" />
                      <span className="truncate">{client.phone || "Telefone não informado"}</span>
                    </div>
                    <div className="flex items-center gap-2 text-[var(--text2)]">
                      <BriefcaseBusiness size={12} className="shrink-0 text-[var(--text3)]" />
                      <span className="truncate">
                        {client.casesCount > 0
                          ? `${client.casesCount} referência${client.casesCount !== 1 ? "s" : ""} de caso${client.casesCount !== 1 ? "s" : ""} indicada${client.casesCount !== 1 ? "s" : ""} na base`
                          : "Acompanhe referências de casos na área de Casos"}
                      </span>
                    </div>
                  </dl>

                  <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-[var(--bd)] pt-4">
                    <span
                      className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-semibold ${risk.className}`}
                      title="Indicador operacional local; não substitui revisão jurídica."
                    >
                      {risk.label}
                    </span>
                    <span className="text-[11px] text-[var(--text3)]">
                      {client.sourceMode ? `Origem: ${client.sourceMode} · ` : ""}
                      Registro desde {formatDate(client.createdAt)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </AppLayout>
    </AuthGuard>
  );
}
