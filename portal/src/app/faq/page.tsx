"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  HelpCircle,
  Search,
  ChevronDown,
  MessageSquare,
  FileText,
  Calendar,
  CreditCard,
  Clock,
  ArrowRight,
  Send,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { openQuestion } from "@/services/apiClient";

interface FaqItem {
  id: string;
  category: "docs" | "scheduling" | "costs" | "general";
  question: string;
  answer: string;
}

const FAQ_ITEMS: FaqItem[] = [
  {
    id: "f-1",
    category: "docs",
    question: "Quais documentos preciso levar no dia do atendimento?",
    answer:
      "A lista exata de documentos depende do serviço desejado. Recomendamos que você acesse a Ficha do Serviço no catálogo e consulte o checklist interativo antes de sair de casa para separar todos os originais necessários.",
  },
  {
    id: "f-2",
    category: "scheduling",
    question: "Posso cancelar ou remarcar um agendamento já confirmado?",
    answer:
      "Sim. Conforme a regra RN-22 do SOSP, você pode cancelar ou remarcar seu atendimento pelo portal com até 24 horas de antecedência do horário marcado. Basta acessar 'Meus Agendamentos' com seu CPF e senha.",
  },
  {
    id: "f-3",
    category: "scheduling",
    question: "O que acontece se eu não comparecer no horário marcado?",
    answer:
      "Caso não possa comparecer, solicitamos que realize o cancelamento prévio para liberar a vaga para outro cidadão. O não comparecimento sem justificativa é registrado pelo atendente na central de triagem (RN-23).",
  },
  {
    id: "f-4",
    category: "costs",
    question: "Todos os serviços públicos cadastrados no SOSP são gratuitos?",
    answer:
      "Muitos serviços essenciais (como a 1ª via do RG/CIN e o Cadastro Único) são totalmente gratuitos. Serviços que exigem taxa oficial do Estado (como a Renovação de CNH ou segundas vias) exibem o valor exato na ficha orientativa e as instruções de recolhimento via DARE/Guia.",
  },
  {
    id: "f-5",
    category: "general",
    question: "Por que o botão 'Entrar com Gov.br' não redireciona diretamente?",
    answer:
      "No MVP atual (regra D10), todos os cidadãos, servidores e gestores autenticam-se com segurança via CPF e senha local com hash criptográfico Argon2id. A integração com o login Gov.br estará disponível na versão 2.0.",
  },
];

