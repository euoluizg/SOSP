"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

export const Header: React.FC = () => {
  const pathname = usePathname();

  const navLinks = [
    { href: "/servicos", label: "Serviços" },
    { href: "/cidadao/meus-agendamentos", label: "Meus Agendamentos" },
    { href: "/faq", label: "Ajuda & FAQ" },
  ];

  return (
    <header className="bg-white border-b border-[#CBD2DC] sticky top-0 z-40">
      <div className="max-w-[1200px] mx-auto px-4 h-20 flex items-center justify-between">
        {/* Logomarca SOSP */}
        <Link href="/" className="flex items-center gap-3 group" aria-label="SOSP — Página Inicial">
          <div className="w-11 h-11 rounded-lg bg-[#1351B4] flex items-center justify-center text-white shadow-xs group-hover:bg-[#0C326F] transition-colors">
            {/* Ícone Bússola/Orientação */}
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="10" strokeWidth="2" />
              <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="currentColor" stroke="none" />
            </svg>
          </div>
          <div>
            <span className="text-xl font-extrabold text-[#1351B4] tracking-tight block leading-tight">SOSP</span>
            <span className="text-xs text-[#4A5568] block">Serviços públicos</span>
          </div>
        </Link>

        {/* Menu Desktop */}
        <nav aria-label="Navegação Principal" className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => {
            const isActive = pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={clsx(
                  "text-sm font-semibold transition-colors hover:text-[#1351B4] py-2 border-b-2",
                  isActive
                    ? "text-[#1351B4] border-[#1351B4]"
                    : "text-[#4A5568] border-transparent"
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Ações de Usuário */}
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="inline-flex items-center justify-center font-bold text-sm bg-[#1351B4] text-white hover:bg-[#0C326F] px-5 py-2.5 rounded-md min-h-[44px] transition-colors"
          >
            Entrar
          </Link>
        </div>
      </div>
    </header>
  );
};

