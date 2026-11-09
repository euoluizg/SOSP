"use client";

import React from "react";
import Link from "next/link";
import { FileText, ArrowLeft, GraduationCap, CheckCircle2, AlertTriangle } from "lucide-react";

export default function TermsOfUsePage() {
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
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-[#1351B4] flex items-center justify-center">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-[#1351B4]">
              Condições de Acesso e Utilização
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 mt-0.5">
              Termos e Condições de Uso
            </h1>
          </div>
        </div>

        <div className="prose prose-sm max-w-none text-gray-700 space-y-5 text-sm leading-relaxed">
          <p>
            Ao utilizar o <strong>SOSP (Sistema de Orientação para Serviços Públicos)</strong>, o cidadão
            ou servidor declara ciência e concordância com os presentes Termos de Uso, com a Política de
            Privacidade e com as regras gerais de uso responsável de plataformas digitais.
          </p>

          <h2 className="text-lg font-bold text-gray-900 pt-2">1. Natureza da Plataforma</h2>
          <p>
            O SOSP destina-se à orientação sobre documentos necessários, etapas procedimentais e
            simulação de agendamento presencial em órgãos públicos conveniados (ex.: DETRAN, SSP, SEFAZ).
            Por se tratar de um ambiente acadêmico de desenvolvimento, os agendamentos realizados constituem
            simulações de atendimento presencial e exercícios de arquitetura de software.
          </p>

          <h2 className="text-lg font-bold text-gray-900 pt-2">2. Veracidade dos Dados e Responsabilidade</h2>
          <p>
            O usuário compromete-se a fornecer informações verídicas e autênticas durante o cadastro e a
            emissão de solicitações. O fornecimento deliberado de dados falsos ou a utilização de documentos
            de terceiros sem a devida autorização legal constitui infração às regras de uso e enseja bloqueio
            imediato da conta.
          </p>

          <h2 className="text-lg font-bold text-gray-900 pt-2">3. Regras de Agendamento, Vagas e Cancelamento</h2>
          <ul className="list-disc pl-5 space-y-2">
            <li>
              <strong>Agendamento Único por Serviço (Regra RN-21):</strong> Para garantir a equidade no acesso
              e evitar retenção abusiva de vagas, cada usuário pode manter apenas um agendamento com status ativo
              (pendente ou confirmado) para um mesmo serviço simultaneamente.
            </li>
            <li>
              <strong>Slots e Limite Diário (Regras RN-18 e RN-19):</strong> Os atendimentos são distribuídos em
              intervalos de 30 minutos, respeitando o expediente da unidade e descontando feriados e dias sem
              expediente.
            </li>
            <li>
              <strong>Cancelamento Antecipado (Regra RN-22):</strong> Caso o usuário não possa comparecer, o
              cancelamento deve ser formalizado pelo portal com antecedência mínima de <strong>24 horas</strong>,
              liberando a vaga para outro cidadão.
            </li>
          </ul>

          <h2 className="text-lg font-bold text-gray-900 pt-2">4. Segurança de Acesso e Bloqueio Preventivo (Regra RN-29)</h2>
          <p>
            Para salvaguardar as contas contra tentativas de força bruta, o sistema aplica bloqueio temporário
            de <strong>5 minutos após 5 tentativas de login consecutivas com credenciais incorretas</strong>.
            A sessão ativa é encerrada automaticamente após 30 minutos de inatividade (Regra RN-28).
          </p>

          <h2 className="text-lg font-bold text-gray-900 pt-2">5. Propriedade Intelectual e Código Aberto</h2>
          <p>
            O código-fonte e a documentação do projeto SOSP são desenvolvidos para fins acadêmicos e científicos,
            respeitando licenças de software livre e direitos autorais dos estudantes e orientadores do CESMAC.
          </p>
        </div>
      </div>
    </div>
  );
}
