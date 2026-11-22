"use client";

import React, { useState, useEffect } from "react";
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
  Lock,
  AlertCircle,
  UserCheck,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { openQuestion } from "@/services/apiClient";
import type { ProblemDetails } from "@/types/api";

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

  // Estados de autenticação e sessão do cidadão (RF-11, UC-14)
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [citizenName, setCitizenName] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [userSubject, setUserSubject] = useState("");
  const [userQuestion, setUserQuestion] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedProtocol, setSubmittedProtocol] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSessionExpired, setIsSessionExpired] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("sosp_auth_token");
    if (!token) {
      setIsAuthenticated(false);
      return;
    }
    setIsAuthenticated(true);

    try {
      const stored = localStorage.getItem("sosp_user");
      if (stored) {
        const user = JSON.parse(stored);
        if (user.fullName) setCitizenName(user.fullName);
        if (user.email) setUserEmail(user.email);
      }
    } catch {
      // Ignora erro no parse do JSON
    }
  }, []);

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
    if (!userQuestion.trim()) return;

    setIsSubmitting(true);
    setErrorMessage(null);
    setIsSessionExpired(false);

    try {
      const res = await openQuestion({
        citizenName: citizenName || "Cidadão Identificado",
        email: userEmail || "cidadao@exemplo.com.br",
        category: activeCategory !== "all" ? activeCategory : "Geral",
        subject: userSubject.trim() || "Dúvida enviada pelo portal FAQ",
        description: userQuestion.trim(),
      });
      setSubmittedProtocol(res.protocolNumber || "20261109-0001");
      setUserQuestion("");
      setUserSubject("");
    } catch (err: unknown) {
      const problem = err as ProblemDetails;
      if (problem?.status === 401) {
        if (typeof window !== "undefined") {
          localStorage.removeItem("sosp_auth_token");
          localStorage.removeItem("sosp_user");
        }
        setIsAuthenticated(false);
        setIsSessionExpired(true);
        setErrorMessage(
          "Sua sessão expirou por inatividade (Regra RN-28). Por favor, realize o login novamente para enviar sua dúvida."
        );
      } else {
        setErrorMessage(
          problem?.detail || "Ocorreu um erro ao registrar sua dúvida. Tente novamente mais tarde."
        );
      }
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

        {/* Seção de Envio de Dúvidas ao Suporte / Ouvidoria (UC-14 / RF-11) */}
        {isAuthenticated === null ? (
          <div
            className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200 animate-pulse"
            aria-busy="true"
          >
            <div className="h-6 bg-gray-200 rounded w-1/3 mb-2" />
            <div className="h-4 bg-gray-100 rounded w-2/3" />
          </div>
        ) : !isAuthenticated ? (
          /* Estado Não Autenticado: Banner Orientativo com link seguro de login */
          <div
            className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200"
            data-testid="faq-auth-guard"
          >
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-50 text-[#1351B4] flex items-center justify-center shrink-0">
                <Lock className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <h2 className="text-lg font-bold text-gray-900">
                  Não encontrou o que procurava?
                </h2>
                <p className="mt-1 text-sm text-gray-600">
                  Para enviar uma dúvida diretamente à nossa equipe de atendimento do SOSP, é necessário estar identificado no portal.
                </p>

                {isSessionExpired && errorMessage && (
                  <div
                    className="mt-4 p-4 bg-amber-50 border-l-4 border-amber-500 rounded-md text-amber-900 text-sm flex items-start gap-2"
                    role="alert"
                  >
                    <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <strong className="font-semibold">Sessão Expirada:</strong> {errorMessage}
                    </div>
                  </div>
                )}

                <div className="mt-5 flex flex-col sm:flex-row sm:items-center gap-3">
                  <Link
                    href="/login?redirect=/faq"
                    className="inline-flex items-center justify-center px-5 py-2.5 rounded-xl bg-[#1351B4] text-white text-sm font-semibold hover:bg-[#0F2942] transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-[#1351B4] focus:ring-offset-2"
                    data-testid="faq-login-cta"
                  >
                    Entrar com CPF e Senha
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Link>
                  <span className="text-xs text-gray-500">
                    Ainda não tem conta?{" "}
                    <Link
                      href="/cadastro?redirect=/faq"
                      className="text-[#1351B4] font-semibold hover:underline"
                    >
                      Cadastre-se gratuitamente
                    </Link>
                  </span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Estado Autenticado: Formulário com pré-preenchimento e tratamento de 401 */
          <div
            className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200"
            data-testid="faq-authenticated-form"
          >
            <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
              <div className="flex items-center gap-3">
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
              <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-50 text-[#1351B4] rounded-full text-xs font-medium border border-blue-100">
                <UserCheck className="w-3.5 h-3.5" />
                <span>
                  Identificado como: <strong>{citizenName || "Cidadão Autenticado"}</strong>
                </span>
              </div>
            </div>

            {submittedProtocol ? (
              <div
                className="p-5 bg-green-50 border border-green-200 rounded-xl text-green-900 text-sm animate-fadeIn"
                data-testid="faq-success-banner"
              >
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-6 h-6 text-green-600 shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <h3 className="font-bold text-green-900 text-base">
                      Dúvida registrada com sucesso!
                    </h3>
                    <p className="mt-1 text-sm text-green-800">
                      Seu atendimento foi aberto sob o protocolo{" "}
                      <strong className="font-mono font-bold text-green-950 underline">
                        {submittedProtocol}
                      </strong>.
                    </p>
                    <p className="mt-1 text-xs text-green-700">
                      Nossa equipe responderá no e-mail informado ({userEmail || "cadastrado"}) em até 1 dia útil.
                    </p>
                    <button
                      type="button"
                      onClick={() => setSubmittedProtocol(null)}
                      className="mt-3 text-xs font-semibold text-[#1351B4] underline hover:text-[#0F2942]"
                    >
                      Enviar outra dúvida
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmitQuestion} className="space-y-4">
                {errorMessage && (
                  <div
                    className="p-4 bg-red-50 border-l-4 border-red-500 rounded-md text-red-800 text-sm flex items-start gap-2"
                    role="alert"
                  >
                    <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                    <div>{errorMessage}</div>
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Input
                    label="Assunto da Dúvida"
                    id="user-subject"
                    type="text"
                    placeholder="Ex.: Dúvida sobre agendamento ou taxas (opcional)"
                    value={userSubject}
                    onChange={(e) => setUserSubject(e.target.value)}
                  />

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
                    <label
                      htmlFor="user-q"
                      className="block text-sm font-semibold text-gray-700 mb-1.5"
                    >
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
                  <Button
                    type="submit"
                    variant="primary"
                    isLoading={isSubmitting}
                    className="px-6 shadow-sm"
                  >
                    <Send className="w-4 h-4 mr-2" />
                    Enviar Pergunta
                  </Button>
                </div>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
