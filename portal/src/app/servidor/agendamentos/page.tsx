"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Calendar as CalendarIcon,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  ChevronRight,
  ArrowLeft,
  Building,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Tag } from "@/components/ui/Tag";

interface AppointmentItem {
  id: string;
  protocol: string;
  citizenName: string;
  citizenCpf: string;
  serviceName: string;
  date: string;
  time: string;
  unitName: string;
  status: "scheduled" | "confirmed" | "completed" | "cancelled" | "no_show";
}

const APPOINTMENTS_LIST: AppointmentItem[] = [
  {
    id: "app-1",
    protocol: "20261105-1001",
    citizenName: "Maria Eduarda Silveira",
    citizenCpf: "123.456.789-01",
    serviceName: "Emitir Carteira de Identidade Nacional (CIN)",
    date: "2026-11-05",
    time: "08:00",
    unitName: "Central Já! Centro",
    status: "completed",
  },
  {
    id: "app-2",
    protocol: "20261105-1014",
    citizenName: "João Pedro Cavalcante",
    citizenCpf: "234.567.890-12",
    serviceName: "Renovação da CNH",
    date: "2026-11-05",
    time: "08:30",
    unitName: "Central Já! Centro",
    status: "completed",
  },
  {
    id: "app-3",
    protocol: "20261105-1028",
    citizenName: "Ana Clara Albuquerque",
    citizenCpf: "345.678.901-23",
    serviceName: "Emitir Carteira de Identidade Nacional (CIN)",
    date: "2026-11-05",
    time: "09:00",
    unitName: "Central Já! Centro",
    status: "confirmed",
  },
  {
    id: "app-4",
    protocol: "20261105-1042",
    citizenName: "Carlos Eduardo Santos",
    citizenCpf: "456.789.012-34",
    serviceName: "Cadastro Único (CadÚnico)",
    date: "2026-11-05",
    time: "09:30",
    unitName: "Central Já! Centro",
    status: "scheduled",
  },
  {
    id: "app-5",
    protocol: "20261105-1068",
    citizenName: "Lucas Henrique Ferreira",
    citizenCpf: "678.901.234-56",
    serviceName: "Emitir Carteira de Identidade Nacional (CIN)",
    date: "2026-11-05",
    time: "10:30",
    unitName: "Central Já! Centro",
    status: "no_show",
  },
];

export default function ServerAppointmentsPage() {
  const [appointments, setAppointments] = useState<AppointmentItem[]>(APPOINTMENTS_LIST);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const filtered = appointments.filter((item) => {
    if (statusFilter !== "all" && item.status !== statusFilter) return false;
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      return (
        item.citizenName.toLowerCase().includes(q) ||
        item.protocol.includes(q) ||
        item.citizenCpf.includes(q)
      );
    }
    return true;
  });

  const getStatusBadge = (status: AppointmentItem["status"]) => {
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
      <div className="max-w-[1200px] mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center text-xs text-gray-500 mb-6" aria-label="Breadcrumb">
          <Link href="/servidor/painel" className="hover:text-[#1351B4]">Painel do Servidor</Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <span className="font-semibold text-gray-900" aria-current="page">
            Gerenciar Agendamentos (Tela 17 / RF-08)
          </span>
        </nav>

        {/* Topo */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200 mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-blue-50 text-[#1351B4] rounded-2xl flex items-center justify-center">
              <CalendarIcon className="w-8 h-8" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-[#1351B4]">
                Operação Presencial SOSP
              </span>
              <h1 className="text-2xl font-extrabold text-gray-900 mt-0.5">
                Gerenciamento de Agendamentos
              </h1>
              <p className="text-xs text-gray-500 mt-0.5">
                Central Já! Centro — Grade horária em slots de 30 minutos (RN-18)
              </p>
            </div>
          </div>

          <Link href="/servidor/painel">
            <Button variant="secondary" className="text-xs">
              <ArrowLeft className="w-4 h-4 mr-1.5" />
              Voltar ao Painel
            </Button>
          </Link>
        </div>

        {/* Busca e Filtros */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-200 mb-8 flex flex-col sm:flex-row gap-4 justify-between items-center">
          <div className="relative w-full sm:w-96">
            <input
              type="search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar por cidadão, CPF ou protocolo..."
              className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
            />
            <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <span className="text-xs text-gray-500">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="py-2 px-3 text-xs rounded-xl border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
            >
              <option value="all">Todos os status</option>
              <option value="scheduled">Agendados</option>
              <option value="confirmed">Confirmados</option>
              <option value="completed">Concluídos</option>
              <option value="no_show">Não Compareceu</option>
            </select>
          </div>
        </div>

        {/* Tabela de Agendamentos */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-gray-600">
                  <th className="py-3.5 px-6 font-semibold">Protocolo</th>
                  <th className="py-3.5 px-6 font-semibold">Data / Horário</th>
                  <th className="py-3.5 px-6 font-semibold">Cidadão</th>
                  <th className="py-3.5 px-6 font-semibold">Serviço</th>
                  <th className="py-3.5 px-6 font-semibold">Status</th>
                  <th className="py-3.5 px-6 font-semibold text-right">Ação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map((item) => {
                  const badge = getStatusBadge(item.status);
                  return (
                    <tr key={item.id} className="hover:bg-gray-50/70 transition-colors">
                      <td className="py-4 px-6 font-mono font-bold text-[#1351B4]">
                        {item.protocol}
                      </td>
                      <td className="py-4 px-6">
                        <span className="font-semibold text-gray-900 block">
                          {item.date.split("-").reverse().join("/")}
                        </span>
                        <span className="text-xs text-gray-500 font-bold">{item.time} (30 min)</span>
                      </td>
                      <td className="py-4 px-6">
                        <span className="font-semibold text-gray-900 block">{item.citizenName}</span>
                        <span className="text-xs text-gray-500 font-mono">{item.citizenCpf}</span>
                      </td>
                      <td className="py-4 px-6 text-gray-700">{item.serviceName}</td>
                      <td className="py-4 px-6">
                        <Tag variant={badge.variant}>{badge.label}</Tag>
                      </td>
                      <td className="py-4 px-6 text-right">
                        <Link href={`/cidadao/protocolos/${item.protocol}`}>
                          <Button variant="secondary" className="text-xs py-1 px-3">
                            Ver Detalhes
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

