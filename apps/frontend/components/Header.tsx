"use client";

import { Bell, LogOut, Menu, Search, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ThemeToggle } from "@/components/ThemeToggle";
import { cn } from "@/lib/cn";
import { clearStoredSession } from "@/src/lib/authStorage";
import { useDevSession } from "@/src/lib/useDevSession";

type HeaderProps = { onMenuClick?: () => void };

const roleMeta: Record<string, { label: string; cls: string }> = {
  admin:   { label: "Administrador", cls: "cv-badge-blue" },
  analyst: { label: "Analista", cls: "cv-badge-teal" },
  client:  { label: "Cliente",  cls: "cv-badge-muted" },
  owner:   { label: "Proprietário", cls: "cv-badge-teal" },
  support: { label: "Suporte",  cls: "cv-badge-orange" }
};

export function Header({ onMenuClick }: HeaderProps) {
  const router        = useRouter();
  const session       = useDevSession();
  const [query, setQuery]           = useState("");
  const [searchOpen, setSearchOpen] = useState(false);

  function handleLogout() {
    clearStoredSession();
    router.replace("/login");
  }

  const meta = session ? (roleMeta[session.role] ?? roleMeta.client) : null;
  const initials = session
    ? session.email.slice(0, 2).toUpperCase()
    : "??";

  return (
    <header className="cv-header sticky top-0 z-30">
      <div className="flex h-16 items-center gap-3 px-4 md:px-6">

        {/* Hamburger — mobile only */}
        {onMenuClick && (
          <button
            aria-label="Abrir menu"
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-lg lg:hidden",
              "min-h-11 min-w-11 text-[var(--text2)] hover:bg-[var(--surf3)] hover:text-[var(--text)]",
              "transition-colors duration-fast"
            )}
            onClick={onMenuClick}
          >
            <Menu size={19} />
          </button>
        )}

        {/* Search — desktop always visible, mobile toggleable */}
        <div
          className={cn(
            "relative transition-all duration-base ease-smooth",
            searchOpen
              ? "flex-1"
              : "hidden w-56 flex-none md:flex md:w-64 lg:w-80"
          )}
        >
          <Search
            aria-hidden="true"
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text3)]"
            size={15}
          />
          <input
            autoFocus={searchOpen}
            className={cn(
              "cv-input min-h-11 w-full pl-9 pr-3 text-sm",
              "transition-all duration-base ease-smooth",
              "focus:shadow-glow-teal"
            )}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar casos, clientes..."
            type="search"
            value={query}
          />
          {searchOpen && (
            <button
              aria-label="Fechar busca"
              className="absolute right-2.5 top-1/2 flex h-8 min-h-8 w-8 min-w-8 -translate-y-1/2 items-center justify-center rounded-lg text-[var(--text3)] transition-colors duration-fast hover:bg-[var(--surf3)] hover:text-[var(--text)]"
              onClick={() => { setSearchOpen(false); setQuery(""); }}
            >
              <X size={14} />
            </button>
          )}
        </div>

        {/* Mobile search toggle */}
        {!searchOpen && (
          <button
            aria-label="Buscar"
            className="flex h-11 w-11 items-center justify-center rounded-lg text-[var(--text2)] transition-colors duration-fast hover:bg-[var(--surf3)] hover:text-[var(--text)] md:hidden"
            onClick={() => setSearchOpen(true)}
          >
            <Search size={18} />
          </button>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Right cluster */}
        <div className="flex items-center gap-1.5">
          <ThemeToggle className="hidden sm:flex" />

          {/* Notifications */}
          <button
            aria-label="Notificações"
            className={cn(
              "relative flex h-9 w-9 items-center justify-center rounded-lg",
              "min-h-11 min-w-11 text-[var(--text2)] hover:bg-[var(--surf3)] hover:text-[var(--text)]",
              "transition-colors duration-fast"
            )}
          >
            <Bell size={17} />
            <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-[var(--teal)] ring-2 ring-[var(--surf)]" />
          </button>

          {session ? (
            <div className="flex items-center gap-2 pl-1">
              {/* Role + name — sm+ */}
              <div className="hidden text-right sm:block">
                <p className="text-[12px] font-semibold leading-tight text-[var(--text)]">
                  {session.email.split("@")[0]}
                </p>
                {meta && (
                  <span
                    className={cn(
                      "cv-badge px-1.5 py-px text-[9px]",
                      meta.cls
                    )}
                  >
                    {meta.label}
                  </span>
                )}
              </div>

              {/* Avatar — acts as logout button */}
              <button
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full",
                  "bg-gradient-brand text-[11px] font-bold text-white",
                  "min-h-11 min-w-11 shadow-glow-teal ring-2 ring-[var(--surf)]",
                  "transition-all duration-base hover:shadow-glow-teal-lg hover:scale-105",
                  "active:scale-95"
                )}
                onClick={handleLogout}
                title="Sair da sessão"
              >
                {initials}
              </button>
              <button
                className={cn(
                  "hidden h-8 items-center gap-1.5 rounded-lg border border-slate-200 dark:border-slate-700",
                  "cv-btn-secondary min-h-11 px-2.5 text-[11px] font-semibold",
                  "md:flex"
                )}
                onClick={handleLogout}
                type="button"
              >
                <LogOut size={13} />
                Sair
              </button>
            </div>
          ) : (
            <a
              className={cn(
                "cv-btn cv-btn-secondary inline-flex min-h-11 items-center px-3",
                "text-[12px] font-semibold"
              )}
              href="/login"
            >
              Entrar
            </a>
          )}
        </div>
      </div>
    </header>
  );
}
