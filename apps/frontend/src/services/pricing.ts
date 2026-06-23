/**
 * Pricing API service — frontend-backend contract for pricing catalog,
 * admin config, and server-side estimates.
 *
 * NO mock fallback — prices come exclusively from the backend.
 * Aligns with 28P-B gate: sem fallback R$0,00, sem mock/fake/seed.
 */

import { apiClient } from "@/src/services/apiClient";

// ---------------------------------------------------------------------------
// Types — mirror backend Pydantic schemas
// ---------------------------------------------------------------------------

export interface PricingProduct {
  code: string;
  title: string;
  description: string;
  includes: string[];
  base_price_cents: number;
  sla_hours: number;
  variants?: PricingProductVariant[];
}

export interface PricingProductVariant {
  code: string;
  title: string;
  price_cents: number;
  installments: number;
}

export interface PricingModule {
  code: string;
  title: string;
  description: string;
  price_cents: number;
}

export interface ModuleMatrixConfig {
  default: boolean;
  recommended: boolean;
  required: boolean;
  locked: boolean;
}

export interface PricingSlaRules {
  human_review_extra_hours: number;
  meeting_product_extra_hours: number;
  human_review_module: string;
  meeting_product: string;
}

export interface PricingCatalog {
  currency: string;
  version: string;
  products: PricingProduct[];
  modules: PricingModule[];
  matrix: Record<string, Record<string, ModuleMatrixConfig>>;
  sla_rules: PricingSlaRules;
}

export interface PricingLineItem {
  code: string;
  title: string;
  price_cents: number;
}

export interface PricingEstimate {
  product: string;
  variant: PricingProductVariantLineItem | null;
  currency: string;
  base_price_cents: number;
  modules: PricingLineItem[];
  modules_total_cents: number;
  variant_price_cents: number;
  total_price_cents: number;
  sla_hours: number;
}

export interface PricingProductVariantLineItem {
  code: string;
  title: string;
  price_cents: number;
  installments: number;
  installment_cents: number;
}

export interface ProductOverride {
  base_price_cents: number;
}

export interface ProductVariantOverride {
  price_cents: number;
  installments: number;
}

export interface ModuleOverride {
  price_cents: number;
}

export interface PricingConfig {
  organization_id: string;
  cases_limit: number | null;
  product_overrides: Record<string, ProductOverride>;
  product_variant_overrides: Record<string, Record<string, ProductVariantOverride>>;
  module_overrides: Record<string, ModuleOverride>;
  version: number;
  notes: string | null;
  updated_by: string | null;
  updated_at: string;
}

export interface UpdatePricingConfigPayload {
  cases_limit?: number | null;
  product_overrides?: Record<string, ProductOverride> | null;
  product_variant_overrides?: Record<string, Record<string, ProductVariantOverride>> | null;
  module_overrides?: Record<string, ModuleOverride> | null;
  notes?: string | null;
}

export interface CasesLimitCheck {
  cases_limit: number | null;
  active_cases_count: number;
  allowed: boolean;
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

export async function getPricingCatalog(): Promise<PricingCatalog> {
  const res = await apiClient.get<PricingCatalog>("/api/v1/pricing");
  return res.data;
}

export async function estimatePricing(
  product: string,
  modules: string[],
  variant?: string | null
): Promise<PricingEstimate> {
  const res = await apiClient.post<PricingEstimate>(
    "/api/v1/pricing/estimate",
    { product, modules, variant }
  );
  return res.data;
}

export async function getPricingConfig(): Promise<PricingConfig> {
  const res = await apiClient.get<PricingConfig>("/api/v1/pricing/config");
  return res.data;
}

export async function updatePricingConfig(
  payload: UpdatePricingConfigPayload
): Promise<PricingConfig> {
  const res = await apiClient.put<PricingConfig>(
    "/api/v1/pricing/config",
    payload
  );
  return res.data;
}

export async function checkCasesLimit(): Promise<CasesLimitCheck> {
  const res = await apiClient.get<CasesLimitCheck>(
    "/api/v1/pricing/config/limit-check"
  );
  return res.data;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