export default function FaqPage() {
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [expandedId, setExpandedId] = useState<string | null>("f-1");

  // Dúvida enviada pelo cidadão (UC-14)
  const [userQuestion, setUserQuestion] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const filteredFaq = FAQ_ITEMS.filter((item) => {
    if (activeCategory !== "all" && item.category !== activeCategory) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        item.question.toLowerCase().includes(q) ||
        item.answer.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const handleSubmitQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userQuestion || !userEmail) return;

    setIsSubmitting(true);
    try {
      await openQuestion({
        citizenName: "Cidadão Anônimo",
        email: userEmail,
        category: activeCategory !== "all" ? activeCategory : "Geral",
        subject: "Dúvida enviada pelo portal FAQ",
        description: userQuestion,
      });
      setSubmitted(true);
      setUserQuestion("");
      setUserEmail("");
    } catch (err) {
      console.error("Erro ao enviar dúvida:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[1000px] mx-auto">
        {/* Topo Hero */}
        <div className="text-center max-w-2xl mx-auto mb-10">
          <div className="w-12 h-12 bg-blue-100 text-[#1351B4] rounded-2xl flex items-center justify-center mx-auto mb-3">
            <HelpCircle className="w-6 h-6" />
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            Perguntas Frequentes & Ajuda
          </h1>
          <p className="mt-2 text-sm sm:text-base text-gray-600">
            Tire dúvidas sobre agendamentos presenciais, documentos exigidos, taxas e funcionamento do portal.
          </p>

          {/* Barra de Busca de FAQ */}
          <div className="relative mt-6 max-w-lg mx-auto">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Digite sua dúvida (ex.: cancelar agendamento, documentos)..."
              className="w-full pl-11 pr-4 py-3 rounded-xl border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#1351B4] shadow-sm bg-white"
            />
            <Search className="w-5 h-5 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          </div>
        </div>

        {/* Categorias Rápidas */}
        <div className="flex flex-wrap justify-center gap-2 mb-8">
          {[
            { id: "all", label: "Todas as Dúvidas" },
            { id: "docs", label: "Documentos e Checklists" },
            { id: "scheduling", label: "Agendamentos e Prazos" },
            { id: "costs", label: "Custos e Taxas" },
            { id: "general", label: "Acesso e Conta" },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`px-4 py-2 text-xs sm:text-sm font-semibold rounded-full border transition-all ${
                activeCategory === cat.id
                  ? "bg-[#1351B4] text-white border-[#1351B4] shadow-sm"
                  : "bg-white text-gray-700 border-gray-200 hover:bg-gray-100"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Acordeão de Perguntas e Respostas */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 divide-y divide-gray-100 mb-12">
          {filteredFaq.length === 0 ? (
            <div className="p-8 text-center text-gray-500 text-sm">
              Nenhuma pergunta encontrada com o termo informado. Você pode enviar sua dúvida no formulário abaixo!
            </div>
          ) : (
            filteredFaq.map((item) => {
              const isExpanded = expandedId === item.id;
              return (
                <div key={item.id} className="p-5 sm:p-6">
                  <button
                    type="button"
                    onClick={() => setExpandedId(isExpanded ? null : item.id)}
                    className="w-full flex items-center justify-between text-left gap-4 focus:outline-none"
                    aria-expanded={isExpanded}
                  >
                    <span className="text-base font-bold text-gray-900 leading-snug">
                      {item.question}
                    </span>
                    <ChevronDown
                      className={`w-5 h-5 text-gray-400 shrink-0 transition-transform ${
                        isExpanded ? "rotate-180 text-[#1351B4]" : ""
                      }`}
                    />
                  </button>

                  {isExpanded && (
                    <div className="mt-3 text-sm text-gray-600 leading-relaxed pr-6 animate-fadeIn">
                      {item.answer}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Formulário de Envio de Dúvidas ao Suporte / Ouvidoria (UC-14) */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#1351B4] flex items-center justify-center">
              <MessageSquare className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">
                Não encontrou o que procurava?
              </h2>
              <p className="text-xs text-gray-500">
                Envie sua pergunta diretamente para a equipe de atendimento do SOSP
              </p>
            </div>
          </div>

          {submitted ? (
            <div className="p-4 bg-green-50 border border-green-200 rounded-xl flex items-center gap-3 text-green-800 text-sm animate-fadeIn">
              <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0" />
              <span>
                <strong>Sua dúvida foi enviada com sucesso!</strong> Nossa equipe responderá no e-mail informado em até 1 dia útil.
              </span>
            </div>
          ) : (
            <form onSubmit={handleSubmitQuestion} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Seu E-mail para Resposta"
                  id="user-email"
                  type="email"
                  placeholder="exemplo@email.com"
                  value={userEmail}
                  onChange={(e) => setUserEmail(e.target.value)}
                  required
                />
                <div className="sm:col-span-2">
                  <label htmlFor="user-q" className="block text-sm font-semibold text-gray-700 mb-1.5">
                    Descreva sua dúvida ou solicitação
                  </label>
                  <textarea
                    id="user-q"
                    rows={4}
                    value={userQuestion}
                    onChange={(e) => setUserQuestion(e.target.value)}
                    placeholder="Detalhe o serviço ou procedimento sobre o qual deseja orientação..."
                    className="w-full px-4 py-3 rounded-xl border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
                    required
                  />
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <Button type="submit" variant="primary" isLoading={isSubmitting} className="px-6 shadow-sm">
                  <Send className="w-4 h-4 mr-2" />
                  Enviar Pergunta
                </Button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

