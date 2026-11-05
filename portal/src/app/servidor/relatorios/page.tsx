"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  FileText,
  Download,
  Calendar,
  Filter,
  BarChart3,
  TrendingUp,
  Users,
  CheckCircle2,
  UserX,
  ArrowLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function ReportsPage() {
  const [period, setPeriod] = useState("30days");
  const [isExporting, setIsExporting] = useState(false);

  const handleExportCsv = () => {
    setIsExporting(true);
    setTimeout(() => {
      setIsExporting(false);
      // Simula download CSV
      const csvContent =
        "data:text/csv;charset=utf-8,Protocolo,Cidadao,Servico,Unidade,Data,Status\n" +
        "20261105-1001,Maria Eduarda Silveira,Emitir CIN,Central Ja! Centro,2026-11-05,Concluido\n" +
        "20261105-1014,Joao Pedro Cavalcante,Renovacao CNH,Central Ja! Centro,2026-11-05,Concluido\n" +
        "20261105-1068,Lucas Henrique Ferreira,Emitir CIN,Central Ja! Centro,2026-11-05,Nao Compareceu\n";
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", `relatorio_atendimentos_sosp_${period}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }, 600);
  };

  const handleExportPdf = () => {
    window.print();
  };

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
              Métricas agregadas de desempenho, comparecimento e capacidade instalada da unidade.
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
              <option value="month">Mês Atual (Novembro/2026)</option>
              <option value="year">Ano de 2026</option>
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

        {/* Indicadores Principais */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between text-xs font-bold text-gray-500 uppercase">
              <span>Total de Agendamentos</span>
              <Users className="w-4 h-4 text-[#1351B4]" />
            </div>
            <div className="text-3xl font-black text-gray-900 mt-2">1.248</div>
            <span className="text-xs text-green-600 mt-1 block">
              +12% em relação ao período anterior
            </span>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between text-xs font-bold text-gray-500 uppercase">
              <span>Taxa de Comparecimento</span>
              <CheckCircle2 className="w-4 h-4 text-green-600" />
            </div>
            <div className="text-3xl font-black text-green-600 mt-2">91.4%</div>
            <span className="text-xs text-gray-500 mt-1 block">1.141 cidadãos atendidos</span>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between text-xs font-bold text-gray-500 uppercase">
              <span>Taxa de Abstenção</span>
              <UserX className="w-4 h-4 text-red-600" />
            </div>
            <div className="text-3xl font-black text-red-600 mt-2">8.6%</div>
            <span className="text-xs text-red-600/80 mt-1 block">107 ausências (RN-23)</span>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between text-xs font-bold text-gray-500 uppercase">
              <span>Tempo Médio</span>
              <BarChart3 className="w-4 h-4 text-amber-600" />
            </div>
            <div className="text-3xl font-black text-gray-900 mt-2">18 min</div>
            <span className="text-xs text-gray-500 mt-1 block">Slot máximo de 30 minutos</span>
          </div>
        </div>

        {/* Gráfico / Distribuição por Serviço */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Card 1: Distribuição de Demanda por Serviço */}
          <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
            <h2 className="text-lg font-bold text-gray-900 mb-6">
              Serviços Mais Procurados
            </h2>
            <div className="space-y-4">
              {[
                { name: "Emitir Carteira de Identidade (CIN)", count: 620, percent: 50 },
                { name: "Renovação de CNH (DETRAN)", count: 310, percent: 25 },
                { name: "Cadastro Único (CadÚnico)", count: 186, percent: 15 },
                { name: "Certidão Negativa de Débitos (SEFAZ)", count: 132, percent: 10 },
              ].map((svc, idx) => (
                <div key={idx}>
                  <div className="flex justify-between text-xs font-semibold text-gray-700 mb-1">
                    <span>{svc.name}</span>
                    <span>
                      {svc.count} ({svc.percent}%)
                    </span>
                  </div>
                  <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#1351B4] rounded-full"
                      style={{ width: `${svc.percent}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Card 2: Horários de Pico no Expediente */}
          <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
            <h2 className="text-lg font-bold text-gray-900 mb-6">
              Distribuição por Faixa de Horário
            </h2>
            <div className="space-y-4">
              {[
                { time: "08:00 - 10:00 (Manhã cedo)", load: 95 },
                { time: "10:00 - 12:00 (Pico da manhã)", load: 100 },
                { time: "13:30 - 15:30 (Início da tarde)", load: 78 },
                { time: "15:30 - 17:00 (Final do expediente)", load: 60 },
              ].map((slot, idx) => (
                <div key={idx}>
                  <div className="flex justify-between text-xs font-semibold text-gray-700 mb-1">
                    <span>{slot.time}</span>
                    <span>{slot.load}% ocupação</span>
                  </div>
                  <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        slot.load >= 90
                          ? "bg-red-500"
                          : slot.load >= 70
                          ? "bg-amber-500"
                          : "bg-green-500"
                      }`}
                      style={{ width: `${slot.load}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

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

