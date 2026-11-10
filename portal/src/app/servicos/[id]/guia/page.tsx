"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  CheckSquare,
  Square,
  Printer,
  Calendar,
  ChevronRight,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { getServiceById } from "@/services/apiClient";
import type { Service } from "@/types/api";

export default function ServiceGuidePage() {
  const params = useParams();
  const router = useRouter();
  const serviceId = params?.id as string;

  const [service, setService] = useState<Service | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Estado dos documentos checados, persistido no localStorage (RN-15)
  const [checkedDocs, setCheckedDocs] = useState<Record<string, boolean>>({});

  useEffect(() => {
    async function loadService() {
      setIsLoading(true);
      try {
        const data = await getServiceById(serviceId);
        setService(data);

        // Carrega progresso salvo no localStorage
        const storageKey = `sosp_checklist_${serviceId}`;
        const saved = localStorage.getItem(storageKey);
        if (saved) {
          try {
            setCheckedDocs(JSON.parse(saved));
          } catch {
            // Ignora erro de parse
          }
        }
      } catch (err) {
        console.error("Erro ao carregar dados do guia:", err);
      } finally {
        setIsLoading(false);
      }
    }
    if (serviceId) {
      loadService();
    }
  }, [serviceId]);

  const toggleDocument = (docId: string) => {
    setCheckedDocs((prev) => {
      const updated = { ...prev, [docId]: !prev[docId] };
      const storageKey = `sosp_checklist_${serviceId}`;
      localStorage.setItem(storageKey, JSON.stringify(updated));
      return updated;
    });
  };

  const handlePrint = () => {
    window.print();
  };

  if (isLoading) {
    return (
      <div className="max-w-[1000px] mx-auto py-10 px-4" aria-busy="true">
        <span className="sr-only">Carregando passo a passo e checklist de documentos...</span>
        <Skeleton className="h-6 w-48 mb-4" />
        <Skeleton className="h-10 w-2/3 mb-6" />
        <Skeleton className="h-28 w-full rounded-2xl mb-8" />
        <Skeleton className="h-60 w-full rounded-2xl" />
      </div>
    );
  }

  if (!service) {
    return (
      <div className="max-w-md mx-auto py-20 px-4 text-center">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-gray-900">Serviço não encontrado</h2>
        <Link href="/servicos" className="mt-4 inline-block">
          <Button variant="primary">Voltar ao catálogo</Button>
        </Link>
      </div>
    );
  }

  const requiredDocuments = service.documents.filter((d) => d.isRequired);
  const optionalDocuments = service.documents.filter((d) => !d.isRequired);

  const totalRequired = requiredDocuments.length;
  const checkedRequired = requiredDocuments.filter((d) => checkedDocs[d.id]).length;
  const progressPercent = totalRequired > 0 ? Math.round((checkedRequired / totalRequired) * 100) : 100;
  const isReadyToSchedule = checkedRequired === totalRequired;

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8 print:bg-white print:py-0">
      <div className="max-w-[1000px] mx-auto">
        {/* Breadcrumb (oculto na impressão) */}
        <nav className="flex items-center text-xs text-gray-500 mb-6 print:hidden" aria-label="Breadcrumb">
          <Link href="/" className="hover:text-[#1351B4]">Início</Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <Link href="/servicos" className="hover:text-[#1351B4]">Catálogo</Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <Link href={`/servicos/${service.id}`} className="hover:text-[#1351B4] truncate max-w-xs">
            {service.name}
          </Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <span className="font-semibold text-gray-900" aria-current="page">
            Guia e Checklist
          </span>
        </nav>

        {/* Topo com Ações de Impressão e Agendamento */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <span className="text-xs font-bold text-[#1351B4] uppercase tracking-wider">
              Guia Passo a Passo & Checklist Oficial
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 mt-1">
              {service.name}
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Órgão: {service.agencyName} ({service.agencyAcronym})
            </p>
          </div>

          <div className="flex items-center gap-3 print:hidden">
            <Button variant="secondary" onClick={handlePrint} className="text-xs">
              <Printer className="w-4 h-4 mr-1.5" />
              Imprimir Guia (PDF)
            </Button>
            {service.channel !== "online" && (
              <Link href={`/servicos/${service.id}/agendamento`}>
                <Button variant="primary" className="text-xs font-bold shadow-md">
                  <Calendar className="w-4 h-4 mr-1.5" />
                  Ir para Agendamento
                </Button>
              </Link>
            )}
          </div>
        </div>

        {/* Card de Progresso do Checklist (RN-15) */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200 mb-8 print:border-none print:shadow-none">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
            <div>
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <CheckSquare className="w-5 h-5 text-[#1351B4]" />
                Seu Progresso de Documentos
              </h2>
              <p className="text-xs text-gray-500 mt-1">
                Marque os documentos que você já tem em mãos para não esquecer nada no dia do atendimento.
              </p>
            </div>

            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-[#1351B4]">{progressPercent}%</span>
              <span className="text-xs text-gray-500">
                ({checkedRequired} de {totalRequired} obrigatórios)
              </span>
            </div>
          </div>

          {/* Barra de progresso visual */}
          <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                progressPercent === 100 ? "bg-green-600" : "bg-[#1351B4]"
              }`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          {isReadyToSchedule && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-xl flex items-center gap-2 text-xs text-green-800 animate-fadeIn">
              <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0" />
              <span>
                <strong>Tudo pronto!</strong> Você já tem todos os documentos obrigatórios separados. Pode agendar com tranquilidade.
              </span>
            </div>
          )}
        </div>

        {/* Seção 1: Checklist de Documentos Obrigatórios */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200 mb-8">
          <h2 className="text-lg font-bold text-gray-900 mb-2">
            1. Documentos Obrigatórios
          </h2>
          <p className="text-xs text-gray-500 mb-6">
            A apresentação destes documentos originais é indispensável para a conclusão do serviço.
          </p>

          <div className="space-y-3">
            {requiredDocuments.map((doc) => {
              const isChecked = Boolean(checkedDocs[doc.id]);
              return (
                <div
                  key={doc.id}
                  onClick={() => toggleDocument(doc.id)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer flex items-start gap-3.5 select-none ${
                    isChecked
                      ? "bg-blue-50/60 border-blue-300"
                      : "bg-gray-50 hover:bg-gray-100/70 border-gray-200"
                  }`}
                >
                  <button
                    type="button"
                    className="mt-0.5 text-gray-400 hover:text-[#1351B4] focus:outline-none"
                    aria-label={isChecked ? `Desmarcar ${doc.name}` : `Marcar ${doc.name}`}
                  >
                    {isChecked ? (
                      <CheckSquare className="w-5 h-5 text-[#1351B4]" />
                    ) : (
                      <Square className="w-5 h-5 text-gray-400" />
                    )}
                  </button>
                  <div className="flex-1">
                    <span
                      className={`font-semibold text-sm block ${
                        isChecked ? "text-gray-900 line-through decoration-blue-500" : "text-gray-900"
                      }`}
                    >
                      {doc.name}
                    </span>
                    {doc.description && (
                      <p className="text-xs text-gray-600 mt-1">{doc.description}</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Seção 2: Documentos Opcionais / Casos Específicos */}
        {optionalDocuments.length > 0 && (
          <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200 mb-8">
            <h2 className="text-lg font-bold text-gray-900 mb-2">
              2. Documentos Complementares ou Específicos
            </h2>
            <p className="text-xs text-gray-500 mb-6">
              Necessários apenas em situações específicas (ex.: menores de idade, representação legal, isenções).
            </p>

            <div className="space-y-3">
              {optionalDocuments.map((doc) => {
                const isChecked = Boolean(checkedDocs[doc.id]);
                return (
                  <div
                    key={doc.id}
                    onClick={() => toggleDocument(doc.id)}
                    className={`p-4 rounded-xl border transition-all cursor-pointer flex items-start gap-3.5 select-none ${
                      isChecked
                        ? "bg-amber-50/60 border-amber-300"
                        : "bg-gray-50 hover:bg-gray-100/70 border-gray-200"
                    }`}
                  >
                    <button
                      type="button"
                      className="mt-0.5 text-gray-400 hover:text-amber-600 focus:outline-none"
                      aria-label={isChecked ? `Desmarcar ${doc.name}` : `Marcar ${doc.name}`}
                    >
                      {isChecked ? (
                        <CheckSquare className="w-5 h-5 text-amber-600" />
                      ) : (
                        <Square className="w-5 h-5 text-gray-400" />
                      )}
                    </button>
                    <div className="flex-1">
                      <span className="font-semibold text-sm text-gray-900 block">{doc.name}</span>
                      {doc.description && (
                        <p className="text-xs text-gray-600 mt-1">{doc.description}</p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Seção 3: Stepper Interativo com as Etapas */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200 mb-8">
          <h2 className="text-lg font-bold text-gray-900 mb-6">
            3. Como Seguir: Etapas do Atendimento
          </h2>

          <div className="space-y-6">
            {service.steps.map((st) => (
              <div key={st.stepOrder} className="flex gap-4 items-start">
                <div className="w-8 h-8 rounded-full bg-[#1351B4] text-white flex items-center justify-center font-bold text-sm shrink-0">
                  {st.stepOrder}
                </div>
                <div className="flex-1 pb-4 border-b border-gray-100 last:border-none">
                  <h3 className="font-bold text-gray-900 text-sm sm:text-base">{st.title}</h3>
                  <p className="text-xs sm:text-sm text-gray-600 mt-1">{st.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Botão de Rodapé para Agendamento */}
        {service.channel !== "online" && (
          <div className="bg-gradient-to-r from-blue-900 to-[#1351B4] rounded-2xl p-6 sm:p-8 text-white flex flex-col sm:flex-row items-center justify-between gap-6 print:hidden">
            <div>
              <h2 className="text-xl font-bold">Pronto para marcar seu horário?</h2>
              <p className="text-xs sm:text-sm text-blue-100 mt-1 max-w-xl">
                Escolha a unidade mais próxima, a data ideal e selecione um horário de 30 minutos sem filas.
              </p>
            </div>
            <Link href={`/servicos/${service.id}/agendamento`} className="w-full sm:w-auto">
              <Button
                variant="secondary"
                className="w-full sm:w-auto bg-white text-[#1351B4] font-bold px-8 py-3 text-sm shadow-lg hover:bg-gray-100"
              >
                Agendar Horário
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
