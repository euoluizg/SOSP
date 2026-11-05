"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  FileText,
  Calendar,
  Clock,
  DollarSign,
  MapPin,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ChevronRight,
  ArrowRight,
  Share2,
  Printer,
  Sparkles,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Tag } from "@/components/ui/Tag";
import { Skeleton } from "@/components/ui/Skeleton";
import { getServiceById, getUnits } from "@/services/apiClient";
import type { Service, Unit } from "@/types/api";

export default function ServiceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const serviceId = params?.id as string;

  const [service, setService] = useState<Service | null>(null);
  const [units, setUnits] = useState<Unit[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const isReviewsFeatureEnabled = process.env.NEXT_PUBLIC_FEATURE_REVIEWS_ENABLED === "true";

  useEffect(() => {
    async function loadService() {
      setIsLoading(true);
      try {
        const data = await getServiceById(serviceId);
        setService(data);
        if (data) {
          const loadedUnits = await getUnits(data.agencyId);
          setUnits(loadedUnits);
        }
      } catch (err) {
        console.error("Erro ao carregar detalhes do serviço:", err);
      } finally {
        setIsLoading(false);
      }
    }
    if (serviceId) {
      loadService();
    }
  }, [serviceId]);

  if (isLoading) {
    return (
      <div className="max-w-[1200px] mx-auto py-10 px-4">
        <Skeleton className="h-6 w-48 mb-4" />
        <Skeleton className="h-10 w-3/4 mb-4" />
        <Skeleton className="h-5 w-1/2 mb-8" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <Skeleton className="h-40 w-full rounded-2xl" />
            <Skeleton className="h-60 w-full rounded-2xl" />
          </div>
          <div>
            <Skeleton className="h-72 w-full rounded-2xl" />
          </div>
        </div>
      </div>
    );
  }

  if (!service) {
    return (
      <div className="max-w-md mx-auto py-20 px-4 text-center">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-gray-900">Serviço não encontrado</h2>
        <p className="mt-2 text-sm text-gray-600">
          O serviço solicitado não foi encontrado ou está temporariamente indisponível.
        </p>
        <div className="mt-6">
          <Link href="/servicos">
            <Button variant="primary">Voltar ao catálogo de serviços</Button>
          </Link>
        </div>
      </div>
    );
  }

  const requiredDocuments = service.documents.filter((d) => d.isRequired);
  const optionalDocuments = service.documents.filter((d) => !d.isRequired);

  const channelLabel =
    service.channel === "online"
      ? "Online"
      : service.channel === "inPerson"
      ? "Presencial"
      : "Híbrido";

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[1200px] mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center text-xs text-gray-500 mb-6" aria-label="Breadcrumb">
          <Link href="/" className="hover:text-[#1351B4]">Início</Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <Link href="/servicos" className="hover:text-[#1351B4]">Catálogo de Serviços</Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <span className="font-semibold text-gray-900 truncate max-w-xs sm:max-w-md" aria-current="page">
            {service.name}
          </span>
        </nav>

        {/* Hero do Serviço */}
        <div className="bg-white rounded-3xl p-6 sm:p-10 shadow-sm border border-gray-200 mb-8">
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <Tag variant="channel">{channelLabel}</Tag>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-[#1351B4]">
              {service.category}
            </span>
            <span className="text-xs text-gray-500">
              Órgão: <strong>{service.agencyName} ({service.agencyAcronym})</strong>
            </span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold text-gray-900 tracking-tight leading-tight">
            {service.name}
          </h1>

          <p className="mt-4 text-base sm:text-lg text-gray-600 leading-relaxed max-w-3xl">
            {service.summary}
          </p>

          {/* Cards Rápidos de Metadados (Custo, Prazo, Validade) */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-6 border-t border-gray-100">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-green-50 text-green-700 flex items-center justify-center shrink-0">
                <DollarSign className="w-5 h-5" />
              </div>
              <div>
                <span className="block text-xs text-gray-500">Quanto custa?</span>
                <span className="text-sm font-bold text-gray-900">
                  {service.isFree ? "Gratuito" : `R$ ${service.costAmount?.toFixed(2)}`}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#1351B4] flex items-center justify-center shrink-0">
                <Clock className="w-5 h-5" />
              </div>
              <div>
                <span className="block text-xs text-gray-500">Prazo estimado</span>
                <span className="text-sm font-bold text-gray-900">
                  {service.averageDeadlineDays === 0
                    ? "Imediato"
                    : `${service.averageDeadlineDays} dias úteis`}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center shrink-0">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <span className="block text-xs text-gray-500">Documentos</span>
                <span className="text-sm font-bold text-gray-900">
                  {requiredDocuments.length} obrigatórios
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center shrink-0">
                <Calendar className="w-5 h-5" />
              </div>
              <div>
                <span className="block text-xs text-gray-500">Atendimento</span>
                <span className="text-sm font-bold text-gray-900">
                  {service.channel === "online" ? "100% Digital" : "Com Agendamento"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Layout Principal: 8 Blocos Oficiais + Painel Lateral de Ações */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Coluna da Esquerda: Os 8 Blocos da Ficha Orientativa */}
          <div className="lg:col-span-2 space-y-8">
            {/* Bloco 1: O que é */}
            <section className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <h2 className="text-xl font-bold text-gray-900 mb-3 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-[#1351B4]" />
                1. O que é este serviço?
              </h2>
              <p className="text-gray-700 leading-relaxed text-sm sm:text-base">
                {service.description}
              </p>
            </section>

            {/* Bloco 2: Quem tem direito */}
            <section className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <h2 className="text-xl font-bold text-gray-900 mb-3 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                2. Quem tem direito?
              </h2>
              <p className="text-gray-700 leading-relaxed text-sm sm:text-base">
                {service.whoCanUse}
              </p>
            </section>

            {/* Bloco 3: O que levar? (Documentos Obrigatórios vs Opcionais - RN-09) */}
            <section className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-[#1351B4]" />
                  3. O que levar? (Documentos necessários)
                </h2>
                <Link
                  href={`/servicos/${service.id}/guia`}
                  className="text-xs font-bold text-[#1351B4] hover:underline"
                >
                  Abrir checklist interativo
                </Link>
              </div>

              {/* Documentos Obrigatórios */}
              <div className="mb-6">
                <span className="inline-block text-xs font-bold uppercase tracking-wider text-red-700 bg-red-50 px-2.5 py-1 rounded-md mb-3">
                  Documentos Obrigatórios ({requiredDocuments.length})
                </span>
                <ul className="space-y-3">
                  {requiredDocuments.map((doc) => (
                    <li
                      key={doc.id}
                      className="p-3.5 bg-gray-50 rounded-xl border border-gray-200 flex items-start gap-3"
                    >
                      <CheckCircle2 className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold text-gray-900 text-sm">{doc.name}</span>
                        {doc.description && (
                          <p className="text-xs text-gray-600 mt-0.5">{doc.description}</p>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Documentos Opcionais */}
              {optionalDocuments.length > 0 && (
                <div>
                  <span className="inline-block text-xs font-bold uppercase tracking-wider text-amber-700 bg-amber-50 px-2.5 py-1 rounded-md mb-3">
                    Documentos Opcionais ou Específicos ({optionalDocuments.length})
                  </span>
                  <ul className="space-y-3">
                    {optionalDocuments.map((doc) => (
                      <li
                        key={doc.id}
                        className="p-3.5 bg-gray-50 rounded-xl border border-gray-200 flex items-start gap-3"
                      >
                        <HelpCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                        <div>
                          <span className="font-semibold text-gray-900 text-sm">{doc.name}</span>
                          {doc.description && (
                            <p className="text-xs text-gray-600 mt-0.5">{doc.description}</p>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </section>

            {/* Bloco 4: Como fazer? (Etapas) */}
            <section className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-[#1351B4]" />
                4. Como fazer? (Etapas do serviço)
              </h2>
              <ol className="relative border-l border-blue-200 ml-4 space-y-6">
                {service.steps.map((st) => (
                  <li key={st.stepOrder} className="ml-6">
                    <span className="absolute -left-3 flex items-center justify-center w-6 h-6 bg-[#1351B4] text-white rounded-full text-xs font-bold">
                      {st.stepOrder}
                    </span>
                    <h3 className="font-bold text-gray-900 text-sm sm:text-base">{st.title}</h3>
                    <p className="text-xs sm:text-sm text-gray-600 mt-1">{st.description}</p>
                  </li>
                ))}
              </ol>
            </section>

            {/* Bloco 5: Onde fazer? (Locais com mapa condicional - RN-10) */}
            <section className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <MapPin className="w-5 h-5 text-[#1351B4]" />
                5. Onde fazer? (Locais de atendimento)
              </h2>

              {units && units.length > 0 ? (
                <div className="space-y-4">
                  {units.map((unit) => (
                    <div
                      key={unit.id}
                      className="p-4 bg-gray-50 rounded-xl border border-gray-200"
                    >
                      <h3 className="font-bold text-gray-900 text-base">{unit.name}</h3>
                      <p className="text-xs sm:text-sm text-gray-600 mt-1">
                        {unit.street}, {unit.number} - {unit.neighborhood} — {unit.city}/{unit.state}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Expediente: {unit.openingHours}
                      </p>

                      {/* Mapa renderizado condicionalmente se latitude e longitude existirem (RN-10) */}
                      {unit.latitude && unit.longitude ? (
                        <div className="mt-3 overflow-hidden rounded-lg border border-gray-300">
                          <iframe
                            title={`Mapa de localização de ${unit.name}`}
                            width="100%"
                            height="200"
                            style={{ border: 0 }}
                            loading="lazy"
                            src={`https://maps.google.com/maps?q=${unit.latitude},${unit.longitude}&z=15&output=embed`}
                          />
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-600">
                  Este serviço é 100% digital e não exige deslocamento presencial.
                </p>
              )}
            </section>

            {/* Bloco 6: Quando? */}
            <section className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <h2 className="text-xl font-bold text-gray-900 mb-2 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-[#1351B4]" />
                6. Quando? (Horários e dias)
              </h2>
              <p className="text-gray-700 text-sm sm:text-base leading-relaxed">
                Atendimento presencial de segunda a sexta-feira, das 08h às 17h (exceto feriados
                municipais e estaduais). Solicitações online estão disponíveis 24 horas por dia, 7
                dias por semana no portal.
              </p>
            </section>

            {/* Bloco 7: Quanto custa? */}
            <section className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <h2 className="text-xl font-bold text-gray-900 mb-2 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-green-600" />
                7. Quanto custa?
              </h2>
              <p className="text-gray-700 text-sm sm:text-base leading-relaxed">
                {service.isFree ? (
                  <span className="font-semibold text-green-700">
                    Este serviço é totalmente gratuito para o cidadão.
                  </span>
                ) : (
                  <span>
                    Taxa oficial de <strong>R$ {service.costAmount?.toFixed(2)}</strong>, recolhida via DARE/Guia após a solicitação.
                  </span>
                )}
              </p>
            </section>

            {/* Bloco 8: Quanto tempo demora? */}
            <section className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <h2 className="text-xl font-bold text-gray-900 mb-2 flex items-center gap-2">
                <Clock className="w-5 h-5 text-[#1351B4]" />
                8. Quanto tempo demora? (Prazos)
              </h2>
              <p className="text-gray-700 text-sm sm:text-base leading-relaxed">
                Prazo estimado de conclusão:{" "}
                <strong>
                  {service.averageDeadlineDays === 0
                    ? "Imediato"
                    : `${service.averageDeadlineDays} dias úteis`}
                </strong>{" "}
                após a entrega de todos os documentos e validação presencial ou digital.
              </p>
            </section>
          </div>

          {/* Coluna da Direita: Card Flutuante com os 3 Botões Oficiais */}
          <div className="lg:col-span-1">
            <div className="sticky top-24 bg-white rounded-3xl p-6 shadow-lg border border-gray-200 space-y-6">
              <h2 className="text-lg font-bold text-gray-900">Ações para este serviço</h2>

              <div className="space-y-3">
                {/* Botão 1: Ver Passo-a-Passo */}
                <Link href={`/servicos/${service.id}/guia`} className="w-full block">
                  <Button
                    variant="secondary"
                    className="w-full justify-between py-3.5 text-sm font-bold border-2 border-[#1351B4] text-[#1351B4] hover:bg-blue-50"
                  >
                    <span>Ver Passo-a-Passo</span>
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>

                {/* Botão 2: Agendar Atendimento */}
                {service.channel !== "online" ? (
                  <Link href={`/servicos/${service.id}/agendamento`} className="w-full block">
                    <Button
                      variant="primary"
                      className="w-full justify-between py-3.5 text-sm font-bold shadow-md"
                    >
                      <span>Agendar Atendimento</span>
                      <Calendar className="w-4 h-4 ml-2" />
                    </Button>
                  </Link>
                ) : (
                  <Button
                    variant="primary"
                    className="w-full justify-between py-3.5 text-sm font-bold shadow-md"
                    onClick={() => alert("Este serviço é 100% digital. Redirecionando para formulário online...")}
                  >
                    <span>Iniciar Solicitação Online</span>
                    <ExternalLink className="w-4 h-4 ml-2" />
                  </Button>
                )}

                {/* Botão 3: Avaliar (Regra ADR-007 / D7 - Exibido apenas se flag ativa) */}
                {isReviewsFeatureEnabled && (
                  <Button
                    variant="tertiary"
                    className="w-full justify-center py-2 text-xs text-gray-600"
                    onClick={() => alert("Avaliação de serviço (v2.0).")}
                  >
                    Avaliar este serviço
                  </Button>
                )}
              </div>

              {/* Informações de Contato do Órgão */}
              <div className="pt-6 border-t border-gray-100 text-xs text-gray-500 space-y-2">
                <p>
                  <strong>Órgão:</strong> {service.agencyName}
                </p>
                <p>
                  <strong>Sigla:</strong> {service.agencyAcronym}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
