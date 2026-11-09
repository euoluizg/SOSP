"use client";

import React, { Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Clock, LogIn, Home } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { sanitizeRedirectUrl } from "@/utils/validations";

function SessionExpiredContent() {
  const searchParams = useSearchParams();
  const redirectParam = searchParams.get("redirect");
  const safeRedirect = sanitizeRedirectUrl(redirectParam);

  const loginUrl = safeRedirect
    ? `/login?redirect=${encodeURIComponent(safeRedirect)}`
    : "/login";

  return (
    <div className="min-h-[calc(100vh-280px)] flex items-center justify-center py-12 px-4 bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center border border-gray-200 animate-fadeIn">
        <div className="w-16 h-16 bg-amber-100 text-amber-600 rounded-full flex items-center justify-center mx-auto mb-5">
          <Clock className="w-10 h-10" />
        </div>

        <h1 className="text-2xl font-bold text-gray-900 leading-snug">
          Sua Sessão Expirou
        </h1>

        <p className="mt-3 text-sm text-gray-600 leading-relaxed">
          Por motivos de segurança e proteção dos seus dados pessoais (Regra <strong>RN-28</strong>),
          sua conexão foi encerrada após 30 minutos de inatividade.
        </p>

        <div className="mt-8 flex flex-col gap-3">
          <Link href={loginUrl} className="w-full">
            <Button variant="primary" className="w-full justify-center py-3 text-base">
              <LogIn className="w-4 h-4 mr-2" />
              Fazer Login Novamente
            </Button>
          </Link>
          <Link href="/" className="w-full">
            <Button variant="secondary" className="w-full justify-center">
              <Home className="w-4 h-4 mr-2" />
              Voltar para o Início
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function SessionExpiredPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[calc(100vh-280px)] flex items-center justify-center py-12 px-4 bg-gray-50">
          <p className="text-gray-500 text-sm">Carregando...</p>
        </div>
      }
    >
      <SessionExpiredContent />
    </Suspense>
  );
}

