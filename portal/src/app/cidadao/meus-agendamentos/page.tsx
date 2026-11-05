"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Calendar,
  Clock,
  MapPin,
  ChevronRight,
  Plus,
  Eye,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Tag } from "@/components/ui/Tag";
import { Skeleton } from "@/components/ui/Skeleton";
import { CriticalConfirmationModal } from "@/components/ui/CriticalConfirmationModal";
import { getCitizenAppointments, cancelAppointment } from "@/services/apiClient";
import type { Appointment } from "@/types/api";

export default function MyAppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [cancelingAppointment, setCancelingAppointment] = useState<Appointment | null>(null);
  const [isCanceling, setIsCanceling] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAppointments() {
      setIsLoading(true);
      try {
        const data = await getCitizenAppointments("citizen-001");
        setAppointments(data);
      } catch (err) {
        console.error("Erro ao carregar agendamentos:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadAppointments();
  }, []);

  const handleCancelClick = (appointment: Appointment) => {
    // Validação da regra RN-22 (Cancelamento até 24h antes)
    const appDate = new Date(`${appointment.scheduledDate}T${appointment.scheduledTime}:00`);
    const now = new Date();
    const diffHours = (appDate.getTime() - now.getTime()) / (1000 * 60 * 60);

    if (diffHours < 24) {
      setCancelError(
        "Conforme a regra RN-22, o cancelamento só pode ser realizado com antecedência mínima de 24 horas do atendimento."
      );
      setTimeout(() => setCancelError(null), 6000);
      return;
    }

    setCancelingAppointment(appointment);
  };

  const handleConfirmCancel = async () => {
    if (!cancelingAppointment) return;

    setIsCanceling(true);
    try {
      await cancelAppointment(
        cancelingAppointment.id,
        "Cancelado pelo cidadão através do portal"
      );
      setAppointments((prev) =>
        prev.map((app) =>
          app.id === cancelingAppointment.id
            ? { ...app, status: "cancelled" as const }
            : app
        )
      );
      setCancelingAppointment(null);
    } catch (err) {
      console.error("Erro ao cancelar agendamento:", err);
    } finally {
      setIsCanceling(false);
    }
  };

  const activeAppointments = appointments.filter(
    (app) => app.status === "scheduled" || app.status === "confirmed"
  );
  const historyAppointments = appointments.filter(
    (app) => app.status !== "scheduled" && app.status !== "confirmed"
  );

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

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[1100px] mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center text-xs text-gray-500 mb-6" aria-label="Breadcrumb">
          <Link href="/" className="hover:text-[#1351B4]">Início</Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <span className="font-semibold text-gray-900" aria-current="page">
            Meus Agendamentos e Protocolos
          </span>
        </nav>

        {/* Topo */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900">
              Meus Agendamentos
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Acompanhe o status dos seus atendimentos e gerencie suas solicitações no SOSP.
            </p>
          </div>
          <Link href="/servicos">
            <Button variant="primary" className="text-sm font-semibold shadow-md">
              <Plus className="w-4 h-4 mr-2" />
              Novo Agendamento
            </Button>
          </Link>
        </div>

        {cancelError && (
          <div className="mb-6 p-4 bg-amber-50 border-l-4 border-amber-500 rounded-md flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <p className="text-sm text-amber-800">{cancelError}</p>
          </div>
        )}

        {/* Lista de Agendamentos Ativos */}
        <div className="space-y-6 mb-12">
          <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-[#1351B4]" />
            Próximos Atendimentos ({activeAppointments.length})
          </h2>

          {isLoading ? (
            <div className="space-y-4">
              {[1, 2].map((idx) => (
                <div key={idx} className="bg-white p-6 rounded-2xl border border-gray-200">
                  <Skeleton className="h-6 w-48 mb-3" />
                  <Skeleton className="h-4 w-72 mb-4" />
                  <Skeleton className="h-10 w-full rounded-xl" />
                </div>
              ))}
            </div>
          ) : activeAppointments.length === 0 ? (
            <div className="bg-white rounded-2xl p-8 border border-gray-200 text-center shadow-sm">
              <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <h3 className="text-base font-bold text-gray-900">Você não possui agendamentos ativos</h3>
              <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
                Quando você agendar um atendimento para emissão de documentos ou consultas, ele aparecerá aqui.
              </p>
              <Link href="/servicos" className="mt-5 inline-block">
                <Button variant="secondary" className="text-xs">
                  Consultar Catálogo de Serviços
                </Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {activeAppointments.map((app) => {
                const statusMeta = formatStatus(app.status);
                return (
                  <div
                    key={app.id}
                    className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200 hover:border-blue-300 transition-all"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-100">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <Tag variant={statusMeta.variant}>{statusMeta.label}</Tag>
                          <span className="text-xs font-mono font-bold text-gray-500 bg-gray-100 px-2.5 py-0.5 rounded">
                            Protocolo: {app.protocolNumber}
                          </span>
                        </div>
                        <h3 className="text-lg font-bold text-gray-900">{app.serviceName}</h3>
                        <p className="text-xs text-gray-500">
                          Órgão: {app.agencyName}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <Link href={`/cidadao/protocolos/${app.protocolNumber}`}>
                          <Button variant="secondary" className="text-xs">
                            <Eye className="w-3.5 h-3.5 mr-1.5" />
                            Linha do Tempo
                          </Button>
                        </Link>
                        <Button
                          variant="danger"
                          className="text-xs"
                          onClick={() => handleCancelClick(app)}
                        >
                          Cancelar
                        </Button>
                      </div>
                    </div>

                    {/* Informações de Local e Data */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-4 text-xs text-gray-600">
                      <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-gray-400 shrink-0" />
                        <span>{app.unitName}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-gray-400 shrink-0" />
                        <span>Data: <strong>{app.scheduledDate.split("-").reverse().join("/")}</strong></span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-gray-400 shrink-0" />
                        <span>Horário: <strong>{app.scheduledTime}</strong></span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Histórico Anterior */}
        {historyAppointments.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-gray-900">
              Histórico de Atendimentos Anteriores
            </h2>

            <div className="space-y-3">
              {historyAppointments.map((app) => {
                const statusMeta = formatStatus(app.status);
                return (
                  <div
                    key={app.id}
                    className="bg-white rounded-xl p-5 border border-gray-200 opacity-80"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <Tag variant={statusMeta.variant}>{statusMeta.label}</Tag>
                          <span className="text-xs font-mono text-gray-500">
                            {app.protocolNumber}
                          </span>
                        </div>
                        <h4 className="font-semibold text-gray-900 text-sm">{app.serviceName}</h4>
                        <p className="text-xs text-gray-500">
                          {app.unitName} • {app.scheduledDate.split("-").reverse().join("/")} às {app.scheduledTime}
                        </p>
                      </div>

                      <Link href={`/cidadao/protocolos/${app.protocolNumber}`}>
                        <Button variant="secondary" className="text-xs">
                          Ver Protocolo
                        </Button>
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Modal de Cancelamento Crítico */}
      <CriticalConfirmationModal
        isOpen={Boolean(cancelingAppointment)}
        onClose={() => setCancelingAppointment(null)}
        onConfirm={handleConfirmCancel}
        isLoading={isCanceling}
        title="Cancelar Agendamento"
        description={`Deseja realmente cancelar o atendimento para ${cancelingAppointment?.serviceName} no dia ${cancelingAppointment?.scheduledDate.split("-").reverse().join("/")}? Essa vaga será disponibilizada para outros cidadãos.`}
        confirmText="Sim, Cancelar Agendamento"
        cancelText="Não, Manter Agendamento"
        isDestructive={true}
      />
    </div>
  );
}
