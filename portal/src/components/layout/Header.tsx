"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import clsx from "clsx";
import { User, LogOut, Menu, X } from "lucide-react";
import {
  AUTH_TOKEN_KEY,
  clearAuthSessionStorage,
  getStoredUserSession,
  MANAGER_ROLES,
  SERVER_ROLES,
  SESSION_CLEARED_EVENT,
  SESSION_UPDATED_EVENT,
} from "@/utils/session";

export const Header: React.FC = () => {
  const pathname = usePathname();
  const router = useRouter();
  const [userName, setUserName] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<string | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const syncUserFromStorage = () => {
      if (typeof window === "undefined") return;

      const token = localStorage.getItem(AUTH_TOKEN_KEY);
      const parsed = getStoredUserSession();
      if (!token || !parsed || pathname === "/sessao-expirada" || parsed.mustChangePassword) {
        setUserName(null);
        setUserRole(null);
        return;
      }

      setUserName(parsed.fullName ? parsed.fullName.split(" ")[0] : "Usuário");
      setUserRole(parsed.role || "citizen");
    };

    syncUserFromStorage();
    window.addEventListener(SESSION_CLEARED_EVENT, syncUserFromStorage);
    window.addEventListener(SESSION_UPDATED_EVENT, syncUserFromStorage);
    window.addEventListener("storage", syncUserFromStorage);

    return () => {
      window.removeEventListener(SESSION_CLEARED_EVENT, syncUserFromStorage);
      window.removeEventListener(SESSION_UPDATED_EVENT, syncUserFromStorage);
      window.removeEventListener("storage", syncUserFromStorage);
    };
  }, [pathname]);

  const handleLogout = () => {
    clearAuthSessionStorage();
    setUserName(null);
    setUserRole(null);
    router.push("/");
  };

  const navLinks = [
    { href: "/servicos", label: "Serviços" },
    { href: "/cidadao/meus-agendamentos", label: "Meus Agendamentos" },
    { href: "/ajuda", label: "Ajuda" },
    { href: "/faq", label: "FAQ" },
  ];

  return (
    <header className="bg-white border-b border-[#CBD2DC] sticky top-0 z-40">
      <div className="max-w-[1200px] mx-auto px-4 h-20 flex items-center justify-between">
        {/* Logomarca SOSP com identidade oficial */}
        <Link href="/" className="flex items-center gap-3 group" aria-label="SOSP — Página Inicial">
          <div className="w-11 h-11 rounded-lg bg-[#1351B4] flex items-center justify-center text-white shadow-xs group-hover:bg-[#0C326F] transition-colors">
            {/* Ícone Bússola/Orientação */}
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="10" strokeWidth="2" />
              <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="currentColor" stroke="none" />
            </svg>
          </div>
          <div>
            <span className="text-xl font-extrabold text-[#1351B4] tracking-tight block leading-tight">
              SOSP
            </span>
            <span className="text-xs text-[#4A5568] font-medium block">
              Sistema de Orientação para Serviços Públicos
            </span>
          </div>
        </Link>

        {/* Menu Desktop */}
        <nav aria-label="Navegação Principal" className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => {
            const isActive = pathname === link.href || (link.href !== "/" && pathname.startsWith(link.href));
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
        <div className="hidden md:flex items-center gap-3">
          {userName ? (
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-gray-700 flex items-center gap-1.5 bg-gray-100 px-3 py-1.5 rounded-full">
                <User className="w-4 h-4 text-[#1351B4]" />
                Olá, {userName}
              </span>
              {userRole && (SERVER_ROLES as readonly string[]).includes(userRole) && (
                <Link
                  href="/servidor/painel"
                  className="text-xs font-bold bg-amber-100 text-amber-800 px-2.5 py-1 rounded hover:bg-amber-200 transition-colors"
                >
                  Painel Servidor
                </Link>
              )}
              {userRole && (MANAGER_ROLES as readonly string[]).includes(userRole) && (
                <Link
                  href="/admin/orgaos"
                  className="text-xs font-bold bg-indigo-100 text-indigo-800 px-2.5 py-1 rounded hover:bg-indigo-200 transition-colors"
                >
                  Painel Gestor
                </Link>
              )}
              <button
                type="button"
                onClick={handleLogout}
                className="text-xs font-semibold text-red-600 hover:text-red-800 flex items-center gap-1 p-1.5 rounded hover:bg-red-50 transition-colors"
                title="Sair da conta"
                aria-label="Sair da conta"
              >
                <LogOut className="w-4 h-4" />
                Sair
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="inline-flex items-center justify-center font-bold text-sm bg-[#1351B4] text-white hover:bg-[#0C326F] px-5 py-2.5 rounded-md min-h-[44px] transition-colors"
              >
                Entrar
              </Link>
            </div>
          )}
        </div>

        {/* Botão Menu Mobile */}
        <div className="flex md:hidden items-center">
          <button
            type="button"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 text-gray-600 hover:text-gray-900 focus:outline-none"
            aria-label={isMobileMenuOpen ? "Fechar menu" : "Abrir menu"}
            aria-expanded={isMobileMenuOpen}
          >
            {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Navegação Mobile Colapsável */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white px-4 py-4 space-y-3">
          <nav aria-label="Navegação Mobile" className="flex flex-col space-y-2">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setIsMobileMenuOpen(false)}
                className="text-sm font-semibold text-gray-700 hover:text-[#1351B4] py-2 px-1 border-b border-gray-100"
              >
                {link.label}
              </Link>
            ))}
          </nav>
          <div className="pt-2 border-t border-gray-100">
            {userName ? (
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-700">Olá, {userName}</span>
                <button
                  type="button"
                  onClick={() => {
                    handleLogout();
                    setIsMobileMenuOpen(false);
                  }}
                  className="text-xs font-semibold text-red-600 hover:underline flex items-center gap-1"
                >
                  <LogOut className="w-4 h-4" />
                  Sair
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                onClick={() => setIsMobileMenuOpen(false)}
                className="block text-center font-bold text-sm bg-[#1351B4] text-white py-2.5 rounded-md"
              >
                Entrar
              </Link>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
