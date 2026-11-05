"use client";

import React from "react";
import Link from "next/link";
import { FileText, ArrowLeft } from "lucide-react";

export default function TermsOfUsePage() {
  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[850px] mx-auto bg-white rounded-2xl p-6 sm:p-10 shadow-sm border border-gray-200">
        <Link href="/" className="inline-flex items-center text-xs font-semibold text-[#1351B4] hover:underline mb-6">
          <ArrowLeft className="w-3.5 h-3.5 mr-1" />
          Voltar para a página inicial
        </Link>

        <div className="flex items-center gap-4 pb-6 border-b border-gray-100 mb-8">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-[#1351B4] flex items-center justify-center">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-[#1351B4]">
              Condições Oficiais de Serviço
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 mt-0.5">
              Termos e Condições de Uso
            </h1>
          </div>
        </div>

        <div className="prose prose-sm max-w-none text-gray-700 space-y-5 text-sm leading-relaxed">
          <p>
            Ao utilizar o <strong>SOSP (Sistema de Orientação para Serviços Públicos)</strong>, você concorda
            com os presentes Termos de Uso e com as normas de conduta da administração pública digital.
          </p>

          <h2 className="text-lg font-bold text-gray-900 pt-2">1. Responsabilidade sobre as Informações</h2>
          <p>
            O cidadão declara sob as penas da lei que todas as informações prestadas durante o cadastro e o
            agendamento são verdadeiras e correspondem à sua identidade real. O uso indevido de dados de terceiros
            constitui crime de falsidade ideológica (Art. 299 do Código Penal).
          </p>

          <h2 className="text-lg font-bold text-gray-900 pt-2">2. Regras de Agendamento e Cancelamento</h2>
          <p>
            Cada cidadão pode manter apenas um agendamento ativo por serviço (regra RN-21). Caso não possa comparecer
            ao atendimento na data e horário marcados, o cancelamento voluntário deve ser realizado com no mínimo
            <strong>24 horas de antecedência</strong> através do portal (regra RN-22), de modo a permitir que outros
            cidadãos usufruam da vaga.
          </p>

          <h2 className="text-lg font-bold text-gray-900 pt-2">3. Disponibilidade do Serviço</h2>
          <p>
            O Governo do Estado empenha-se em manter a plataforma operacional 24 horas por dia, 7 dias por semana,
            ressalvadas paradas programadas para manutenção corretiva ou preventiva e atualizações de segurança.
          </p>
        </div>
      </div>
    </div>
  );
}

