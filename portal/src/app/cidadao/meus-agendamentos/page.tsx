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
  LogIn,
  UserPlus,
  Search,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Tag } from "@/components/ui/Tag";
import { Skeleton } from "@/components/ui/Skeleton";
import { CriticalConfirmationModal } from "@/components/ui/CriticalConfirmationModal";
import { getCitizenAppointments, cancelAppointment } from "@/services/apiClient";
import type { Appointment } from "@/types/api";

export default function MyAppointmentsPage() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [citizenId, setCitizenId] = useState<string | null>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [cancelingAppointment, setCancelingAppointment] = useState<Appointment | null>(null);
  const [isCanceling, setIsCanceling] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);

  useEffect(() => {
    async function init() {
      setIsLoading(true);
      if (typeof window !== "undefined") {
        const token = localStorage.getItem("sosp_auth_token");
        const storedUser = localStorage.getItem("sosp_user");

        if (!token) {
          setIsAuthenticated(false);
          setIsLoading(false);
          return;
        }

        setIsAuthenticated(true);
        let id = "citizen-001";
        if (storedUser) {
          try {
            const parsed = JSON.parse(storedUser);
            if (parsed.id) id = parsed.id;
          } catch {
            // fallback id
          }
        }
        setCitizenId(id);

        try {
          const data = await getCitizenAppointments(id);
          setAppointments(data || []);
        } catch (err) {
          console.error("Erro ao carregar agendamentos:", err);
          setAppointments([]);
        } finally {
          setIsLoading(false);
        }
      }
    }
    init();
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
      default:
        return { label: "Pendente", variant: "warning" as const };
    }
  };

  // 1. Estado de Carregamento Inicial
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 py-10 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1200px] mx-auto space-y-6">
          <Skeleton className="h-8 w-64 mb-2" />
          <Skeleton className="h-4 w-96 mb-8" />
          <div className="space-y-4">
            <Skeleton className="h-32 w-full rounded-2xl" />
            <Skeleton className="h-32 w-full rounded-2xl" />
          </div>
        </div>
      </div>
    );
  }

  // 2. Seção 7.1: Visitante Não Autenticado
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[720px] mx-auto text-center space-y-8 bg-white p-8 sm:p-12 rounded-3xl border border-gray-200 shadow-xs">
          <div className="w-16 h-16 rounded-2xl bg-blue-50 text-[#1351B4] flex items-center justify-center mx-auto shadow-xs">
            <Calendar className="w-8 h-8" />
          </div>

          <div className="space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-[#1351B4] bg-blue-50 px-3 py-1 rounded-full">
              Área do Cidadão
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
              Seus agendamentos em um só lugar
            </h1>
            <p className="text-sm sm:text-base text-gray-600 max-w-lg mx-auto leading-relaxed">
              Entre na sua conta ou cadastre-se para visualizar, acompanhar e gerenciar seus
              agendamentos presenciais com total segurança.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <Link
              href="/login?redirect=/cidadao/meus-agendamentos"
              className="w-full sm:w-auto inline-flex items-center justify-center font-bold text-sm bg-[#1351B4] text-white hover:bg-[#0C326F] px-6 py-3.5 rounded-xl min-h-[44px] transition-colors shadow-xs"
            >
              <LogIn className="w-4 h-4 mr-2" />
              Entrar na minha conta
            </Link>
            <Link
              href="/cadastro"
              className="w-full sm:w-auto inline-flex items-center justify-center font-bold text-sm bg-gray-100 text-gray-800 hover:bg-gray-200 px-6 py-3.5 rounded-xl min-h-[44px] transition-colors"
            >
              <UserPlus className="w-4 h-4 mr-2" />
              Criar conta
            </Link>
          </div>

          <div className="pt-6 border-t border-gray-100 text-xs text-gray-500 flex items-center justify-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-500" />
            <span>Precisa apenas se orientar sobre documentos? </span>
            <Link href="/servicos" className="text-[#1351B4] font-bold hover:underline">
              Consulte os serviços públicos
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // 3. Seção 7.2: Cidadão Autenticado sem Agendamentos
  if (appointments.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[720px] mx-auto text-center space-y-6 bg-white p-8 sm:p-12 rounded-3xl border border-gray-200 shadow-xs">
          <div className="w-16 h-16 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto shadow-xs">
            <Calendar className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
              Você ainda não possui agendamentos
            </h1>
            <p className="text-sm sm:text-base text-gray-600 max-w-md mx-auto leading-relaxed">
              Encontre um serviço público e escolha um horário para realizar seu primeiro
              agendamento em uma das Centrais Já! de Alagoas.
            </p>
          </div>

          <div className="pt-4">
            <Link
              href="/servicos"
              className="inline-flex items-center justify-center font-bold text-sm bg-[#1351B4] text-white hover:bg-[#0C326F] px-8 py-3.5 rounded-xl min-h-[44px] transition-colors shadow-xs"
            >
              <Search className="w-4 h-4 mr-2" />
              Explorar serviços
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // 4. Seção 7.3: Cidadão Autenticado com Agendamentos
  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[1200px] mx-auto">
        {/* Cabeçalho da Página */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
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

          {activeAppointments.length === 0 ? (
            <div className="bg-white rounded-2xl p-8 border border-gray-200 text-center shadow-sm">
              <Calendar className="w-10 h-10 text-gray-400 mx-auto mb-2" />
              <h3 className="text-sm font-bold text-gray-900">Sem agendamentos futuros pendentes</h3>
              <p className="text-xs text-gray-500 mt-1">
                Você não possui nenhum atendimento marcado para os próximos dias.
              </p>
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
                        {app.status === "scheduled" && (
                          <Button
                            variant="danger"
                            className="text-xs"
                            onClick={() => handleCancelClick(app)}
                          >
                            Cancelar
                          </Button>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 text-xs text-gray-600">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-gray-400 shrink-0" />
                        <span>Data: <strong>{app.scheduledDate}</strong></span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-gray-400 shrink-0" />
                        <span>Horário: <strong>{app.scheduledTime}</strong></span>
                      </div>
                      <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-gray-400 shrink-0" />
                        <span className="truncate" title={app.unitAddress}>
                          Local: <strong>{app.unitName}</strong>
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Histórico de Agendamentos Anteriores */}
        {historyAppointments.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <Clock className="w-5 h-5 text-gray-400" />
              Histórico de Atendimentos ({historyAppointments.length})
            </h2>

            <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-xs divide-y divide-gray-100">
              {historyAppointments.map((app) => {
                const statusMeta = formatStatus(app.status);
                return (
                  <div key={app.id} className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-gray-50/50 transition-colors">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Tag variant={statusMeta.variant}>{statusMeta.label}</Tag>
                        <span className="text-xs font-mono text-gray-400">
                          {app.protocolNumber}
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-gray-800">{app.serviceName}</h4>
                      <p className="text-xs text-gray-500">
                        {app.unitName} · {app.scheduledDate} às {app.scheduledTime}
                      </p>
                    </div>

                    <Link href={`/cidadao/protocolos/${app.protocolNumber}`}>
                      <Button variant="secondary" className="text-xs py-1.5 px-3">
                        Ver Detalhes
                        <ChevronRight className="w-3.5 h-3.5 ml-1" />
                      </Button>
                    </Link>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Modal de Confirmação Crítica de Cancelamento (RN-22 / RN-40) */}
        <CriticalConfirmationModal
          isOpen={Boolean(cancelingAppointment)}
          onClose={() => setCancelingAppointment(null)}
          onConfirm={handleConfirmCancel}
          title="Cancelar Agendamento Presencial?"
          description={`Tem certeza que deseja cancelar o agendamento de "${cancelingAppointment?.serviceName}" marcado para o dia ${cancelingAppointment?.scheduledDate} às ${cancelingAppointment?.scheduledTime}? A vaga será liberada imediatamente para outro cidadão.`}
          confirmText="Sim, quero cancelar"
          cancelText="Não, manter agendamento"
          isDestructive={true}
          isLoading={isCanceling}
        />
      </div>
    </div>
  );
}
