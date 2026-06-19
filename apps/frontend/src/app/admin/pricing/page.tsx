"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  DollarSign,
  Save,
  AlertTriangle,
  CheckCircle,
  Settings,
  Package,
  Layers,
  Shield,
} from "lucide-react";

import { AuthGuard } from "@/components/AuthGuard";
import { AppLayout } from "@/components/AppLayout";
import { PageTitle } from "@/components/PageTitle";
import { Card } from "@/components/Card";

import {
  getPricingCatalog,
  getPricingConfig,
  updatePricingConfig,
  checkCasesLimit,
  formatCents,
  type PricingCatalog,
  type PricingConfig,
  type CasesLimitCheck,
  type UpdatePricingConfigPayload,
} from "@/src/services/pricing";
import { errorMessage } from "@/src/lib/errorMessage";

type Status = "idle" | "loading" | "saving" | "success" | "error";

export default function AdminPricingPage() {
  const router = useRouter();

  const [catalog, setCatalog] = useState<PricingCatalog | null>(null);
  const [config, setConfig] = useState<PricingConfig | null>(null);
  const [limitCheck, setLimitCheck] = useState<CasesLimitCheck | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form state
  const [casesLimit, setCasesLimit] = useState<string>("");
  const [unlimitedCases, setUnlimitedCases] = useState(true);
  const [productOverrides, setProductOverrides] = useState<
    Record<string, string>
  >({});
  const [moduleOverrides, setModuleOverrides] = useState<
    Record<string, string>
  >({});
  const [notes, setNotes] = useState("");

  const loadData = useCallback(async () => {
    setStatus("loading");
    setError(null);
    try {
      const [cat, cfg, lim] = await Promise.all([
        getPricingCatalog(),
        getPricingConfig(),
        checkCasesLimit(),
      ]);
      setCatalog(cat);
      setConfig(cfg);
      setLimitCheck(lim);

      // Initialize form state from config
      if (cfg.cases_limit === null) {
        setUnlimitedCases(true);
        setCasesLimit("");
      } else {
        setUnlimitedCases(false);
        setCasesLimit(String(cfg.cases_limit));
      }
      setProductOverrides(
        Object.fromEntries(
          Object.entries(cfg.product_overrides).map(([k, v]) => [
            k,
            String(v.base_price_cents),
          ])
        )
      );
      setModuleOverrides(
        Object.fromEntries(
          Object.entries(cfg.module_overrides).map(([k, v]) => [
            k,
            String(v.price_cents),
          ])
        )
      );
      setNotes(cfg.notes ?? "");
      setStatus("idle");
    } catch (err) {
      setError(errorMessage(err, "Erro ao carregar pricing."));
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSave = async () => {
    setStatus("saving");
    setError(null);
    setSuccessMsg(null);
    try {
      const payload: UpdatePricingConfigPayload = {};

      // cases_limit
      payload.cases_limit = unlimitedCases
        ? null
        : parseInt(casesLimit, 10) || null;

      // product overrides (only changed ones)
      const prodOv: Record<string, { base_price_cents: number }> = {};
      for (const [code, val] of Object.entries(productOverrides)) {
        const cents = parseInt(val, 10);
        if (!isNaN(cents) && cents >= 0) {
          prodOv[code] = { base_price_cents: cents };
        }
      }
      if (Object.keys(prodOv).length > 0) {
        payload.product_overrides = prodOv;
      }

      // module overrides (only changed ones)
      const modOv: Record<string, { price_cents: number }> = {};
      for (const [code, val] of Object.entries(moduleOverrides)) {
        const cents = parseInt(val, 10);
        if (!isNaN(cents) && cents >= 0) {
          modOv[code] = { price_cents: cents };
        }
      }
      if (Object.keys(modOv).length > 0) {
        payload.module_overrides = modOv;
      }

      if (notes.trim()) {
        payload.notes = notes.trim();
      }

      const updated = await updatePricingConfig(payload);
      setConfig(updated);
      setSuccessMsg(
        `Configuração salva (versão ${updated.version}).`
      );
      setStatus("success");

      // Refresh limit check
      const lim = await checkCasesLimit();
      setLimitCheck(lim);
    } catch (err) {
      setError(errorMessage(err, "Erro ao salvar."));
      setStatus("error");
    }
  };

  const isLoading = status === "loading";
  const isSaving = status === "saving";

  return (
    <AuthGuard>
      <AppLayout>
        <div className="max-w-5xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/admin")}
              className="p-2 rounded-lg hover:opacity-80 transition-opacity"
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

          {/* Feedback messages */}
          {error && (
            <div
              className="flex items-center gap-2 p-3 rounded-lg text-sm"
              style={{
                background: "rgba(239, 68, 68, 0.1)",
                color: "#ef4444",
                border: "1px solid rgba(239, 68, 68, 0.2)",
              }}
            >
              <AlertTriangle size={16} />
              {error}
            </div>
          )}
          {successMsg && (
            <div
              className="flex items-center gap-2 p-3 rounded-lg text-sm"
              style={{
                background: "rgba(34, 197, 94, 0.1)",
                color: "#22c55e",
                border: "1px solid rgba(34, 197, 94, 0.2)",
              }}
            >
              <CheckCircle size={16} />
              {successMsg}
            </div>
          )}

          {isLoading ? (
            <div
              className="text-center py-12 text-sm"
              style={{ color: "var(--text2)" }}
            >
              Carregando...
            </div>
          ) : (
            <>
              {/* Cases Limit + Status */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card>
                  <div className="flex items-center gap-2 mb-4">
                    <Shield size={18} style={{ color: "var(--accent)" }} />
                    <h3
                      className="font-semibold"
                      style={{ color: "var(--text)" }}
                    >
                      Limite de Casos
                    </h3>
                  </div>
                  <div className="space-y-3">
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={unlimitedCases}
                        onChange={(e) => setUnlimitedCases(e.target.checked)}
                        className="rounded"
                      />
                      <span style={{ color: "var(--text2)" }}>
                        Ilimitado (sem restrição)
                      </span>
                    </label>
                    {!unlimitedCases && (
                      <input
                        type="number"
                        min={1}
                        value={casesLimit}
                        onChange={(e) => setCasesLimit(e.target.value)}
                        placeholder="Ex: 100"
                        className="w-full px-3 py-2 rounded-lg text-sm"
                        style={{
                          background: "var(--surf2)",
                          border: "1px solid var(--bd)",
                          color: "var(--text)",
                        }}
                      />
                    )}
                  </div>
                </Card>

                <Card>
                  <div className="flex items-center gap-2 mb-4">
                    <Settings size={18} style={{ color: "var(--accent)" }} />
                    <h3
                      className="font-semibold"
                      style={{ color: "var(--text)" }}
                    >
                      Status Atual
                    </h3>
                  </div>
                  <div className="space-y-2 text-sm">
                    {limitCheck && (
                      <>
                        <div className="flex justify-between">
                          <span style={{ color: "var(--text2)" }}>
                            Casos ativos
                          </span>
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
                          <span style={{ color: "var(--text2)" }}>
                            Pode criar
                          </span>
                          <span
                            style={{
                              color: limitCheck.allowed
                                ? "#22c55e"
                                : "#ef4444",
                            }}
                          >
                            {limitCheck.allowed ? "Sim" : "Não"}
                          </span>
                        </div>
                      </>
                    )}
                    {config && (
                      <div
                        className="flex justify-between pt-2 mt-2"
                        style={{ borderTop: "1px solid var(--bd)" }}
                      >
                        <span style={{ color: "var(--text2)" }}>Versão</span>
                        <span style={{ color: "var(--text)" }}>
                          {config.version}
                        </span>
                      </div>
                    )}
                  </div>
                </Card>
              </div>

              {/* Product Overrides */}
              {catalog && (
                <Card>
                  <div className="flex items-center gap-2 mb-4">
                    <Package size={18} style={{ color: "var(--accent)" }} />
                    <h3
                      className="font-semibold"
                      style={{ color: "var(--text)" }}
                    >
                      Preços de Produtos
                    </h3>
                    <span
                      className="text-xs px-2 py-0.5 rounded-full"
                      style={{
                        background: "var(--surf2)",
                        color: "var(--text2)",
                      }}
                    >
                      Deixe vazio para usar o padrão
                    </span>
                  </div>
                  <div className="space-y-3">
                    {catalog.products.map((product) => {
                      const hasOverride =
                        productOverrides[product.code] !== undefined &&
                        productOverrides[product.code] !== "";
                      return (
                        <div
                          key={product.code}
                          className="flex items-center gap-4 p-3 rounded-lg"
                          style={{
                            background: "var(--surf2)",
                            border: "1px solid var(--bd)",
                          }}
                        >
                          <div className="flex-1 min-w-0">
                            <div
                              className="font-medium text-sm"
                              style={{ color: "var(--text)" }}
                            >
                              {product.title}
                            </div>
                            <div
                              className="text-xs"
                              style={{ color: "var(--text2)" }}
                            >
                              Padrão: {formatCents(product.base_price_cents)}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <DollarSign
                              size={14}
                              style={{ color: "var(--text3)" }}
                            />
                            <input
                              type="number"
                              min={0}
                              value={productOverrides[product.code] ?? ""}
                              onChange={(e) =>
                                setProductOverrides((prev) => ({
                                  ...prev,
                                  [product.code]: e.target.value,
                                }))
                              }
                              placeholder={String(product.base_price_cents)}
                              className="w-32 px-2 py-1 rounded text-sm text-right"
                              style={{
                                background: "var(--surf3)",
                                border: "1px solid var(--bd)",
                                color: "var(--text)",
                              }}
                            />
                            <span
                              className="text-xs w-6"
                              style={{
                                color: hasOverride ? "#f59e0b" : "var(--text3)",
                              }}
                            >
                              {hasOverride ? "¢" : ""}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              )}

              {/* Module Overrides */}
              {catalog && (
                <Card>
                  <div className="flex items-center gap-2 mb-4">
                    <Layers size={18} style={{ color: "var(--accent)" }} />
                    <h3
                      className="font-semibold"
                      style={{ color: "var(--text)" }}
                    >
                      Preços de Módulos
                    </h3>
                    <span
                      className="text-xs px-2 py-0.5 rounded-full"
                      style={{
                        background: "var(--surf2)",
                        color: "var(--text2)",
                      }}
                    >
                      Deixe vazio para usar o padrão
                    </span>
                  </div>
                  <div className="space-y-3">
                    {catalog.modules.map((mod) => {
                      const hasOverride =
                        moduleOverrides[mod.code] !== undefined &&
                        moduleOverrides[mod.code] !== "";
                      return (
                        <div
                          key={mod.code}
                          className="flex items-center gap-4 p-3 rounded-lg"
                          style={{
                            background: "var(--surf2)",
                            border: "1px solid var(--bd)",
                          }}
                        >
                          <div className="flex-1 min-w-0">
                            <div
                              className="font-medium text-sm"
                              style={{ color: "var(--text)" }}
                            >
                              {mod.title}
                            </div>
                            <div
                              className="text-xs"
                              style={{ color: "var(--text2)" }}
                            >
                              Padrão: {formatCents(mod.price_cents)}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <DollarSign
                              size={14}
                              style={{ color: "var(--text3)" }}
                            />
                            <input
                              type="number"
                              min={0}
                              value={moduleOverrides[mod.code] ?? ""}
                              onChange={(e) =>
                                setModuleOverrides((prev) => ({
                                  ...prev,
                                  [mod.code]: e.target.value,
                                }))
                              }
                              placeholder={String(mod.price_cents)}
                              className="w-32 px-2 py-1 rounded text-sm text-right"
                              style={{
                                background: "var(--surf3)",
                                border: "1px solid var(--bd)",
                                color: "var(--text)",
                              }}
                            />
                            <span
                              className="text-xs w-6"
                              style={{
                                color: hasOverride ? "#f59e0b" : "var(--text3)",
                              }}
                            >
                              {hasOverride ? "¢" : ""}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              )}

              {/* Notes */}
              <Card>
                <h3
                  className="font-semibold mb-3"
                  style={{ color: "var(--text)" }}
                >
                  Observações
                </h3>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  maxLength={500}
                  rows={3}
                  placeholder="Notas internas sobre a configuração de pricing..."
                  className="w-full px-3 py-2 rounded-lg text-sm resize-none"
                  style={{
                    background: "var(--surf2)",
                    border: "1px solid var(--bd)",
                    color: "var(--text)",
                  }}
                />
                <div
                  className="text-xs mt-1 text-right"
                  style={{ color: "var(--text3)" }}
                >
                  {notes.length}/500
                </div>
              </Card>

              {/* Save */}
              <div className="flex justify-end">
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="flex items-center gap-2 px-6 py-2.5 rounded-lg font-medium text-sm transition-opacity hover:opacity-90 disabled:opacity-50"
                  style={{
                    background: "var(--accent)",
                    color: "#fff",
                  }}
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
