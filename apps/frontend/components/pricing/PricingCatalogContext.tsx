"use client";

import { useEffect, useState, useMemo, createContext, useContext } from "react";

import { MATRIZ } from "@/lib/produtoConfig";
import { errorMessage } from "@/src/lib/errorMessage";
import {
  getPricingCatalog,
  type PricingCatalog,
  type PricingModule,
  type PricingProduct,
} from "@/src/services/pricing";

type PricingCatalogContextValue = {
  catalog: PricingCatalog | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
};

const PricingCatalogContext = createContext<PricingCatalogContextValue | null>(
  null
);

export function PricingCatalogProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [catalog, setCatalog] = useState<PricingCatalog | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getPricingCatalog();
      setCatalog(data);
    } catch (err) {
      setError(errorMessage(err, "Erro ao carregar catálogo de preços."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refetch();
  }, []);

  return (
    <PricingCatalogContext.Provider
      value={{ catalog, isLoading, error, refetch }}
    >
      {children}
    </PricingCatalogContext.Provider>
  );
}

export function usePricingCatalog() {
  const ctx = useContext(PricingCatalogContext);
  if (!ctx) {
    throw new Error(
      "usePricingCatalog must be used within PricingCatalogProvider"
    );
  }
  return ctx;
}

export function useProductPrice(productCode: string): number | null {
  const { catalog } = usePricingCatalog();
  return useMemo(() => {
    if (!catalog) return null;
    return (
      catalog.products.find((p: PricingProduct) => p.code === productCode)
        ?.base_price_cents ?? null
    );
  }, [catalog, productCode]);
}

export function useModulePrice(moduleCode: string): number | null {
  const { catalog } = usePricingCatalog();
  return useMemo(() => {
    if (!catalog) return null;
    return (
      catalog.modules.find((m: PricingModule) => m.code === moduleCode)
        ?.price_cents ?? null
    );
  }, [catalog, moduleCode]);
}

export function usePricingLookup() {
  const { catalog } = usePricingCatalog();
  return useMemo(() => {
    const products = new Map<string, PricingProduct>();
    const modules = new Map<string, PricingModule>();
    catalog?.products.forEach((p) => products.set(p.code, p));
    catalog?.modules.forEach((m) => modules.set(m.code, m));
    return { products, modules };
  }, [catalog]);
}

/**
 * Returns the effective product/module matrix, preferring the backend catalog
 * and falling back to the local MATRIX when offline.
 */
export function usePricingMatrix(): Record<string, Record<string, { required?: boolean; obrigatorio?: boolean }>> {
  const { catalog } = usePricingCatalog();
  return useMemo(() => {
    if (catalog?.matrix) return catalog.matrix as Record<string, Record<string, { required?: boolean }>>;
    return MATRIZ as unknown as Record<string, Record<string, { obrigatorio?: boolean }>>;
  }, [catalog]);
}

/** Returns whether a module is required/locked for a given product. */
export function useModuleRequired(
  productCode: string,
  moduleCode: string
): boolean {
  const matrix = usePricingMatrix();
  return useMemo(() => {
    const config = matrix[productCode]?.[moduleCode];
    return config?.required === true || config?.obrigatorio === true;
  }, [matrix, productCode, moduleCode]);
}
