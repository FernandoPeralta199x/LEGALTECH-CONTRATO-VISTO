"use client";

import { useState } from "react";
import type { ReactNode } from "react";

import { Header } from "@/components/Header";
import { MobileSidebar, Sidebar } from "@/components/Sidebar";

type AppLayoutProps = {
  children: ReactNode;
};

export function AppLayout({ children }: AppLayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="cv-app-shell min-h-screen overflow-x-hidden">
      <div className="flex">
        <Sidebar />
        <MobileSidebar onClose={() => setMobileOpen(false)} open={mobileOpen} />

        <div className="min-w-0 flex-1">
          <Header onMenuClick={() => setMobileOpen(true)} />
          <main className="mx-auto w-full max-w-7xl px-4 py-5 sm:px-6 sm:py-7">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
