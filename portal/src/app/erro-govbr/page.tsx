"use client";

import React from "react";
import Link from "next/link";
import { AlertTriangle, ArrowRight, Home } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function GovbrErrorPage() {
  return (
    <div className="min-h-[calc(100vh-280px)] flex items-center justify-center py-12 px-4 bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center border border-amber-200 animate-fadeIn">
        <div className="w-16 h-16 bg-amber-100 text-amber-600 rounded-full flex items-center justify-center mx-auto mb-5">
          <AlertTriangle className="w-10 h-10" />
        </div>

        <h1 className="text-2xl font-bold text-gray-900 leading-snug">
          Não foi possível conectar com o Gov.br
        </h1>

        <p className="mt-3 text-sm text-gray-600 leading-relaxed">
          O serviço de autenticação com o provedor externo do Governo Federal não pôde ser
          concluído. Conforme a regra <strong>D10 / RF-02</strong> do MVP do SOSP, a integração
          completa com o Gov.br estará disponível na versão 2.0.
        </p>

        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-xl text-left">
          <span className="text-xs font-bold text-[#1351B4] uppercase tracking-wider block mb-1">
            Como acessar agora?
          </span>
          <p className="text-xs text-blue-900">
            Você pode acessar todos os serviços do SOSP utilizando o seu <strong>CPF e senha local</strong>.
          </p>
        </div>

        <div className="mt-8 flex flex-col gap-3">
          <Link href="/login" className="w-full">
            <Button variant="primary" className="w-full justify-center py-3 text-base">
              Entrar com CPF e Senha
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
          <Link href="/" className="w-full">
            <Button variant="secondary" className="w-full justify-center">
              <Home className="w-4 h-4 mr-2" />
              Voltar para a Página Inicial
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

