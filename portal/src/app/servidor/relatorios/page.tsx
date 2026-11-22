"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  FileText,
  Download,
  BarChart3,
  Users,
  CheckCircle2,
  UserX,
  ArrowLeft,
  ChevronRight,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { getAppointmentsReport, createReportExport } from "@/services/apiClient";
import type { AppointmentsReportSummary, ProblemDetails } from "@/types/api";

function computeDateRange(period: string): { startDate: string; endDate: string } {
  const now = new Date();
  const end = now.toISOString().slice(0, 10);
  const start = new Date(now);
  if (period === "7days") {
    start.setDate(now.getDate() - 7);
  } else if (period === "30days") {
    start.setDate(now.getDate() - 30);
  } else if (period === "month") {
    start.setDate(1);
  } else {
    start.setMonth(0, 1);
  }
  return { startDate: start.toISOString().slice(0, 10), endDate: end };
}

export default function ReportsPage() {
  const [period, setPeriod] = useState("30days");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<AppointmentsReportSummary | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const loadReport = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const range = computeDateRange(period);
      const data = await getAppointmentsReport(range);
      setReport(data);
    } catch (err: unknown) {
      const problem = err as ProblemDetails;
      setError(problem?.detail || "Não foi possível carregar os indicadores reais de atendimento.");
    } finally {
      setIsLoading(false);
    }
  }, [period]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  const handleExportCsv = async () => {
    setIsExporting(true);
    try {
      const range = computeDateRange(period);
      await createReportExport("csv", range).catch(() => null);
      const rows = report?.recentQueue || [];
      const header = "Protocolo,Cidadao,Servico,Unidade,Data,Horario,Status\n";
      const body = rows
        .map(
          (r) =>
            `"${r.protocolNumber}","${r.citizenName}","${r.serviceName}","${r.unitName}","${r.scheduledDate}","${r.scheduledTime}","${r.status}"`
        )
        .join("\n");
      const blob = new Blob(["\uFEFF" + header + body], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", `relatorio_atendimentos_sosp_${period}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportPdf = async () => {
    const range = computeDateRange(period);
    await createReportExport("pdf", range).catch(() => null);
    window.print();
  };

  const total = report?.metrics.totalAppointments ?? 0;
  const completed = report?.metrics.completed ?? 0;
  const noShow = report?.metrics.noShow ?? 0;
  const scheduled = report?.metrics.scheduled ?? 0;
  const attendanceRate = report?.metrics.attendanceRate ?? 0;
  const noShowRate = total > 0 ? Number(((noShow / total) * 100).toFixed(1)) : 0;
  const serviceRows = report?.byService || [];

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[1200px] mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center text-xs text-gray-500 mb-6 print:hidden" aria-label="Breadcrumb">
          <Link href="/servidor/painel" className="hover:text-[#1351B4]">Painel do Servidor</Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <span className="font-semibold text-gray-900" aria-current="page">
            Relatórios Gerenciais (RF-14)
          </span>
        </nav>

        {/* Topo */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900">
              Relatório Geral de Atendimentos
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Métricas reais agregadas de desempenho, comparecimento e demanda da unidade.
            </p>
          </div>

          <div className="flex items-center gap-3 print:hidden">
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="py-2.5 px-3 rounded-xl border border-gray-300 text-xs bg-white focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
            >
              <option value="7days">Últimos 7 dias</option>
              <option value="30days">Últimos 30 dias</option>
              <option value="month">Mês Atual</option>
              <option value="year">Ano Atual</option>
            </select>

            <Button
              variant="secondary"
              onClick={handleExportCsv}
              isLoading={isExporting}
              className="text-xs"
            >
              <Download className="w-4 h-4 mr-1.5" />
              Exportar CSV
            </Button>

            <Button variant="primary" onClick={handleExportPdf} className="text-xs">
              <FileText className="w-4 h-4 mr-1.5" />
              Exportar PDF
            </Button>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-sm text-red-700">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{error}</span>
            </div>
            <Button variant="secondary" size="sm" onClick={loadReport}>
              Tentar novamente
            </Button>
          </div>
        )}

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8" aria-busy="true">
            <Skeleton className="h-32 w-full rounded-2xl" />
            <Skeleton className="h-32 w-full rounded-2xl" />
            <Skeleton className="h-32 w-full rounded-2xl" />
            <Skeleton className="h-32 w-full rounded-2xl" />
          </div>
        ) : (
          <>
            {/* Indicadores Principais */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
                <div className="flex items-center justify-between text-xs font-bold text-gray-500 uppercase">
                  <span>Total de Agendamentos</span>
                  <Users className="w-4 h-4 text-[#1351B4]" />
                </div>
                <div className="text-3xl font-black text-gray-900 mt-2">{total}</div>
                <span className="text-xs text-gray-500 mt-1 block">
                  {scheduled} aguardando atendimento
                </span>
              </div>

              <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
                <div className="flex items-center justify-between text-xs font-bold text-gray-500 uppercase">
                  <span>Taxa de Comparecimento</span>
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                </div>
                <div className="text-3xl font-black text-green-600 mt-2">{attendanceRate}%</div>
                <span className="text-xs text-gray-500 mt-1 block">{completed} cidadãos concluídos</span>
              </div>

              <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
                <div className="flex items-center justify-between text-xs font-bold text-gray-500 uppercase">
                  <span>Taxa de Abstenção</span>
                  <UserX className="w-4 h-4 text-red-600" />
                </div>
                <div className="text-3xl font-black text-red-600 mt-2">{noShowRate}%</div>
                <span className="text-xs text-red-600/80 mt-1 block">{noShow} ausências (RN-23)</span>
              </div>

              <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
                <div className="flex items-center justify-between text-xs font-bold text-gray-500 uppercase">
                  <span>Duração do Slot</span>
                  <BarChart3 className="w-4 h-4 text-amber-600" />
                </div>
                <div className="text-3xl font-black text-gray-900 mt-2">30 min</div>
                <span className="text-xs text-gray-500 mt-1 block">Padrão oficial SOSP (RN-18)</span>
              </div>
            </div>

            {/* Distribuição por Serviço + Últimos Protocolos */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
                <h2 className="text-lg font-bold text-gray-900 mb-6">
                  Serviços Mais Procurados no Período
                </h2>
                {serviceRows.length === 0 ? (
                  <p className="text-sm text-gray-500">
                    Nenhum agendamento registrado neste período para o seu escopo.
                  </p>
                ) : (
                  <div className="space-y-4">
                    {serviceRows.map((svc, idx) => {
                      const pct = total > 0 ? Math.round((svc.total / total) * 100) : 0;
                      return (
                        <div key={idx}>
                          <div className="flex justify-between text-xs font-semibold text-gray-700 mb-1">
                            <span>{svc.serviceName}</span>
                            <span>
                              {svc.total} ({pct}%)
                            </span>
                          </div>
                          <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-[#1351B4] rounded-full"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
                <h2 className="text-lg font-bold text-gray-900 mb-6">
                  Últimos Protocolos Registrados
                </h2>
                {!report?.recentQueue || report.recentQueue.length === 0 ? (
                  <p className="text-sm text-gray-500">
                    Nenhum protocolo encontrado no período selecionado.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {report.recentQueue.slice(0, 8).map((item) => (
                      <div
                        key={item.id}
                        className="flex items-center justify-between text-xs p-3 rounded-xl bg-gray-50 border border-gray-100"
                      >
                        <div>
                          <span className="font-mono font-bold text-[#1351B4]">{item.protocolNumber}</span>
                          <p className="font-semibold text-gray-900">{item.citizenName}</p>
                          <p className="text-gray-500">{item.serviceName}</p>
                        </div>
                        <div className="text-right">
                          <span className="block font-semibold text-gray-700">{item.scheduledDate}</span>
                          <span className="text-gray-500">{item.scheduledTime} · {item.status}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {/* Voltar */}
        <div className="print:hidden">
          <Link href="/servidor/painel">
            <Button variant="secondary">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Voltar ao Painel do Servidor
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

