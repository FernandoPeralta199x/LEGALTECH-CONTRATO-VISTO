"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Save,
  AlertTriangle,
  CheckCircle,
  Settings,
  Layers,
  Shield,
  RotateCcw,
  Info,
} from "lucide-react";

import { AuthGuard } from "@/components/AuthGuard";
import { AppLayout } from "@/components/AppLayout";
import { PageTitle } from "@/components/PageTitle";
import { Card } from "@/components/Card";
import { CurrencyInput, centsToReaisLabel } from "@/components/CurrencyInput";

import {
  getPricingCatalog,
  getPricingConfig,
  updatePricingConfig,
  checkCasesLimit,
  type PricingCatalog,
  type PricingConfig,
  type CasesLimitCheck,
  type UpdatePricingConfigPayload,
} from "@/src/services/pricing";
import { errorMessage } from "@/src/lib/errorMessage";

const TOAST_MS = 4000;

type Status = "idle" | "loading" | "saving" | "success" | "error";

function useToast() {
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(
    null
  );

  useEffect(() => {
    if (!message) return;
    const t = setTimeout(() => setMessage(null), TOAST_MS);
    return () => clearTimeout(t);
  }, [message]);

  return { message, setMessage };
}

export default function AdminPricingPage() {
  const router = useRouter();

  const [catalog, setCatalog] = useState<PricingCatalog | null>(null);
  const [config, setConfig] = useState<PricingConfig | null>(null);
  const [limitCheck, setLimitCheck] = useState<CasesLimitCheck | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const { message, setMessage } = useToast();

  // Form state
  const [casesLimit, setCasesLimit] = useState<number | null>(null);
  const [unlimitedCases, setUnlimitedCases] = useState(true);
  const [moduleOverrides, setModuleOverrides] = useState<
    Record<string, number | null>
  >({});
  const [variantOverrides, setVariantOverrides] = useState<
    Record<string, Record<string, { price_cents: number | null; installments: number | null }>>
  >({});
  const [notes, setNotes] = useState("");

  const loadData = useCallback(async () => {
    setStatus("loading");
    try {
      const [cat, cfg, lim] = await Promise.all([
        getPricingCatalog(),
        getPricingConfig(),
        checkCasesLimit(),
      ]);
      setCatalog(cat);
      setConfig(cfg);
      setLimitCheck(lim);

      const unlimited = cfg.cases_limit === null;
      setUnlimitedCases(unlimited);
      setCasesLimit(unlimited ? null : cfg.cases_limit);

      setModuleOverrides(
        Object.fromEntries(
          Object.entries(cfg.module_overrides).map(([k, v]) => [k, v.price_cents])
        )
      );

      const initialVariants: Record<
        string,
        Record<string, { price_cents: number | null; installments: number | null }>
      > = {};
      for (const [productCode, variants] of Object.entries(
        cfg.product_variant_overrides
      )) {
        initialVariants[productCode] = Object.fromEntries(
          Object.entries(variants).map(([variantCode, v]) => [
            variantCode,
            { price_cents: v.price_cents, installments: v.installments }
          ])
        );
      }
      setVariantOverrides(initialVariants);

      setNotes(cfg.notes ?? "");
      setStatus("idle");
    } catch (err) {
      setMessage({
        text: errorMessage(err, "API local indisponível. Verifique se o backend e o PostgreSQL estão rodando e se você está logado."),
        type: "error",
      });
      setStatus("error");
    }
  }, [setMessage]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const hasChanges = useMemo(() => {
    if (!config) return false;
    const initialUnlimited = config.cases_limit === null;
    if (initialUnlimited !== unlimitedCases) return true;
    if (!unlimitedCases && casesLimit !== config.cases_limit) return true;

    const initialModules = Object.fromEntries(
      Object.entries(config.module_overrides).map(([k, v]) => [k, v.price_cents])
    );

    if (notes.trim() !== (config.notes ?? "").trim()) return true;

    const allModuleKeys = new Set([
      ...Object.keys(initialModules),
      ...Object.keys(moduleOverrides),
    ]);
    for (const key of allModuleKeys) {
      if ((initialModules[key] ?? null) !== (moduleOverrides[key] ?? null)) return true;
    }

    const initialVariantMap = new Map<string, number | null>();
    const currentVariantMap = new Map<string, number | null>();
    for (const [productCode, variants] of Object.entries(
      config.product_variant_overrides ?? {}
    )) {
      for (const [variantCode, v] of Object.entries(variants)) {
        initialVariantMap.set(`${productCode}.${variantCode}.price`, v.price_cents);
        initialVariantMap.set(`${productCode}.${variantCode}.installments`, v.installments);
      }
    }
    for (const [productCode, variants] of Object.entries(variantOverrides)) {
      for (const [variantCode, v] of Object.entries(variants)) {
        currentVariantMap.set(`${productCode}.${variantCode}.price`, v.price_cents);
        currentVariantMap.set(`${productCode}.${variantCode}.installments`, v.installments);
      }
    }
    const allVariantKeys = new Set([
      ...initialVariantMap.keys(),
      ...currentVariantMap.keys(),
    ]);
    for (const key of allVariantKeys) {
      if (initialVariantMap.get(key) !== currentVariantMap.get(key)) return true;
    }

    return false;
  }, [config, unlimitedCases, casesLimit, moduleOverrides, variantOverrides, notes]);

  const handleReset = () => {
    if (!config) return;
    const unlimited = config.cases_limit === null;
    setUnlimitedCases(unlimited);
    setCasesLimit(unlimited ? null : config.cases_limit);
    setModuleOverrides(
      Object.fromEntries(
        Object.entries(config.module_overrides).map(([k, v]) => [k, v.price_cents])
      )
    );

    const initialVariants: Record<
      string,
      Record<string, { price_cents: number | null; installments: number | null }>
    > = {};
    for (const [productCode, variants] of Object.entries(
      config.product_variant_overrides
    )) {
      initialVariants[productCode] = Object.fromEntries(
        Object.entries(variants).map(([variantCode, v]) => [
          variantCode,
          { price_cents: v.price_cents, installments: v.installments }
        ])
      );
    }
    setVariantOverrides(initialVariants);

    setNotes(config.notes ?? "");
  };

  const handleSave = async () => {
    setStatus("saving");
    setMessage(null);
    try {
      const payload: UpdatePricingConfigPayload = {
        cases_limit: unlimitedCases ? null : casesLimit ?? null,
      };

      const modOv: Record<string, { price_cents: number }> = {};
      for (const [code, cents] of Object.entries(moduleOverrides)) {
        if (cents !== null && !Number.isNaN(cents) && cents >= 0) {
          modOv[code] = { price_cents: cents };
        }
      }
      payload.module_overrides = modOv;

      const varOv: Record<string, Record<string, { price_cents: number; installments: number }>> = {};
      for (const [productCode, variants] of Object.entries(variantOverrides)) {
        for (const [variantCode, v] of Object.entries(variants)) {
          const price = v.price_cents;
          const installments = v.installments ?? 10;
          if (price !== null && !Number.isNaN(price) && price >= 0 && installments >= 1) {
            if (!varOv[productCode]) varOv[productCode] = {};
            varOv[productCode][variantCode] = { price_cents: price, installments };
          }
        }
      }
      if (Object.keys(varOv).length > 0) {
        payload.product_variant_overrides = varOv;
      }

      payload.notes = notes.trim() || null;

      const updated = await updatePricingConfig(payload);
      setConfig(updated);
      setMessage({
        text: `Configuração salva (versão ${updated.version}).`,
        type: "success",
      });
      setStatus("idle");

      const lim = await checkCasesLimit();
      setLimitCheck(lim);
    } catch (err) {
      setMessage({
        text: errorMessage(err, "Erro ao salvar."),
        type: "error",
      });
      setStatus("error");
    }
  };

  const isLoading = status === "loading";
  const isSaving = status === "saving";

  return (
    <AuthGuard>
      <AppLayout>
        <div className="mx-auto max-w-5xl space-y-6">
          {/* Header */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/admin")}
              className="rounded-lg p-2 transition-opacity hover:opacity-80"
              style={{ color: "var(--text2)" }}
            >
              <ArrowLeft size={20} />
            </button>
            <PageTitle
              title="Configuração de Pricing"
              description="Gerencie limites, preços e overrides por organização"
              eyebrow="Administração"
            />
          </div>

          {/* Toast */}
          {message && (
            <div
              className="flex items-center gap-2 rounded-lg p-3 text-sm"
              style={{
                background:
                  message.type === "error"
                    ? "rgba(239, 68, 68, 0.1)"
                    : "rgba(34, 197, 94, 0.1)",
                color: message.type === "error" ? "#ef4444" : "#22c55e",
                border:
                  message.type === "error"
                    ? "1px solid rgba(239, 68, 68, 0.2)"
                    : "1px solid rgba(34, 197, 94, 0.2)",
              }}
            >
              {message.type === "error" ? (
                <AlertTriangle size={16} />
              ) : (
                <CheckCircle size={16} />
              )}
              {message.text}
            </div>
          )}

          {isLoading ? (
            <div
              className="py-12 text-center text-sm"
              style={{ color: "var(--text2)" }}
            >
              Carregando...
            </div>
          ) : (
            <>
              {/* Cases Limit + Status */}
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <Card title="Limite de Casos">
                  <div className="mb-4 flex items-center gap-2">
                    <Shield size={18} style={{ color: "var(--accent)" }} />
                    <h3 className="font-semibold" style={{ color: "var(--text)" }}>
                      Limite de Casos
                    </h3>
                  </div>
                  <div className="space-y-3">
                    <label className="flex cursor-pointer items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={unlimitedCases}
                        onChange={(e) => setUnlimitedCases(e.target.checked)}
                        className="rounded border-[var(--bd)] bg-[var(--surf2)] text-[var(--accent)]"
                      />
                      <span style={{ color: "var(--text2)" }}>
                        Ilimitado (sem restrição)
                      </span>
                    </label>
                    {!unlimitedCases && (
                      <div className="space-y-1">
                        <label
                          className="text-xs"
                          style={{ color: "var(--text3)" }}
                        >
                          Quantidade máxima de casos ativos
                        </label>
                        <input
                          type="number"
                          min={1}
                          value={casesLimit ?? ""}
                          onChange={(e) => {
                            const v = e.target.value;
                            setCasesLimit(v === "" ? null : parseInt(v, 10));
                          }}
                          placeholder="Ex: 100"
                          className="w-full rounded-lg border border-[var(--bd)] bg-[var(--surf2)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--accent)]"
                        />
                      </div>
                    )}
                  </div>
                </Card>

                <Card title="Status Atual">
                  <div className="mb-4 flex items-center gap-2">
                    <Settings size={18} style={{ color: "var(--accent)" }} />
                    <h3 className="font-semibold" style={{ color: "var(--text)" }}>
                      Status Atual
                    </h3>
                  </div>
                  <div className="space-y-2 text-sm">
                    {limitCheck && (
                      <>
                        <div className="flex justify-between">
                          <span style={{ color: "var(--text2)" }}>Casos ativos</span>
                          <span style={{ color: "var(--text)" }}>
                            {limitCheck.active_cases_count}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span style={{ color: "var(--text2)" }}>Limite</span>
                          <span style={{ color: "var(--text)" }}>
                            {limitCheck.cases_limit ?? "Ilimitado"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span style={{ color: "var(--text2)" }}>Pode criar</span>
                          <span
                            style={{
                              color: limitCheck.allowed ? "#22c55e" : "#ef4444",
                            }}
                          >
                            {limitCheck.allowed ? "Sim" : "Não"}
                          </span>
                        </div>
                      </>
                    )}
                    {config && (
                      <div
                        className="mt-2 flex justify-between pt-2"
                        style={{ borderTop: "1px solid var(--bd)" }}
                      >
                        <span style={{ color: "var(--text2)" }}>Versão</span>
                        <span style={{ color: "var(--text)" }}>{config.version}</span>
                      </div>
                    )}
                  </div>
                </Card>
              </div>

              {/* Module Overrides */}
              {catalog && (
                <Card
                  title={
                    <span className="flex items-center gap-2">
                      <Layers size={18} style={{ color: "var(--accent)" }} />
                      Preços de Módulos
                    </span>
                  }
                  description="Deixe vazio para usar o padrão. Os preços dos produtos são calculados automaticamente a partir dos módulos obrigatórios."
                  actions={
                    <span
                      className="inline-flex items-center gap-1 text-xs"
                      style={{ color: "var(--text3)" }}
                    >
                      <Info size={13} /> Valores em reais
                    </span>
                  }
                >
                  <div className="space-y-3">
                    {catalog.modules.map((mod) => {
                      const overrideCents = moduleOverrides[mod.code] ?? null;
                      const hasOverride = overrideCents !== null;
                      return (
                        <div
                          key={mod.code}
                          className="flex flex-col gap-3 rounded-lg border border-[var(--bd)] bg-[var(--surf2)] p-3 sm:flex-row sm:items-center"
                        >
                          <div className="min-w-0 flex-1">
                            <div
                              className="text-sm font-medium"
                              style={{ color: "var(--text)" }}
                            >
                              {mod.title}
                            </div>
                            <div
                              className="mt-0.5 flex items-center gap-2 text-xs"
                              style={{ color: "var(--text2)" }}
                            >
                              <span>Padrão: {centsToReaisLabel(mod.price_cents)}</span>
                              {hasOverride && (
                                <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-400">
                                  override
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <CurrencyInput
                              value={overrideCents}
                              onChange={(cents) =>
                                setModuleOverrides((prev) => ({
                                  ...prev,
                                  [mod.code]: cents,
                                }))
                              }
                              placeholder={centsToReaisLabel(mod.price_cents)}
                              className="w-40"
                              aria-label={`Preço override para ${mod.title}`}
                            />
                            {hasOverride && (
                              <button
                                type="button"
                                onClick={() =>
                                  setModuleOverrides((prev) => ({
                                    ...prev,
                                    [mod.code]: null,
                                  }))
                                }
                                className="text-xs text-[var(--text3)] underline hover:text-[var(--text)]"
                              >
                                usar padrão
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              )}

              {/* Product Variants Overrides */}
              {catalog && (
                <Card
                  title={
                    <span className="flex items-center gap-2">
                      <Layers size={18} style={{ color: "var(--accent)" }} />
                      Preços de Variantes de Produto
                    </span>
                  }
                  description="Edite o preço e o número de parcelas para cada variante disponível. Deixe vazio para usar o padrão."
                  actions={
                    <span
                      className="inline-flex items-center gap-1 text-xs"
                      style={{ color: "var(--text3)" }}
                    >
                      <Info size={13} /> Valores em reais
                    </span>
                  }
                >
                  <div className="space-y-6">
                    {catalog.products
                      .filter((p) => (p.variants?.length ?? 0) > 0)
                      .map((product) => (
                        <div key={product.code}>
                          <h4
                            className="mb-2 text-sm font-semibold"
                            style={{ color: "var(--text)" }}
                          >
                            {product.title}
                          </h4>
                          <div className="space-y-3">
                            {product.variants?.map((variant) => {
                              const ov = variantOverrides[product.code]?.[variant.code] ?? {
                                price_cents: null,
                                installments: null,
                              };
                              const hasOverride = ov.price_cents !== null;
                              const installmentValue = ov.installments ?? variant.installments;
                              return (
                                <div
                                  key={variant.code}
                                  className="flex flex-col gap-3 rounded-lg border border-[var(--bd)] bg-[var(--surf2)] p-3 sm:flex-row sm:items-center"
                                >
                                  <div className="min-w-0 flex-1">
                                    <div
                                      className="text-sm font-medium"
                                      style={{ color: "var(--text)" }}
                                    >
                                      {variant.title}
                                    </div>
                                    <div
                                      className="mt-0.5 flex items-center gap-2 text-xs"
                                      style={{ color: "var(--text2)" }}
                                    >
                                      <span>
                                        Padrão: {centsToReaisLabel(variant.price_cents)} em{" "}
                                        {variant.installments}x
                                      </span>
                                      {hasOverride && (
                                        <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-400">
                                          override
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                  <div className="flex flex-wrap items-center gap-3">
                                    <CurrencyInput
                                      value={ov.price_cents}
                                      onChange={(cents) =>
                                        setVariantOverrides((prev) => ({
                                          ...prev,
                                          [product.code]: {
                                            ...(prev[product.code] ?? {}),
                                            [variant.code]: {
                                              ...ov,
                                              price_cents: cents,
                                              installments: installmentValue,
                                            },
                                          },
                                        }))
                                      }
                                      placeholder={centsToReaisLabel(variant.price_cents)}
                                      className="w-40"
                                      aria-label={`Preço override para ${variant.title}`}
                                    />
                                    <div className="flex items-center gap-2">
                                      <label className="text-xs" style={{ color: "var(--text3)" }}>
                                        Parcelas
                                      </label>
                                      <input
                                        type="number"
                                        min={1}
                                        value={installmentValue}
                                        onChange={(e) => {
                                          const v = e.target.value;
                                          const parsed = v === "" ? null : parseInt(v, 10);
                                          setVariantOverrides((prev) => ({
                                            ...prev,
                                            [product.code]: {
                                              ...(prev[product.code] ?? {}),
                                              [variant.code]: {
                                                ...ov,
                                                price_cents: ov.price_cents,
                                                installments: parsed,
                                              },
                                            },
                                          }));
                                        }}
                                        className="w-20 rounded-lg border border-[var(--bd)] bg-[var(--surf2)] px-2 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--accent)]"
                                        aria-label={`Parcelas para ${variant.title}`}
                                      />
                                    </div>
                                    {hasOverride && (
                                      <button
                                        type="button"
                                        onClick={() =>
                                          setVariantOverrides((prev) => {
                                            const next = { ...prev };
                                            if (next[product.code]) {
                                              const productVariants = { ...next[product.code] };
                                              delete productVariants[variant.code];
                                              if (Object.keys(productVariants).length === 0) {
                                                delete next[product.code];
                                              } else {
                                                next[product.code] = productVariants;
                                              }
                                            }
                                            return next;
                                          })
                                        }
                                        className="text-xs text-[var(--text3)] underline hover:text-[var(--text)]"
                                      >
                                        usar padrão
                                      </button>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                  </div>
                </Card>
              )}

              {/* Notes */}
              <Card title="Observações">
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  maxLength={500}
                  rows={3}
                  placeholder="Notas internas sobre a configuração de pricing..."
                  className="w-full resize-none rounded-lg border border-[var(--bd)] bg-[var(--surf2)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--accent)]"
                />
                <div
                  className="mt-1 text-right text-xs"
                  style={{ color: "var(--text3)" }}
                >
                  {notes.length}/500
                </div>
              </Card>

              {/* Save */}
              <div className="flex items-center justify-end gap-3">
                {hasChanges && (
                  <button
                    type="button"
                    onClick={handleReset}
                    disabled={isSaving}
                    className="flex items-center gap-2 rounded-lg border border-[var(--bd)] bg-[var(--surf)] px-4 py-2.5 text-sm font-medium text-[var(--text)] transition hover:border-[var(--accent)]/40 disabled:opacity-50"
                  >
                    <RotateCcw size={15} />
                    Descartar alterações
                  </button>
                )}
                <button
                  onClick={handleSave}
                  disabled={isSaving || !hasChanges}
                  className="flex items-center gap-2 rounded-lg px-6 py-2.5 text-sm font-medium text-white transition hover:opacity-90 disabled:opacity-50"
                  style={{ background: "var(--accent)" }}
                >
                  <Save size={16} />
                  {isSaving ? "Salvando..." : "Salvar Configuração"}
                </button>
              </div>
            </>
          )}
        </div>
      </AppLayout>
    </AuthGuard>
  );
}
