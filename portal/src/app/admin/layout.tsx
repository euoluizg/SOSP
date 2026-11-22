"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getStoredUserSession,
  isInstitutionalRole,
  SERVER_ROLES,
  MANAGER_ROLES,
} from "@/utils/session";
import { ShieldAlert } from "lucide-react";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [isAuthorized, setIsAuthorized] = useState<boolean | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const session = getStoredUserSession();

    // Se não houver sessão ou não for papel institucional, redireciona para login institucional
    if (!session || !isInstitutionalRole(session.role)) {
      setIsAuthorized(false);
      router.replace("/login/institucional");
      return;
    }

    // Servidor operacional (server / servant) NÃO tem acesso à gestão geral (apenas ao painel designado)
    const role = session.role || "";
    if ((SERVER_ROLES as readonly string[]).includes(role)) {
      setIsAuthorized(false);
      router.replace("/servidor/painel");
      return;
    }

    // Apenas gestores e administradores (MANAGER_ROLES) têm acesso à gestão geral
    if ((MANAGER_ROLES as readonly string[]).includes(role)) {
      setIsAuthorized(true);
    } else {
      setIsAuthorized(false);
      router.replace("/servidor/painel");
    }
  }, [router]);

  if (isAuthorized === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-300 border-t-[#1351B4] mb-3"></div>
          <p className="text-xs font-semibold text-gray-500">
            Verificando permissões de gestão...
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthorized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4">
        <div className="max-w-md w-full bg-white p-6 rounded-2xl shadow-sm border border-red-200 text-center">
          <div className="w-12 h-12 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-3">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-gray-900">Acesso Restrito</h2>
          <p className="text-xs text-gray-600 mt-2">
            Servidores operacionais não têm acesso à gestão geral, apenas ao painel operacional que lhes foi designado. Redirecionando...
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

