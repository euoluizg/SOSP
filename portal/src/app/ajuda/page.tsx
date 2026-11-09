"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  HelpCircle,
  UserPlus,
  Search,
  Calendar,
  FileCheck,
  Clock,
  ArrowRight,
  ChevronDown,
  ShieldAlert,
  ExternalLink,
  BookOpen,
} from "lucide-react";

export default function HelpPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [openSection, setOpenSection] = useState<number | null>(null);

  const toggleSection = (index: number) => {
    setOpenSection(openSection === index ? null : index);
  };

  const helpTopics = [
    {
      id: 1,
      icon: UserPlus,
      title: "Como criar sua conta de cidadão",
      summary: "Passo a passo para cadastro no SOSP utilizando seu CPF e dados básicos.",
      details: [
        "Acesse a opção 'Criar conta' no topo do portal ou na tela de login.",
        "Informe seu nome completo, CPF, data de nascimento e filiação.",
        "Preencha seu CEP para autopreenchimento do endereço residencial.",
        "Crie uma senha segura atendendo aos 5 requisitos (8 caracteres, maiúscula, minúscula, número e caractere especial).",
        "Após a confirmação, você já pode acessar a plataforma e realizar seus agendamentos.",
      ],
      linkText: "Ir para o Cadastro",
      linkHref: "/cadastro",
    },
    {
      id: 2,
      icon: Search,
      title: "Como pesquisar serviços e consultar exigências",
      summary: "Encontre serviços estaduais e verifique documentos necessários antes de sair de casa.",
      details: [
        "Utilize a barra de pesquisa na página inicial ou acesse o Catálogo de Serviços.",
        "Filtre por órgão (SSP, DETRAN, SEFAZ, etc.), categoria ou modalidade (Presencial, Online ou Híbrido).",
        "Acesse a Ficha Orientativa do serviço para consultar os 8 blocos informativos: O que é, Quem tem direito, Documentos obrigatórios, Onde fazer, Custos e Prazos.",
        "Utilize o Guia Passo a Passo para marcar os documentos que você já reuniu no checklist.",
      ],
      linkText: "Explorar Serviços",
      linkHref: "/servicos",
    },
    {
      id: 3,
      icon: Calendar,
      title: "Como agendar seu atendimento presencial",
      summary: "Escolha a unidade mais próxima, data e horário disponível em slots de 30 minutos.",
      details: [
        "Na ficha do serviço desejado, clique no botão 'Agendar Atendimento'.",
        "Selecione o posto de atendimento de sua preferência (ex.: Centrais Já! Centro ou Farol).",
        "Escolha a data desejada no calendário oficial e selecione um dos horários vagos de 30 minutos.",
        "Confirme seus dados e clique em 'Finalizar Agendamento'.",
        "Guarde o número do protocolo gerado no formato AAAAMMDD-XXXX e baixe o comprovante em PDF.",
      ],
      linkText: "Consultar Agendamentos",
      linkHref: "/cidadao/meus-agendamentos",
    },
    {
      id: 4,
      icon: FileCheck,
      title: "Regras de cancelamento e remarcação",
      summary: "Saiba como cancelar voluntariamente seu agendamento caso surja um imprevisto.",
      details: [
        "Conforme a regra RN-22 do SOSP, o cancelamento voluntário pode ser feito até 24 horas antes do horário marcado.",
        "Acesse a página 'Meus Agendamentos' com seu login ativo.",
        "Localize o agendamento ativo e clique no botão 'Cancelar'.",
        "Confirme o cancelamento no modal informativo. A vaga será liberada imediatamente para outro cidadão.",
      ],
      linkText: "Meus Agendamentos",
      linkHref: "/cidadao/meus-agendamentos",
    },
    {
      id: 5,
      icon: Clock,
      title: "Acompanhar protocolos e andamento",
      summary: "Consulte a linha do tempo e o status atual do seu processo.",
      details: [
        "Cada agendamento concluído gera um protocolo único no padrão AAAAMMDD-XXXX.",
        "Pelo protocolo, você acompanha as etapas: Agendado ➔ Confirmado ➔ Em Atendimento ➔ Concluído.",
        "Caso o serviço exija envio prévio de documentos, acerte os anexos no formato PDF, PNG ou JPG (até 10 MB).",
      ],
      linkText: "Ver Perguntas Frequentes",
      linkHref: "/faq",
    },
  ];

  const filteredTopics = helpTopics.filter(
    (t) =>
      t.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.summary.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[1200px] mx-auto space-y-10">
        {/* Breadcrumb */}
        <nav className="flex items-center text-xs text-gray-500" aria-label="Breadcrumb">
          <Link href="/" className="hover:text-[#1351B4]">
            Início
          </Link>
          <span className="mx-2 text-gray-300">/</span>
          <span className="text-gray-900 font-semibold" aria-current="page">
            Central de Ajuda
          </span>
        </nav>

        {/* Hero da Central de Ajuda */}
        <div className="bg-gradient-to-r from-[#1351B4] to-[#0C326F] text-white rounded-3xl p-8 sm:p-12 shadow-sm">
          <div className="max-w-2xl space-y-4">
            <div className="inline-flex items-center gap-2 bg-white/10 text-white/90 px-3 py-1 rounded-full text-xs font-semibold backdrop-blur-xs">
              <HelpCircle className="w-4 h-4" />
              Orientações ao Cidadão e ao Servidor
            </div>
            <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight leading-tight">
              Como podemos ajudar você hoje?
            </h1>
            <p className="text-sm sm:text-base text-white/80 leading-relaxed">
              Consulte os guias práticos abaixo para entender como encontrar serviços, agendar
              atendimentos e gerenciar seus protocolos no SOSP.
            </p>

            {/* Campo de Busca Rápida */}
            <div className="relative pt-2">
              <Search className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Busque por um tópico (ex: agendamento, senha, cancelamento)..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#F9AB00] text-sm shadow-sm"
                aria-label="Buscar tópicos de ajuda"
              />
            </div>
          </div>
        </div>

        {/* Grade de Guias Rápidos */}
        <div className="space-y-6">
          <div className="flex items-center justify-between border-b border-gray-200 pb-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Guias de Utilização do Sistema</h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Respostas práticas e orientações passo a passo para as principais ações do portal
              </p>
            </div>
            <Link
              href="/faq"
              className="text-xs font-bold text-[#1351B4] hover:underline inline-flex items-center gap-1"
            >
              <span>Ver FAQ Completo</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-4">
            {filteredTopics.map((topic, index) => {
              const IconComponent = topic.icon;
              const isOpen = openSection === index;
              return (
                <div
                  key={topic.id}
                  className="bg-white rounded-2xl border border-gray-200 shadow-xs overflow-hidden transition-all"
                >
                  <button
                    type="button"
                    onClick={() => toggleSection(index)}
                    className="w-full p-6 text-left flex items-start justify-between gap-4 hover:bg-gray-50/50 transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-[#1351B4]"
                    aria-expanded={isOpen}
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#1351B4] flex items-center justify-center shrink-0 mt-0.5">
                        <IconComponent className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-gray-900">{topic.title}</h3>
                        <p className="text-xs text-gray-500 mt-1">{topic.summary}</p>
                      </div>
                    </div>
                    <div className="shrink-0 p-1 text-gray-400">
                      <ChevronDown
                        className={`w-5 h-5 transition-transform duration-200 ${
                          isOpen ? "rotate-180 text-[#1351B4]" : ""
                        }`}
                      />
                    </div>
                  </button>

                  {isOpen && (
                    <div className="px-6 pb-6 pt-2 border-t border-gray-100 bg-gray-50/30">
                      <ol className="list-decimal list-inside space-y-2 text-sm text-gray-700 leading-relaxed mb-4">
                        {topic.details.map((step, sIdx) => (
                          <li key={sIdx} className="pl-1">
                            <span>{step}</span>
                          </li>
                        ))}
                      </ol>
                      {topic.linkHref && (
                        <Link
                          href={topic.linkHref}
                          className="inline-flex items-center text-xs font-bold text-[#1351B4] hover:underline gap-1.5"
                        >
                          <span>{topic.linkText}</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      )}
                    </div>
                  )}
                </div>
              );
            })}

            {filteredTopics.length === 0 && (
              <div className="bg-white rounded-2xl p-8 text-center border border-gray-200">
                <HelpCircle className="w-10 h-10 text-gray-400 mx-auto mb-2" />
                <h3 className="text-base font-bold text-gray-900">Nenhum tópico encontrado</h3>
                <p className="text-xs text-gray-500 mt-1">
                  Tente buscar por outro termo ou consulte o nosso FAQ completo.
                </p>
                <Link
                  href="/faq"
                  className="mt-4 inline-flex items-center text-xs font-bold bg-[#1351B4] text-white px-4 py-2 rounded-lg hover:bg-[#0C326F] transition-colors"
                >
                  Acessar Perguntas Frequentes
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Card Informativo sobre o Projeto Acadêmico */}
        <div className="bg-amber-50/70 border border-amber-200/80 rounded-2xl p-6 sm:p-8 flex flex-col sm:flex-row items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center shrink-0">
            <BookOpen className="w-5 h-5" />
          </div>
          <div className="space-y-1.5 text-xs text-amber-900">
            <h4 className="font-bold text-sm text-amber-950">
              Informação sobre Canais de Suporte e Atendimento
            </h4>
            <p className="leading-relaxed">
              O <strong>SOSP (Sistema de Orientação para Serviços Públicos)</strong> é desenvolvido
              exclusivamente como projeto acadêmico de graduação no Centro Universitário CESMAC
              (Maceió - AL). Por este motivo, não disponibilizamos canais de suporte telefônico
              ou e-mails institucionais de atendimento governamental.
            </p>
            <p className="leading-relaxed">
              Para serviços públicos oficiais do Estado de Alagoas, consulte os canais oficiais
              da Secretaria de Estado do Planejamento, Gestão e Patrimônio (SEPLAG/AL) e o portal{" "}
              <Link
                href="https://www.gov.br"
                target="_blank"
                rel="noopener noreferrer"
                className="font-bold underline text-amber-950 inline-flex items-center gap-0.5"
              >
                Gov.br <ExternalLink className="w-3 h-3" />
              </Link>
              .
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
