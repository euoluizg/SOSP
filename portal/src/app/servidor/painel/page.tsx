"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Users,
  CheckCircle2,
  Clock,
  UserX,
  Search,
  Calendar,
  Filter,
  Check,
  Play,
  FileText,
  Building,
  Shield,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Tag } from "@/components/ui/Tag";
import { CriticalConfirmationModal } from "@/components/ui/CriticalConfirmationModal";

interface QueueItem {
  id: string;
  time: string;
  protocol: string;
  citizenName: string;
  citizenCpf: string;
  serviceName: string;
  status: "waiting" | "in_progress" | "completed" | "no_show";
}

const INITIAL_QUEUE: QueueItem[] = [
  {
    id: "q-1",
    time: "08:00",
    protocol: "20261105-1001",
    citizenName: "Maria Eduarda Silveira",
    citizenCpf: "123.456.789-01",
    serviceName: "Emitir Carteira de Identidade Nacional (CIN)",
    status: "completed",
  },
  {
    id: "q-2",
    time: "08:30",
    protocol: "20261105-1014",
    citizenName: "João Pedro Cavalcante",
    citizenCpf: "234.567.890-12",
    serviceName: "Renovação da CNH",
    status: "completed",
  },
  {
    id: "q-3",
    time: "09:00",
    protocol: "20261105-1028",
    citizenName: "Ana Clara Albuquerque",
    citizenCpf: "345.678.901-23",
    serviceName: "Emitir Carteira de Identidade Nacional (CIN)",
    status: "in_progress",
  },
  {
    id: "q-4",
    time: "09:30",
    protocol: "20261105-1042",
    citizenName: "Carlos Eduardo Santos",
    citizenCpf: "456.789.012-34",
    serviceName: "Cadastro Único (CadÚnico)",
    status: "waiting",
  },
  {
    id: "q-5",
    time: "10:00",
    protocol: "20261105-1055",
    citizenName: "Beatriz Oliveira Lima",
    citizenCpf: "567.890.123-45",
    serviceName: "Certidão Negativa de Débitos (SEFAZ)",
    status: "waiting",
  },
  {
    id: "q-6",
    time: "10:30",
    protocol: "20261105-1068",
    citizenName: "Lucas Henrique Ferreira",
    citizenCpf: "678.901.234-56",
    serviceName: "Emitir Carteira de Identidade Nacional (CIN)",
    status: "no_show",
  },
];

