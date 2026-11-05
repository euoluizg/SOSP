"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  Calendar as CalendarIcon,
  Clock,
  MapPin,
  CheckCircle2,
  AlertCircle,
  ChevronRight,
  ArrowRight,
  ArrowLeft,
  Printer,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { Skeleton } from "@/components/ui/Skeleton";
import { getServiceById, getUnits, getAppointmentSlots, createAppointment } from "@/services/apiClient";
import type { Service, Unit, AppointmentSlot, Appointment } from "@/types/api";

export default function AppointmentSchedulingPage() {
  const params = useParams();
  const router = useRouter();
  const serviceId = params?.id as string;

  const [service, setService] = useState<Service | null>(null);
  const [units, setUnits] = useState<Unit[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Etapa do fluxo (1: Seleção de Unidade/Data/Slot, 2: Revisão, 3: Sucesso/Comprovante)
  const [step, setStep] = useState<1 | 2 | 3>(1);

  // Estados da seleção
  const [selectedUnitId, setSelectedUnitId] = useState("");
  const [selectedDate, setSelectedDate] = useState("");
  const [availableSlots, setAvailableSlots] = useState<AppointmentSlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<AppointmentSlot | null>(null);
  const [isSearchingSlots, setIsSearchingSlots] = useState(false);

  // Dados do cidadão mockado para agendamento
  const citizenInfo = {
    name: "Cidadão de Testes",
    cpf: "123.456.789-00",
    email: "cidadao@exemplo.com",
    phone: "(82) 98888-7777",
  };

  // Resultado do agendamento confirmado
  const [confirmedAppointment, setConfirmedAppointment] = useState<Appointment | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const data = await getServiceById(serviceId);
        setService(data);
        if (data) {
          const loadedUnits = await getUnits(data.agencyId);
          setUnits(loadedUnits);
          if (loadedUnits.length > 0) {
            setSelectedUnitId(loadedUnits[0].id);
          }
        }
      } catch (err) {
        console.error("Erro ao carregar serviço:", err);
      } finally {
        setIsLoading(false);
      }
    }
    if (serviceId) {
      loadData();
    }
  }, [serviceId]);

  // Busca slots de 30 minutos quando a data é selecionada (RN-18, RN-19)
  useEffect(() => {
    async function fetchSlots() {
      if (!serviceId || !selectedUnitId || !selectedDate) return;
      setIsSearchingSlots(true);
      setSelectedSlot(null);
      setError(null);
      try {
        const slots = await getAppointmentSlots(selectedUnitId, selectedDate);
        setAvailableSlots(slots);
      } catch (err) {
        console.error("Erro ao buscar horários:", err);
        setError("Não foi possível carregar os horários para esta data.");
      } finally {
        setIsSearchingSlots(false);
      }
    }
    fetchSlots();
  }, [serviceId, selectedUnitId, selectedDate]);

  // Gera lista de datas disponíveis (apenas dias úteis a partir de amanhã, RN-19)
  const availableDates = React.useMemo(() => {
    const dates: { dateStr: string; label: string }[] = [];
    const now = new Date();
    let current = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);

    while (dates.length < 14) {
      const dayOfWeek = current.getDay();
      // 0 = Domingo, 6 = Sábado (Desconta fins de semana - RN-19)
      if (dayOfWeek !== 0 && dayOfWeek !== 6) {
        const yyyy = current.getFullYear();
        const mm = String(current.getMonth() + 1).padStart(2, "0");
        const dd = String(current.getDate()).padStart(2, "0");
        const dateStr = `${yyyy}-${mm}-${dd}`;

        const formatter = new Intl.DateTimeFormat("pt-BR", {
          weekday: "short",
          day: "2-digit",
          month: "2-digit",
        });
        dates.push({
          dateStr,
          label: formatter.format(current),
        });
      }
      current.setDate(current.getDate() + 1);
    }
    return dates;
  }, []);

  const handleProceedToReview = () => {
    if (!selectedUnitId) {
      setError("Selecione uma unidade de atendimento.");
      return;
    }
    if (!selectedDate) {
      setError("Selecione uma data para o atendimento.");
      return;
    }
    if (!selectedSlot) {
      setError("Selecione um horário de 30 minutos disponível.");
      return;
    }
    setError(null);
    setStep(2);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleConfirmAppointment = async () => {
    if (!selectedSlot || !service) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const appointment = await createAppointment({
        serviceId: service.id,
        unitId: selectedUnitId,
        scheduledDate: selectedDate,
        scheduledTime: selectedSlot.startsAt,
      });

      setConfirmedAppointment(appointment);
      setStep(3); // Tela de Comprovante Oficial (10 / W10)
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err: any) {
      console.error("Erro ao confirmar agendamento:", err);
      setError(
        err?.message ||
          "Não foi possível confirmar seu agendamento. Verifique se você já possui um agendamento ativo para este serviço (RN-21)."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-[1000px] mx-auto py-10 px-4">
        <Skeleton className="h-8 w-60 mb-4" />
        <Skeleton className="h-5 w-96 mb-8" />
        <Skeleton className="h-80 w-full rounded-2xl" />
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

  const selectedUnit = units.find((u) => u.id === selectedUnitId);

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[1000px] mx-auto">
        {/* Breadcrumb */}
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
            Agendamento Presencial
          </span>
        </nav>

        {/* Stepper Superior */}
        <div className="mb-8 print:hidden">
          <div className="flex items-center justify-between max-w-lg mx-auto">
            <div className="flex flex-col items-center">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm ${
                  step >= 1 ? "bg-[#1351B4] text-white" : "bg-gray-200 text-gray-600"
                }`}
              >
                1
              </div>
              <span className="text-xs font-semibold mt-1.5 text-gray-700">Data e Horário</span>
            </div>
            <div className={`flex-1 h-0.5 mx-3 ${step >= 2 ? "bg-[#1351B4]" : "bg-gray-200"}`} />
            <div className="flex flex-col items-center">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm ${
                  step >= 2 ? "bg-[#1351B4] text-white" : "bg-gray-200 text-gray-600"
                }`}
              >
                2
              </div>
              <span className="text-xs font-semibold mt-1.5 text-gray-700">Revisão</span>
            </div>
            <div className={`flex-1 h-0.5 mx-3 ${step === 3 ? "bg-[#1351B4]" : "bg-gray-200"}`} />
            <div className="flex flex-col items-center">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm ${
                  step === 3 ? "bg-green-600 text-white" : "bg-gray-200 text-gray-600"
                }`}
              >
                3
              </div>
              <span className="text-xs font-semibold mt-1.5 text-gray-700">Comprovante</span>
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-md flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* ETAPA 1: Seleção de Unidade, Data e Slot de 30 min (RN-18, RN-19) */}
        {step === 1 && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <h2 className="text-xl font-bold text-gray-900 mb-1">
                Agendar: {service.name}
              </h2>
              <p className="text-sm text-gray-600 mb-6">
                Escolha onde e quando deseja ser atendido. Todos os atendimentos possuem duração de 30 minutos.
              </p>

              {/* 1. Escolha da Unidade */}
              <div className="mb-6">
                <Select
                  label="Unidade de Atendimento Presencial"
                  id="select-unit"
                  value={selectedUnitId}
                  onChange={(e) => setSelectedUnitId(e.target.value)}
                  options={
                    units.map((u) => ({
                      value: u.id,
                      label: `${u.name} — ${u.neighborhood}, ${u.city}`,
                    }))
                  }
                  helperText={
                    selectedUnit
                      ? `Endereço: ${selectedUnit.street}, ${selectedUnit.number} | Horário: ${selectedUnit.openingHours}`
                      : ""
                  }
                />
              </div>

              {/* 2. Escolha da Data (Dias úteis - RN-19) */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Escolha uma Data Disponível
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2">
                  {availableDates.map(({ dateStr, label }) => {
                    const isSelected = selectedDate === dateStr;
                    return (
                      <button
                        key={dateStr}
                        type="button"
                        onClick={() => setSelectedDate(dateStr)}
                        className={`p-3 rounded-xl border text-center transition-all focus:outline-none focus:ring-2 focus:ring-[#1351B4] ${
                          isSelected
                            ? "bg-[#1351B4] text-white border-[#1351B4] shadow-md font-bold"
                            : "bg-gray-50 hover:bg-blue-50/50 border-gray-200 text-gray-900"
                        }`}
                      >
                        <span className="block text-xs uppercase opacity-80">
                          {label.split(",")[0]}
                        </span>
                        <span className="block text-sm font-extrabold mt-0.5">
                          {label.split(",")[1]?.trim() || label}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 3. Escolha do Slot de 30 minutos (RN-18) */}
              {selectedDate && (
                <div className="pt-4 border-t border-gray-100">
                  <div className="flex items-center justify-between mb-3">
                    <label className="block text-sm font-semibold text-gray-700">
                      Horários de 30 minutos disponíveis (Regra RN-18)
                    </label>
                    <span className="text-xs text-gray-500">
                      {availableSlots.filter((s) => s.isAvailable).length} horários livres
                    </span>
                  </div>

                  {isSearchingSlots ? (
                    <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
                      {[1, 2, 3, 4, 5, 6].map((idx) => (
                        <Skeleton key={idx} className="h-12 rounded-xl" />
                      ))}
                    </div>
                  ) : availableSlots.length === 0 ? (
                    <p className="text-sm text-gray-500 italic p-4 bg-gray-50 rounded-xl text-center">
                      Nenhum horário disponível para esta data. Por favor, selecione outro dia.
                    </p>
                  ) : (
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5">
                      {availableSlots.map((slot) => {
                        const isSelected = selectedSlot?.startsAt === slot.startsAt;
                        const spotsLeft = slot.capacity - slot.bookedCount;
                        return (
                          <button
                            key={slot.startsAt}
                            type="button"
                            disabled={!slot.isAvailable}
                            onClick={() => setSelectedSlot(slot)}
                            className={`py-2.5 px-3 rounded-xl border text-center transition-all ${
                              !slot.isAvailable
                                ? "bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed line-through"
                                : isSelected
                                ? "bg-[#1351B4] text-white border-[#1351B4] shadow-md font-bold"
                                : "bg-white hover:border-[#1351B4] hover:bg-blue-50/40 border-gray-300 text-gray-900"
                            }`}
                          >
                            <span className="block text-sm font-bold">{slot.startsAt}</span>
                            <span className="block text-[10px] opacity-75">
                              {slot.isAvailable ? `${spotsLeft} vagas` : "Lotado"}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Ação de Avançar */}
            <div className="flex justify-end gap-3">
              <Link href={`/servicos/${service.id}`}>
                <Button variant="secondary">Cancelar</Button>
              </Link>
              <Button
                variant="primary"
                onClick={handleProceedToReview}
                disabled={!selectedSlot}
                className="px-8 shadow-md"
              >
                Avançar para Revisão
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {/* ETAPA 2: Revisão dos Dados antes da Confirmação Atômica */}
        {step === 2 && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <h2 className="text-xl font-bold text-gray-900 mb-2">
                Revisão do Agendamento
              </h2>
              <p className="text-sm text-gray-600 mb-6">
                Confira todas as informações antes de emitir o protocolo oficial.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Dados do Cidadão */}
                <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                  <span className="text-xs font-bold text-gray-500 uppercase tracking-wider block mb-3">
                    Identificação do Cidadão
                  </span>
                  <div className="space-y-1.5 text-sm">
                    <p><strong>Nome:</strong> {citizenInfo.name}</p>
                    <p><strong>CPF:</strong> {citizenInfo.cpf}</p>
                    <p><strong>E-mail:</strong> {citizenInfo.email}</p>
                    <p><strong>Telefone:</strong> {citizenInfo.phone}</p>
                  </div>
                </div>

                {/* Dados do Atendimento */}
                <div className="p-4 bg-blue-50/60 rounded-xl border border-blue-200">
                  <span className="text-xs font-bold text-[#1351B4] uppercase tracking-wider block mb-3">
                    Detalhes da Reserva
                  </span>
                  <div className="space-y-1.5 text-sm">
                    <p><strong>Serviço:</strong> {service.name}</p>
                    <p><strong>Órgão:</strong> {service.agencyName}</p>
                    <p><strong>Unidade:</strong> {selectedUnit?.name}</p>
                    <p><strong>Data:</strong> {selectedDate.split("-").reverse().join("/")}</p>
                    <p>
                      <strong>Horário:</strong> {selectedSlot?.startsAt} às {selectedSlot?.endsAt} (30 min)
                    </p>
                  </div>
                </div>
              </div>

              {/* Aviso da Regra de Cancelamento (RN-22) */}
              <div className="mt-6 p-4 bg-amber-50 rounded-xl border border-amber-200 flex items-start gap-3">
                <Info className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div className="text-xs text-amber-900 leading-relaxed">
                  <strong>Atenção (Regra RN-22):</strong> Cancelamentos ou remarcações podem ser
                  realizados através do portal com até <strong>24 horas de antecedência</strong> do
                  horário marcado. Caso não possa comparecer, cancele para liberar a vaga para outro cidadão.
                </div>
              </div>
            </div>

            {/* Ações */}
            <div className="flex justify-between gap-3">
              <Button variant="secondary" onClick={() => setStep(1)}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Voltar e Alterar
              </Button>
              <Button
                variant="primary"
                onClick={handleConfirmAppointment}
                isLoading={isSubmitting}
                className="px-8 shadow-md"
              >
                Confirmar Agendamento e Emitir Protocolo
                <CheckCircle2 className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {/* ETAPA 3: Comprovante Oficial com Protocolo AAAAMMDD-XXXX (Screen 10 / W10) */}
        {step === 3 && confirmedAppointment && (
          <div className="space-y-6">
            <div className="bg-white rounded-3xl p-6 sm:p-10 shadow-xl border border-green-200 text-center animate-fadeIn">
              <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="w-10 h-10" />
              </div>

              <h2 className="text-2xl sm:text-3xl font-extrabold text-gray-900">
                Agendamento Confirmado!
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Seu atendimento presencial foi agendado com sucesso no SOSP.
              </p>

              {/* Caixa de Destaque do Protocolo AAAAMMDD-XXXX (RN-20) */}
              <div className="my-6 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-[#1351B4] rounded-2xl max-w-md mx-auto">
                <span className="text-xs font-bold uppercase tracking-wider text-[#1351B4]">
                  Número Oficial do Protocolo (RN-20)
                </span>
                <div className="text-3xl sm:text-4xl font-mono font-black text-gray-900 tracking-wider mt-1">
                  {confirmedAppointment.protocolNumber}
                </div>
                <span className="text-xs text-gray-500 block mt-2">
                  Guarde este número para apresentar na recepção ou consultar no portal
                </span>
              </div>

              {/* Informações Resumidas do Atendimento */}
              <div className="max-w-md mx-auto text-left bg-gray-50 p-5 rounded-2xl border border-gray-200 space-y-2 text-sm text-gray-800 mb-6">
                <p>
                  <strong>Serviço:</strong> {confirmedAppointment.serviceName}
                </p>
                <p>
                  <strong>Unidade:</strong> {confirmedAppointment.unitName}
                </p>
                <p>
                  <strong>Endereço:</strong> {confirmedAppointment.unitAddress}
                </p>
                <p>
                  <strong>Data:</strong> {confirmedAppointment.scheduledDate.split("-").reverse().join("/")}
                </p>
                <p>
                  <strong>Horário:</strong> {confirmedAppointment.scheduledTime}
                </p>
              </div>

              {/* Instruções Finais */}
              <div className="max-w-md mx-auto p-4 bg-blue-50 rounded-xl text-left text-xs text-blue-900 space-y-1 mb-8">
                <p className="font-bold">Orientações Importantes:</p>
                <p>• Chegue com pelo menos 15 minutos de antecedência.</p>
                <p>• Apresente documento oficial com foto e o protocolo acima.</p>
                <p>• Tenha todos os documentos originais do checklist em mãos.</p>
              </div>

              {/* Botões de Ação */}
              <div className="flex flex-col sm:flex-row gap-3 justify-center max-w-md mx-auto print:hidden">
                <Button
                  variant="secondary"
                  onClick={() => window.print()}
                  className="flex-1 justify-center"
                >
                  <Printer className="w-4 h-4 mr-2" />
                  Imprimir Comprovante
                </Button>
                <Link href="/cidadao/meus-agendamentos" className="flex-1">
                  <Button variant="primary" className="w-full justify-center shadow-md">
                    Ver Meus Agendamentos
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
