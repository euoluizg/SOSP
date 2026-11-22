"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  FileText,
  Calendar,
  Clock,
  MapPin,
  CheckCircle2,
  AlertCircle,
  XCircle,
  ChevronRight,
  ArrowLeft,
  Printer,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Tag } from "@/components/ui/Tag";
import { Skeleton } from "@/components/ui/Skeleton";
import { CriticalConfirmationModal } from "@/components/ui/CriticalConfirmationModal";
import { getAppointmentByProtocol, cancelAppointment } from "@/services/apiClient";
import type { Appointment } from "@/types/api";

export default function ProtocolDetailPage() {
  const params = useParams();
  const router = useRouter();
  const protocol = params?.protocol as string;

  const [appointment, setAppointment] = useState<Appointment | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);
  const [isCanceling, setIsCanceling] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAppointment() {
      setIsLoading(true);
      try {
        const data = await getAppointmentByProtocol(protocol);
        setAppointment(data);
      } catch (err) {
        console.error("Erro ao carregar protocolo:", err);
      } finally {
        setIsLoading(false);
      }
    }
    if (protocol) {
      loadAppointment();
    }
  }, [protocol]);

  const handleCancelClick = () => {
    if (!appointment) return;
    // Validação de 24h antes (RN-22)
    const appDate = new Date(`${appointment.scheduledDate}T${appointment.scheduledTime}:00`);
    const now = new Date();
    const diffHours = (appDate.getTime() - now.getTime()) / (1000 * 60 * 60);

    if (diffHours < 24) {
      setCancelError(
        "Conforme a regra RN-22, cancelamentos só podem ser realizados com antecedência mínima de 24 horas."
      );
      return;
    }

    setIsCancelModalOpen(true);
  };

  const handleConfirmCancel = async () => {
    if (!appointment) return;
    setIsCanceling(true);
    try {
      await cancelAppointment(appointment.id, "Cancelado pelo cidadão na página de acompanhamento.");
      setAppointment((prev) => (prev ? { ...prev, status: "cancelled" } : null));
      setIsCancelModalOpen(false);
    } catch (err) {
      console.error("Erro ao cancelar:", err);
    } finally {
      setIsCanceling(false);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-[1000px] mx-auto py-10 px-4">
        <Skeleton className="h-6 w-48 mb-4" />
        <Skeleton className="h-10 w-3/4 mb-6" />
        <Skeleton className="h-60 w-full rounded-2xl mb-6" />
        <Skeleton className="h-40 w-full rounded-2xl" />
      </div>
    );
  }

  if (!appointment) {
    return (
      <div className="max-w-md mx-auto py-20 px-4 text-center">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-gray-900">Protocolo não encontrado</h2>
        <p className="mt-2 text-sm text-gray-600">
          O protocolo <strong>{protocol}</strong> não existe ou não pertence ao seu usuário (STRIDE).
        </p>
        <Link href="/cidadao/meus-agendamentos" className="mt-6 inline-block">
          <Button variant="primary">Voltar para meus agendamentos</Button>
        </Link>
      </div>
    );
  }

  const isCancelled = appointment.status === "cancelled";
  const isCompleted = appointment.status === "completed";

  // Linha do tempo dos 4 estágios do ciclo de atendimento
  const timelineStages = [
    {
      title: "Agendamento Realizado",
      desc: "Protocolo registrado no SOSP e vaga reservada com sucesso.",
      isDone: true,
      isCurrent: appointment.status === "scheduled" || appointment.status === "confirmed",
    },
    {
      title: "Triagem e Documentação",
      desc: "Recepção na unidade e verificação dos documentos obrigatórios.",
      isDone: isCompleted,
      isCurrent: false,
    },
    {
      title: "Atendimento Presencial",
      desc: "Coleta biométrica, foto ou conferência pelo servidor público.",
      isDone: isCompleted,
      isCurrent: false,
    },
    {
      title: "Conclusão do Serviço",
      desc: "Emissão e entrega do documento ou finalização do processo.",
      isDone: isCompleted,
      isCurrent: isCompleted,
    },
  ];

  const formatStatus = (status: Appointment["status"]) => {
    switch (status) {
      case "scheduled":
        return { label: "Agendado", variant: "info" as const };
      case "confirmed":
        return { label: "Confirmado", variant: "success" as const };
      case "completed":
        return { label: "Concluído", variant: "success" as const };
      case "cancelled":
        return { label: "Cancelado", variant: "danger" as const };
      case "no_show":
        return { label: "Não Compareceu", variant: "warning" as const };
    }
  };

  const statusMeta = formatStatus(appointment.status);

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[1000px] mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center text-xs text-gray-500 mb-6 print:hidden" aria-label="Breadcrumb">
          <Link href="/" className="hover:text-[#1351B4]">Início</Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <Link href="/cidadao/meus-agendamentos" className="hover:text-[#1351B4]">Meus Agendamentos</Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <span className="font-semibold text-gray-900" aria-current="page">
            Protocolo {appointment.protocolNumber}
          </span>
        </nav>

        {/* Topo com Ações */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8 print:hidden">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Tag variant={statusMeta.variant}>{statusMeta.label}</Tag>
              <span className="text-xs text-gray-500">
                Criado em {new Date(appointment.createdAt).toLocaleDateString("pt-BR")}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900">
              Protocolo {appointment.protocolNumber}
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Serviço: <strong>{appointment.serviceName}</strong> • {appointment.agencyName}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="secondary" onClick={() => window.print()} className="text-xs">
              <Printer className="w-4 h-4 mr-1.5" />
              Imprimir
            </Button>
            {!isCancelled && !isCompleted && (
              <Button variant="danger" onClick={handleCancelClick} className="text-xs">
                Cancelar Atendimento
              </Button>
            )}
          </div>
        </div>

        {cancelError && (
          <div className="mb-6 p-4 bg-amber-50 border-l-4 border-amber-500 rounded-md flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <p className="text-sm text-amber-800">{cancelError}</p>
          </div>
        )}

        {/* Linha do Tempo Visual dos 4 Estágios (Screen 15 / W15) */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200 mb-8">
          <h2 className="text-lg font-bold text-gray-900 mb-6">
            Linha do Tempo de Acompanhamento
          </h2>

          {isCancelled ? (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
              <XCircle className="w-6 h-6 text-red-600 shrink-0 mt-0.5" />
              <div>
                <h3 className="font-bold text-red-900 text-sm">Atendimento Cancelado</h3>
                <p className="text-xs text-red-700 mt-1">
                  Este agendamento foi cancelado e a vaga liberada no sistema.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {timelineStages.map((stage, idx) => (
                <div key={idx} className="flex gap-4 items-start">
                  <div
                    className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm shrink-0 ${
                      stage.isDone
                        ? "bg-green-600 text-white"
                        : stage.isCurrent
                        ? "bg-[#1351B4] text-white ring-4 ring-blue-100"
                        : "bg-gray-200 text-gray-500"
                    }`}
                  >
                    {stage.isDone ? (
                      <CheckCircle2 className="w-5 h-5" />
                    ) : (
                      idx + 1
                    )}
                  </div>
                  <div className="flex-1 pb-4 border-b border-gray-100 last:border-none">
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-gray-900 text-sm sm:text-base">
                        {stage.title}
                      </h3>
                      {stage.isCurrent && (
                        <span className="text-[10px] uppercase font-bold bg-blue-100 text-[#1351B4] px-2 py-0.5 rounded-full">
                          Etapa Atual
                        </span>
                      )}
                    </div>
                    <p className="text-xs sm:text-sm text-gray-600 mt-1">{stage.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detalhes do Agendamento */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Informações da Unidade e Horário */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
            <h2 className="text-base font-bold text-gray-900 mb-4 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-[#1351B4]" />
              Local e Horário Marcado
            </h2>
            <div className="space-y-2 text-sm text-gray-700">
              <p>
                <strong>Unidade:</strong> {appointment.unitName}
              </p>
              <p>
                <strong>Endereço:</strong> {appointment.unitAddress}
              </p>
              <p>
                <strong>Data Marcada:</strong> {appointment.scheduledDate.split("-").reverse().join("/")}
              </p>
              <p>
                <strong>Horário do Atendimento:</strong> {appointment.scheduledTime} (30 min)
              </p>
            </div>
          </div>

          {/* Orientações para o Cidadão */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
            <h2 className="text-base font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Info className="w-4 h-4 text-[#1351B4]" />
              Instruções de Comparecimento
            </h2>
            <ul className="space-y-2 text-xs sm:text-sm text-gray-600">
              <li>• Apresente este protocolo ou comprovante impresso na recepção.</li>
              <li>• Chegue com no mínimo 15 minutos de antecedência.</li>
              <li>• Apresente todos os documentos originais exigidos pelo serviço.</li>
              <li>• O não comparecimento sem cancelamento prévio é registrado no sistema.</li>
            </ul>
          </div>
        </div>

        {/* Voltar */}
        <div className="flex justify-start print:hidden">
          <Link href="/cidadao/meus-agendamentos">
            <Button variant="secondary">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Voltar para Meus Agendamentos
            </Button>
          </Link>
        </div>
      </div>

      {/* Modal de Cancelamento */}
      <CriticalConfirmationModal
        isOpen={isCancelModalOpen}
        onClose={() => setIsCancelModalOpen(false)}
        onConfirm={handleConfirmCancel}
        isLoading={isCanceling}
        title="Cancelar Atendimento"
        description={`Tem certeza que deseja cancelar o protocolo ${appointment.protocolNumber}? A vaga no horário ${appointment.scheduledTime} do dia ${appointment.scheduledDate.split("-").reverse().join("/")} será liberada.`}
        confirmText="Sim, Cancelar Atendimento"
        cancelText="Voltar"
        isDestructive={true}
      />
    </div>
  );
}
