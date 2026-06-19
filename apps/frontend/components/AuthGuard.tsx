"use client";

import { LockKeyhole } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect } from "react";

import { Button } from "@/components/Button";
import { useDevSessionState } from "@/src/lib/useDevSession";

type AuthGuardProps = {
  children: ReactNode;
};

export function AuthGuard({ children }: AuthGuardProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { session, status } = useDevSessionState();

  useEffect(() => {
    if (status === "invalid" || status === "unauthenticated") {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [pathname, router, status]);

  if (status === "loading") {
    return (
      <main className="cv-app-shell flex min-h-screen items-center justify-center px-4 py-10">
        <section className="cv-card w-full max-w-md p-8 text-center" aria-live="polite">
          <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg border border-[rgba(32,201,151,0.22)] bg-[var(--teal-dim)] text-[var(--teal)]">
            <LockKeyhole aria-hidden="true" size={22} />
          </span>
          <h1 className="mt-5 text-xl font-semibold text-[var(--text)]">
            Verificando acesso local
          </h1>
          <p className="mt-2 text-sm leading-6 text-[var(--text2)]">
            Confirmando a sessão dev salva neste navegador.
          </p>
        </section>
      </main>
    );
  }

  if (session) {
    return children;
  }

  return (
    <main className="cv-app-shell flex min-h-screen items-center justify-center px-4 py-10">
      <section className="cv-card w-full max-w-md p-8 text-center">
        <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg border border-[rgba(32,201,151,0.22)] bg-[var(--teal-dim)] text-[var(--teal)]">
          <LockKeyhole aria-hidden="true" size={22} />
        </span>
        <h1 className="mt-5 text-xl font-semibold text-[var(--text)]">
          Acesso restrito
        </h1>
        <p className="mt-2 text-sm leading-6 text-[var(--text2)]">
          Cole um JWT dev válido no login local para acessar esta página.
        </p>
        <Button className="mt-6" href="/login">
          Ir para login
        </Button>
      </section>
    </main>
  );
}
