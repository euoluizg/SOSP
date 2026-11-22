"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  FileCheck,
  CheckCircle2,
  AlertCircle,
  ArrowLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Tag } from "@/components/ui/Tag";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  getAppointmentByProtocol,
  getOperationalAppointments,
  getServiceById,
  updateAppointmentStatus,
} from "@/services/apiClient";
import type { Appointment, ProblemDetails } from "@/types/api";

interface DocCheckItem {
  id: string;
  name: string;
}

const FALLBACK_DOCS: DocCheckItem[] = [
  { id: "doc1", name: "Documento Oficial com Foto (Original)" },
  { id: "doc2", name: "Comprovante de Residência Atualizado" },
  { id: "doc3", name: "Comprovante de Inscrição no CPF" },
];

function ServerAttendanceContent() {
  const searchParams = useSearchParams();
  const queryProtocol = searchParams.get("protocolo") || "";

  const [appointment, setAppointment] = useState<Appointment | null>(null);
  const [documents, setDocuments] = useState<DocCheckItem[]>(FALLBACK_DOCS);
  const [checkedDocs, setCheckedDocs] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [status, setStatus] = useState<"in_progress" | "completed" | "needs_doc">("in_progress");

  useEffect(() => {
    let active = true;
    async function load() {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        let target: Appointment | null = null;
        if (queryProtocol) {
          target = await getAppointmentByProtocol(queryProtocol);
        } else {
          const queue = await getOperationalAppointments();
          target =
            queue.find((a) => a.status === "confirmed") ||
            queue.find((a) => a.status === "scheduled") ||
            queue[0] ||
            null;
        }
        if (!active) return;
        setAppointment(target);
        if (target?.status === "completed") {
          setStatus("completed");
        }
        if (target?.serviceId) {
          const svc = await getServiceById(target.serviceId).catch(() => null);
          if (active && svc && svc.documents && svc.documents.length > 0) {
            setDocuments(svc.documents.map((d) => ({ id: d.id, name: d.name })));
          }
        }
      } catch (err: unknown) {
        if (!active) return;
        const problem = err as ProblemDetails;
        setErrorMessage(problem?.detail || "Não foi possível carregar o atendimento.");
      } finally {
        if (active) setIsLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [queryProtocol]);

  const handleToggle = (id: string) => {
    setCheckedDocs((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const allChecked = documents.length > 0 && documents.every((d) => Boolean(checkedDocs[d.id]));

  const handleComplete = async () => {
    if (!appointment) return;
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await updateAppointmentStatus(
        appointment.id,
        "completed",
        "Documentação conferida e atendimento finalizado no guichê."
      );
      setStatus("completed");
    } catch (err: unknown) {
      const problem = err as ProblemDetails;
      setErrorMessage(problem?.detail || "Erro ao finalizar o atendimento.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1000px] mx-auto space-y-6" aria-busy="true">
          <Skeleton className="h-28 w-full rounded-2xl" />
          <Skeleton className="h-64 w-full rounded-2xl" />
        </div>
      </div>
    );
  }

  if (!appointment) {
    return (
      <div className="min-h-screen bg-gray-50 py-16 px-4 text-center">
        <AlertCircle className="w-12 h-12 text-amber-500 mx-auto mb-3" />
        <h1 className="text-xl font-bold text-gray-900">Nenhum atendimento ativo selecionado</h1>
        <p className="text-sm text-gray-600 mt-1 max-w-md mx-auto">
          {errorMessage || "Selecione um protocolo na fila do painel do servidor para iniciar o atendimento."}
        </p>
        <Link href="/servidor/painel" className="mt-6 inline-block">
          <Button variant="primary">Ir para o Painel do Servidor</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[1000px] mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center text-xs text-gray-500 mb-6" aria-label="Breadcrumb">
          <Link href="/servidor/painel" className="hover:text-[#1351B4]">Painel do Servidor</Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <span className="font-semibold text-gray-900" aria-current="page">
            Atendimento de Protocolo (Tela 18 / RF-09)
          </span>
        </nav>

        {/* Topo */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200 mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Tag variant={status === "completed" ? "success" : "info"}>
                {status === "completed" ? "Atendimento Concluído" : "Em Atendimento"}
              </Tag>
              <span className="text-xs font-mono font-bold text-gray-500 bg-gray-100 px-2.5 py-0.5 rounded">
                Protocolo: {appointment.protocolNumber}
              </span>
            </div>
            <h1 className="text-2xl font-extrabold text-gray-900 mt-1">
              {appointment.serviceName}
            </h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Cidadão: <strong>{appointment.citizenName} (CPF {appointment.citizenCpfMasked})</strong> · {appointment.unitName}
            </p>
          </div>

          <Link href="/servidor/painel">
            <Button variant="secondary" className="text-xs">
              <ArrowLeft className="w-4 h-4 mr-1.5" />
              Voltar ao Painel
            </Button>
          </Link>
        </div>

        {errorMessage && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
            {errorMessage}
          </div>
        )}

        {status === "completed" ? (
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-green-200 text-center animate-fadeIn">
            <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="w-10 h-10" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Atendimento Finalizado com Sucesso!</h2>
            <p className="mt-2 text-sm text-gray-600 max-w-md mx-auto">
              A documentação do cidadão foi validada e o protocolo {appointment.protocolNumber} foi gravado como concluído no sistema.
            </p>
            <div className="mt-6">
              <Link href="/servidor/painel">
                <Button variant="primary">Retornar para a Fila</Button>
              </Link>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Checklist de Documentação Presencial */}
            <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <h2 className="text-lg font-bold text-gray-900 mb-2">
                Conferência de Documentos Físicos Apresentados
              </h2>
              <p className="text-xs text-gray-500 mb-6">
                Marque cada documento original verificado pelo atendente no guichê presencial.
              </p>

              <div className="space-y-3">
                {documents.map((doc) => {
                  const isChecked = Boolean(checkedDocs[doc.id]);
                  return (
                    <div
                      key={doc.id}
                      onClick={() => handleToggle(doc.id)}
                      className={`p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between select-none ${
                        isChecked
                          ? "bg-green-50/60 border-green-300"
                          : "bg-gray-50 hover:bg-gray-100/70 border-gray-200"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <FileCheck
                          className={`w-5 h-5 ${
                            isChecked ? "text-green-600" : "text-gray-400"
                          }`}
                        />
                        <span className="text-sm font-semibold text-gray-900">{doc.name}</span>
                      </div>
                      <span
                        className={`text-xs font-bold px-2.5 py-1 rounded-md ${
                          isChecked
                            ? "bg-green-100 text-green-800"
                            : "bg-gray-200 text-gray-600"
                        }`}
                      >
                        {isChecked ? "Conferido" : "Pendente"}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Ações do Atendente */}
            <div className="flex flex-col sm:flex-row justify-end gap-3 pt-2">
              <Button
                variant="primary"
                onClick={handleComplete}
                disabled={!allChecked || isSubmitting}
                isLoading={isSubmitting}
                className="px-8 shadow-md"
              >
                <CheckCircle2 className="w-4 h-4 mr-2" />
                Concluir Atendimento
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ServerAttendancePage() {
  return (
    <Suspense fallback={<div className="max-w-[1000px] mx-auto py-10 px-4"><Skeleton className="h-40 w-full rounded-2xl" /></div>}>
      <ServerAttendanceContent />
    </Suspense>
  );
}

