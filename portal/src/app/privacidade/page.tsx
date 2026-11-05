"use client";

import React from "react";
import Link from "next/link";
import { ShieldCheck, ArrowLeft } from "lucide-react";

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[850px] mx-auto bg-white rounded-2xl p-6 sm:p-10 shadow-sm border border-gray-200">
        <Link href="/" className="inline-flex items-center text-xs font-semibold text-[#1351B4] hover:underline mb-6">
          <ArrowLeft className="w-3.5 h-3.5 mr-1" />
          Voltar para a página inicial
        </Link>

        <div className="flex items-center gap-4 pb-6 border-b border-gray-100 mb-8">
          <div className="w-12 h-12 rounded-xl bg-green-50 text-green-700 flex items-center justify-center">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-green-700">
              Lei Geral de Proteção de Dados (Lei nº 13.709/2018)
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 mt-0.5">
              Política de Privacidade e Proteção de Dados
            </h1>
          </div>
        </div>

        <div className="prose prose-sm max-w-none text-gray-700 space-y-5 text-sm leading-relaxed">
          <p>
            O <strong>SOSP (Sistema de Orientação para Serviços Públicos)</strong>, mantido pelo Governo do Estado de Alagoas,
            trata os dados pessoais de cidadãos e servidores em estrita observância à Lei Geral de Proteção de Dados Pessoais (LGPD).
          </p>

          <h2 className="text-lg font-bold text-gray-900 pt-2">1. Dados Coletados e Finalidade</h2>
          <p>
            Coletamos apenas as informações estritamente necessárias para a prestação dos serviços públicos solicitados,
            incluindo nome completo, CPF, data de nascimento, filiação, telefone, e-mail e endereço residencial. Tais dados
            são utilizados unicamente para:
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li>Identificação segura do cidadão junto aos órgãos oficiais (ex.: DETRAN, SSP, SEFAZ);</li>
            <li>Geração de protocolo rastreável de agendamento (AAAAMMDD-XXXX);</li>
            <li>Envio de comprovantes e notificações transacionais por e-mail.</li>
          </ul>

          <h2 className="text-lg font-bold text-gray-900 pt-2">2. Segurança e Criptografia</h2>
          <p>
            As senhas de acesso são armazenadas utilizando função de derivação de chave de alta resistência
            (<strong>Argon2id com salt aleatório</strong>), impossibilitando sua recuperação em texto simples.
            Todas as comunicações entre seu navegador e nossos servidores são protegidas por criptografia TLS 1.3.
          </p>

          <h2 className="text-lg font-bold text-gray-900 pt-2">3. Direitos do Titular de Dados</h2>
          <p>
            Você pode solicitar a qualquer momento a confirmação da existência de tratamento, o acesso aos seus dados
            ou a correção de dados incompletos ou inexatos através da área do cidadão ou da Ouvidoria Estadual.
          </p>
        </div>
      </div>
    </div>
  );
}

