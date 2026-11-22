"use client";

import React from "react";
import Link from "next/link";
import { ShieldCheck, ArrowLeft, GraduationCap, Lock, CheckCircle2 } from "lucide-react";

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[850px] mx-auto bg-white rounded-2xl p-6 sm:p-10 shadow-sm border border-gray-200">
        <Link href="/" className="inline-flex items-center text-xs font-semibold text-[#1351B4] hover:underline mb-6">
          <ArrowLeft className="w-3.5 h-3.5 mr-1" />
          Voltar para a página inicial
        </Link>

        {/* Banner Acadêmico */}
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl flex items-start gap-3">
          <GraduationCap className="w-5 h-5 text-[#1351B4] shrink-0 mt-0.5" />
          <div className="text-xs text-blue-900 leading-relaxed">
            <span className="font-bold">Aviso Institucional e Acadêmico:</span> O SOSP é um projeto
            acadêmico desenvolvido por estudantes do curso de Engenharia de Software do CESMAC para fins
            de estudo, pesquisa e demonstração de arquiteturas de software público. Esta plataforma não
            substitui canais oficiais de atendimento governamental.
          </div>
        </div>

        <div className="flex items-center gap-4 pb-6 border-b border-gray-100 mb-8">
          <div className="w-12 h-12 rounded-xl bg-green-50 text-green-700 flex items-center justify-center">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-green-700">
              Lei Geral de Proteção de Dados (Lei nº 13.709/2018 — LGPD)
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 mt-0.5">
              Política de Privacidade e Proteção de Dados
            </h1>
          </div>
        </div>

        <div className="prose prose-sm max-w-none text-gray-700 space-y-5 text-sm leading-relaxed">
          <p>
            O <strong>SOSP (Sistema de Orientação para Serviços Públicos)</strong> trata dados pessoais em
            estrita conformidade com os princípios e bases legais da Lei Geral de Proteção de Dados Pessoais
            (Lei Federal nº 13.709/2018).
          </p>

          <h2 className="text-lg font-bold text-gray-900 pt-2">1. Dados Coletados e Princípio da Minimização</h2>
          <p>
            Coletamos exclusivamente as informações estritamente necessárias para a prestação do serviço
            de orientação e simulação de agendamento presencial (Art. 6º, III da LGPD), compreendendo:
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Identificação do Cidadão:</strong> Nome completo, CPF, data de nascimento e filiação materna;</li>
            <li><strong>Acessibilidade (PCD):</strong> Condição de Pessoa com Deficiência para viabilizar atendimento prioritário e adequado;</li>
            <li><strong>Contato:</strong> E-mail e telefone celular para emissão de comprovantes e protocolos transacionais;</li>
            <li><strong>Localização:</strong> CEP, logradouro e município para direcionamento às unidades de atendimento competentes.</li>
          </ul>

          <h2 className="text-lg font-bold text-gray-900 pt-2">2. Finalidade e Bases Legais</h2>
          <p>
            O tratamento de dados fundamenta-se nas seguintes hipóteses legais previstas na LGPD:
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Execução de Políticas Públicas e Simulação Didática (Art. 7º, III):</strong> Orientação ao cidadão sobre etapas, documentos e agendamento de serviços essenciais;</li>
            <li><strong>Proteção à Saúde e Acessibilidade (Art. 11, II):</strong> Dados sensíveis relacionados a deficiências utilizados estritamente para adequação física do atendimento presencial.</li>
          </ul>

          <h2 className="text-lg font-bold text-gray-900 pt-2">3. Segurança, Criptografia e Armazenamento</h2>
          <p>
            Adotamos medidas técnicas e organizacionais de segurança da informação compatíveis com os mais rigorosos padrões da indústria:
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Senhas Criptografadas:</strong> Armazenadas exclusivamente sob a função criptográfica de derivação de chave <strong>Argon2id com salt aleatório</strong>, impossibilitando sua leitura em texto claro;</li>
            <li><strong>Tráfego Seguro:</strong> Todas as comunicações entre o navegador e as APIs utilizam criptografia TLS 1.3 com certificados válidos;</li>
            <li><strong>Trilha de Auditoria Imutável:</strong> Operações críticas geram registros de auditoria em tabela protegida (auditEvent), com registro de data, hora e IP do solicitante.</li>
          </ul>

          <h2 className="text-lg font-bold text-gray-900 pt-2">4. Exclusão Lógica e Retenção de Dados (Regra RN-40)</h2>
          <p>
            Para resguardar a rastreabilidade e a integridade de registros públicos e históricos de auditoria,
            registros de agendamento e cadastros não sofrem exclusão física imediata no banco de dados. Qualquer
            solicitação de desativação opera por exclusão lógica (<code>isActive = false</code>, <code>deletedAt = NOW()</code>),
            sendo os dados anonimizados conforme preconiza o Art. 16 da LGPD.
          </p>

          <h2 className="text-lg font-bold text-gray-900 pt-2">5. Direitos do Titular de Dados (Art. 18 da LGPD)</h2>
          <p>
            O titular dos dados possui o direito inalienável de solicitar, a qualquer momento:
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li>Confirmação da existência de tratamento e acesso aos dados;</li>
            <li>Correção de dados incompletos, inexatos ou desatualizados;</li>
            <li>Informação sobre as entidades públicas e privadas com as quais o projeto interage.</li>
          </ul>
          <p className="pt-2 text-xs text-gray-500">
            Nenhum dado cadastrado no SOSP é comercializado, cedido ou compartilhado com terceiros para fins publicitários.
          </p>
        </div>
      </div>
    </div>
  );
}
