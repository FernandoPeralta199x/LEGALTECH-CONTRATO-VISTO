"use client";

import { Button } from "@/components/Button";

export default function GlobalError({
  error,
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html className="dark" data-theme="dark" lang="pt-BR">
      <body>
        <main
          className="flex min-h-screen flex-col items-center justify-center p-6 text-center"
          style={{ background: "var(--bg)", color: "var(--text)" }}
        >
          <div className="mx-auto max-w-md space-y-4 rounded-xl border p-6 shadow-lg" style={{ borderColor: "var(--bd)", background: "var(--surf1)" }}>
            <h1 className="text-lg font-semibold" style={{ color: "var(--text)" }}>
              Algo deu errado
            </h1>
            <p className="text-sm" style={{ color: "var(--text2)" }}>
              Ocorreu um erro inesperado na aplicação. Tente novamente ou volte para o início.
            </p>
            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-center">
              <Button href="/" variant="secondary">
                Voltar ao início
              </Button>
              <Button onClick={() => reset()} variant="primary">
                Tentar novamente
              </Button>
            </div>
            {process.env.NODE_ENV !== "production" && error.message && (
              <pre className="mt-4 rounded p-3 text-left text-xs" style={{ background: "var(--surf2)", color: "var(--text2)" }}>
                {error.message}
                {error.digest ? `\nDigest: ${error.digest}` : ""}
              </pre>
            )}
          </div>
        </main>
      </body>
    </html>
  );
}
