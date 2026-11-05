"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Layers,
  Plus,
  Search,
  CheckCircle2,
  XCircle,
  Eye,
  Trash2,
  ChevronRight,
  Building,
  ArrowLeft,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Tag } from "@/components/ui/Tag";
import { CriticalConfirmationModal } from "@/components/ui/CriticalConfirmationModal";
import { getServices } from "@/services/apiClient";
import type { Service } from "@/types/api";

export default function AdminServicesPage() {
  const [services, setServices] = useState<Service[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [deactivatingService, setDeactivatingService] = useState<Service | null>(null);

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      try {
        const res = await getServices();
        setServices(res.items);
      } catch (err) {
        console.error("Erro ao carregar serviços:", err);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  const handleConfirmDeactivate = () => {
    if (!deactivatingService) return;
    // Exclusão Lógica Obrigatória (RN-40, RS-05)
    setServices((prev) => prev.filter((s) => s.id !== deactivatingService.id));
    setDeactivatingService(null);
  };

  const filteredServices = services.filter((s) => {
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      return (
        s.name.toLowerCase().includes(q) ||
        s.agencyName.toLowerCase().includes(q) ||
        s.agencyAcronym.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[1200px] mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center text-xs text-gray-500 mb-6" aria-label="Breadcrumb">
          <Link href="/" className="hover:text-[#1351B4]">Início</Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <Link href="/admin/orgaos" className="hover:text-[#1351B4]">Administração</Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <span className="font-semibold text-gray-900" aria-current="page">
            Catálogo de Serviços
          </span>
        </nav>

        {/* Topo com Ações */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200 mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-blue-50 text-[#1351B4] rounded-2xl flex items-center justify-center">
              <Layers className="w-8 h-8" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-[#1351B4]">
                Gestão do Catálogo SOSP
              </span>
              <h1 className="text-2xl font-extrabold text-gray-900 mt-0.5">
                Serviços Públicos Cadastrados
              </h1>
              <p className="text-xs text-gray-500 mt-0.5">
                Controle de fichas orientativas, requisitos, etapas e versionamento
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/admin/orgaos">
              <Button variant="secondary" className="text-xs">
                <Building className="w-4 h-4 mr-1.5" />
                Gerenciar Órgãos
              </Button>
            </Link>
          </div>
        </div>

        {/* Busca */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-200 mb-8">
          <div className="relative w-full sm:w-96">
            <input
              type="search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar serviço no catálogo..."
              className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
            />
            <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          </div>
        </div>

        {/* Tabela de Serviços */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-gray-600">
                  <th className="py-3.5 px-6 font-semibold">Nome do Serviço</th>
                  <th className="py-3.5 px-6 font-semibold">Órgão Responsável</th>
                  <th className="py-3.5 px-6 font-semibold">Canal</th>
                  <th className="py-3.5 px-6 font-semibold">Custo</th>
                  <th className="py-3.5 px-6 font-semibold">Prazo (SLA)</th>
                  <th className="py-3.5 px-6 font-semibold text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredServices.map((service) => (
                  <tr key={service.id} className="hover:bg-gray-50/70 transition-colors">
                    <td className="py-4 px-6 font-bold text-gray-900">
                      {service.name}
                      <span className="block text-xs text-gray-500 font-normal mt-0.5">
                        Categoria: {service.category}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-gray-700">
                      {service.agencyName} ({service.agencyAcronym})
                    </td>
                    <td className="py-4 px-6">
                      <Tag variant="channel">
                        {service.channel === "online"
                          ? "Online"
                          : service.channel === "inPerson"
                          ? "Presencial"
                          : "Híbrido"}
                      </Tag>
                    </td>
                    <td className="py-4 px-6 font-semibold text-gray-900">
                      {service.isFree ? "Gratuito" : `R$ ${service.costAmount?.toFixed(2)}`}
                    </td>
                    <td className="py-4 px-6 text-gray-600">
                      {service.averageDeadlineDays === 0
                        ? "Imediato"
                        : `${service.averageDeadlineDays} dias úteis`}
                    </td>
                    <td className="py-4 px-6 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link href={`/servicos/${service.id}`}>
                          <Button variant="secondary" className="text-xs py-1 px-2.5">
                            <Eye className="w-3.5 h-3.5 mr-1" />
                            Visualizar
                          </Button>
                        </Link>
                        <Button
                          variant="danger"
                          className="text-xs py-1 px-2.5"
                          onClick={() => setDeactivatingService(service)}
                        >
                          <Trash2 className="w-3.5 h-3.5 mr-1" />
                          Desativar
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Modal de Desativação Lógica Obrigatória (RN-40) */}
      <CriticalConfirmationModal
        isOpen={Boolean(deactivatingService)}
        onClose={() => setDeactivatingService(null)}
        onConfirm={handleConfirmDeactivate}
        title="Desativar Serviço Público"
        description={`Tem certeza que deseja desativar o serviço ${deactivatingService?.name}? Conforme a regra RN-40, novos agendamentos serão bloqueados, mas o histórico permanece preservado.`}
        confirmText="Sim, Desativar Serviço"
        cancelText="Voltar"
        isDestructive={true}
      />
    </div>
  );
}