export default function ServerDashboardPage() {
  const [queue, setQueue] = useState<QueueItem[]>(INITIAL_QUEUE);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [noShowItem, setNoShowItem] = useState<QueueItem | null>(null);

  // Ações do Servidor
  const handleStartAttendance = (id: string) => {
    setQueue((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, status: "in_progress" } : item
      )
    );
  };

  const handleCompleteAttendance = (id: string) => {
    setQueue((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, status: "completed" } : item
      )
    );
  };

  const handleConfirmNoShow = () => {
    if (!noShowItem) return;
    setQueue((prev) =>
      prev.map((item) =>
        item.id === noShowItem.id ? { ...item, status: "no_show" } : item
      )
    );
    setNoShowItem(null);
  };

  // Filtragem da Fila
  const filteredQueue = queue.filter((item) => {
    if (statusFilter !== "all" && item.status !== statusFilter) return false;
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      return (
        item.citizenName.toLowerCase().includes(q) ||
        item.citizenCpf.includes(q) ||
        item.protocol.includes(q)
      );
    }
    return true;
  });

  const totalToday = queue.length;
  const inProgressCount = queue.filter((i) => i.status === "in_progress").length;
  const waitingCount = queue.filter((i) => i.status === "waiting").length;
  const completedCount = queue.filter((i) => i.status === "completed").length;
  const noShowCount = queue.filter((i) => i.status === "no_show").length;

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[1200px] mx-auto">
        {/* Header do Servidor */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200 mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-blue-100 text-[#1351B4] rounded-2xl flex items-center justify-center font-bold text-xl">
              <Shield className="w-8 h-8" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-[#1351B4]">
                Painel do Servidor Público
              </span>
              <h1 className="text-2xl font-extrabold text-gray-900 mt-0.5">
                Central Já! Centro — Guichê 04
              </h1>
              <p className="text-xs text-gray-500 mt-0.5">
                Atendente: <strong>Arthur Franco (Matrícula: 2026-9921)</strong> | Lotação: Maceió - AL
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/servidor/relatorios">
              <Button variant="secondary" className="text-xs">
                <FileText className="w-4 h-4 mr-1.5" />
                Relatórios Operacionais
              </Button>
            </Link>
            <Link href="/admin/orgaos">
              <Button variant="tertiary" className="text-xs text-gray-600">
                <Building className="w-4 h-4 mr-1.5" />
                Gestão Geral
              </Button>
            </Link>
          </div>
        </div>

        {/* 4 Cards de Métricas Operacionais */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-gray-500 uppercase">Total Hoje</span>
              <div className="w-8 h-8 bg-blue-50 text-[#1351B4] rounded-lg flex items-center justify-center">
                <Users className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-extrabold text-gray-900 mt-2">
              {totalToday}
            </div>
            <span className="text-xs text-gray-400 mt-1 block">Agendamentos no dia</span>
          </div>

          <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-amber-700 uppercase">Aguardando</span>
              <div className="w-8 h-8 bg-amber-50 text-amber-600 rounded-lg flex items-center justify-center">
                <Clock className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-extrabold text-amber-700 mt-2">
              {waitingCount + inProgressCount}
            </div>
            <span className="text-xs text-amber-600/80 mt-1 block">
              {inProgressCount > 0 ? `${inProgressCount} em atendimento agora` : "Aguardando chamada"}
            </span>
          </div>

          <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-green-700 uppercase">Concluídos</span>
              <div className="w-8 h-8 bg-green-50 text-green-600 rounded-lg flex items-center justify-center">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-extrabold text-green-700 mt-2">
              {completedCount}
            </div>
            <span className="text-xs text-green-600/80 mt-1 block">Atendidos com sucesso</span>
          </div>

          <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-red-700 uppercase">Não Compareceu</span>
              <div className="w-8 h-8 bg-red-50 text-red-600 rounded-lg flex items-center justify-center">
                <UserX className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-extrabold text-red-700 mt-2">
              {noShowCount}
            </div>
            <span className="text-xs text-red-600/80 mt-1 block">Ausências registradas (RN-23)</span>
          </div>
        </div>

        {/* Fila de Atendimento do Dia */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                Fila de Atendimento do Expediente
              </h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Controle de fluxo de cidadãos e registro de comparecimento
              </p>
            </div>

            {/* Filtros e Busca */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="relative w-full sm:w-64">
                <input
                  type="search"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Buscar cidadão, CPF ou protocolo..."
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
                />
                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
              </div>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="py-2 px-3 text-xs rounded-xl border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
              >
                <option value="all">Todos os status</option>
                <option value="waiting">Aguardando</option>
                <option value="in_progress">Em Atendimento</option>
                <option value="completed">Concluídos</option>
                <option value="no_show">Não Compareceu</option>
              </select>
            </div>
          </div>

          {/* Tabela da Fila */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-gray-600">
                  <th className="py-3 px-4 font-semibold">Horário</th>
                  <th className="py-3 px-4 font-semibold">Protocolo</th>
                  <th className="py-3 px-4 font-semibold">Cidadão</th>
                  <th className="py-3 px-4 font-semibold">Serviço</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold text-right">Ações Operacionais</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredQueue.map((item) => (
                  <tr
                    key={item.id}
                    className={`hover:bg-gray-50/70 transition-colors ${
                      item.status === "in_progress" ? "bg-blue-50/40" : ""
                    }`}
                  >
                    <td className="py-3.5 px-4 font-bold text-gray-900">{item.time}</td>
                    <td className="py-3.5 px-4 font-mono font-bold text-[#1351B4]">
                      {item.protocol}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="font-semibold text-gray-900 block">{item.citizenName}</span>
                      <span className="text-xs text-gray-500 font-mono">{item.citizenCpf}</span>
                    </td>
                    <td className="py-3.5 px-4 text-gray-700">{item.serviceName}</td>
                    <td className="py-3.5 px-4">
                      <Tag
                        variant={
                          item.status === "completed"
                            ? "success"
                            : item.status === "in_progress"
                            ? "info"
                            : item.status === "no_show"
                            ? "danger"
                            : "warning"
                        }
                      >
                        {item.status === "completed"
                          ? "Concluído"
                          : item.status === "in_progress"
                          ? "Em Atendimento"
                          : item.status === "no_show"
                          ? "Não Compareceu"
                          : "Aguardando"}
                      </Tag>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      {item.status === "waiting" && (
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="primary"
                            className="text-xs py-1.5 px-3"
                            onClick={() => handleStartAttendance(item.id)}
                          >
                            <Play className="w-3.5 h-3.5 mr-1" />
                            Chamar
                          </Button>
                          <Button
                            variant="danger"
                            className="text-xs py-1.5 px-3"
                            onClick={() => setNoShowItem(item)}
                          >
                            Falta
                          </Button>
                        </div>
                      )}

                      {item.status === "in_progress" && (
                        <Button
                          variant="secondary"
                          className="text-xs py-1.5 px-3 border-green-600 text-green-700 hover:bg-green-50"
                          onClick={() => handleCompleteAttendance(item.id)}
                        >
                          <Check className="w-3.5 h-3.5 mr-1" />
                          Concluir Atendimento
                        </Button>
                      )}

                      {item.status === "completed" && (
                        <span className="text-xs text-green-700 font-semibold inline-flex items-center">
                          <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                          Finalizado
                        </span>
                      )}

                      {item.status === "no_show" && (
                        <span className="text-xs text-red-600 font-semibold inline-flex items-center">
                          <UserX className="w-3.5 h-3.5 mr-1" />
                          Ausente
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Modal de Registro de Falta (RN-23) */}
      <CriticalConfirmationModal
        isOpen={Boolean(noShowItem)}
        onClose={() => setNoShowItem(null)}
        onConfirm={handleConfirmNoShow}
        title="Registrar Não Comparecimento"
        description={`Confirma que o cidadão ${noShowItem?.citizenName} (Protocolo ${noShowItem?.protocol}) não compareceu no horário das ${noShowItem?.time}? Este registro ficará gravado no histórico (RN-23).`}
        confirmText="Confirmar Ausência"
        cancelText="Voltar"
        isDestructive={true}
      />
    </div>
  );
}

