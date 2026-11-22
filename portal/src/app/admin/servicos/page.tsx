"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Layers,
  Plus,
  Search,
  Eye,
  Trash2,
  ChevronRight,
  Building,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Tag } from "@/components/ui/Tag";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Modal } from "@/components/ui/Modal";
import { Skeleton } from "@/components/ui/Skeleton";
import { CriticalConfirmationModal } from "@/components/ui/CriticalConfirmationModal";
import { getServices, getAgencies, createService, deactivateService } from "@/services/apiClient";
import type { Service, Agency, ProblemDetails } from "@/types/api";

export default function AdminServicesPage() {
  const [services, setServices] = useState<Service[]>([]);
  const [agencies, setAgencies] = useState<Agency[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deactivatingService, setDeactivatingService] = useState<Service | null>(null);

  const [newService, setNewService] = useState({
    name: "",
    category: "Documentos",
    channel: "inPerson" as Service["channel"],
    agencyId: "",
    description: "",
    whoCanUse: "Cidadãos residentes em Alagoas.",
    isFree: true,
    costAmount: "",
    averageDeadlineDays: 5,
  });

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        const [res, loadedAgencies] = await Promise.all([
          getServices({ pageSize: 50 }),
          getAgencies(),
        ]);
        setServices(res.items || []);
        setAgencies(loadedAgencies || []);
        if (loadedAgencies.length > 0) {
          setNewService((prev) => ({ ...prev, agencyId: prev.agencyId || loadedAgencies[0].id }));
        }
      } catch (err: unknown) {
        const problem = err as ProblemDetails;
        setErrorMessage(problem?.detail || "Erro ao carregar catálogo de serviços.");
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  const handleCreateService = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newService.name.trim() || !newService.description.trim() || !newService.agencyId) return;
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const created = await createService({
        name: newService.name.trim(),
        category: newService.category,
        channel: newService.channel,
        agencyId: newService.agencyId,
        description: newService.description.trim(),
        whoCanUse: newService.whoCanUse.trim() || "Cidadãos residentes em Alagoas.",
        isFree: newService.isFree,
        costAmount: newService.isFree ? null : Number(newService.costAmount || 0),
        averageDeadlineDays: Number(newService.averageDeadlineDays || 0),
      });
      setServices((prev) => [created, ...prev]);
      setIsCreateModalOpen(false);
      setNewService({
        name: "",
        category: "Documentos",
        channel: "inPerson",
        agencyId: agencies[0]?.id || "",
        description: "",
        whoCanUse: "Cidadãos residentes em Alagoas.",
        isFree: true,
        costAmount: "",
        averageDeadlineDays: 5,
      });
    } catch (err: unknown) {
      const problem = err as ProblemDetails;
      setErrorMessage(problem?.detail || "Não foi possível publicar o novo serviço.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfirmDeactivate = async () => {
    if (!deactivatingService) return;
    try {
      await deactivateService(deactivatingService.id);
      setServices((prev) => prev.filter((s) => s.id !== deactivatingService.id));
    } catch (err: unknown) {
      const problem = err as ProblemDetails;
      setErrorMessage(problem?.detail || "Erro ao desativar serviço.");
    } finally {
      setDeactivatingService(null);
    }
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
            <Button
              variant="primary"
              className="text-xs font-semibold shadow-md"
              onClick={() => setIsCreateModalOpen(true)}
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Novo Serviço
            </Button>
          </div>
        </div>

        {errorMessage && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2 text-sm text-red-700">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

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
          {isLoading ? (
            <div className="p-6 space-y-3" aria-busy="true">
              <Skeleton className="h-10 w-full rounded-lg" />
              <Skeleton className="h-10 w-full rounded-lg" />
              <Skeleton className="h-10 w-full rounded-lg" />
            </div>
          ) : filteredServices.length === 0 ? (
            <div className="p-10 text-center text-sm text-gray-500">
              Nenhum serviço encontrado no catálogo. Clique em &quot;Novo Serviço&quot; para publicar o primeiro.
            </div>
          ) : (
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
          )}
        </div>
      </div>

      {/* Modal de Criação de Serviço Público (RF-05) */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Publicar Novo Serviço Público"
      >
        <form onSubmit={handleCreateService} className="space-y-4">
          <Input
            label="Nome do Serviço"
            id="svc-name"
            placeholder="Ex: Emitir Carteira de Identidade Nacional (CIN)"
            value={newService.name}
            onChange={(e) => setNewService({ ...newService, name: e.target.value })}
            required
          />

          <Select
            label="Órgão Responsável"
            id="svc-agency"
            value={newService.agencyId}
            onChange={(e) => setNewService({ ...newService, agencyId: e.target.value })}
            options={agencies.map((a) => ({ value: a.id, label: `${a.acronym} — ${a.name}` }))}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Categoria"
              id="svc-cat"
              value={newService.category}
              onChange={(e) => setNewService({ ...newService, category: e.target.value })}
              options={[
                { value: "Documentos", label: "Documentos" },
                { value: "Saúde", label: "Saúde" },
                { value: "Educação", label: "Educação" },
                { value: "Transporte", label: "Transporte / Trânsito" },
                { value: "Assistência Social", label: "Assistência Social" },
                { value: "Tributos", label: "Tributos" },
                { value: "Trabalho", label: "Trabalho" },
                { value: "Geral", label: "Geral" },
              ]}
            />

            <Select
              label="Canal de Atendimento"
              id="svc-channel"
              value={newService.channel}
              onChange={(e) =>
                setNewService({ ...newService, channel: e.target.value as Service["channel"] })
              }
              options={[
                { value: "inPerson", label: "Presencial" },
                { value: "hybrid", label: "Híbrido" },
                { value: "online", label: "Online" },
              ]}
            />
          </div>

          <div>
            <label htmlFor="svc-desc" className="block text-xs font-bold text-gray-700 mb-1">
              Descrição Detalhada (O que é?)
            </label>
            <textarea
              id="svc-desc"
              rows={3}
              required
              value={newService.description}
              onChange={(e) => setNewService({ ...newService, description: e.target.value })}
              placeholder="Explique em linguagem simples o objetivo deste serviço público..."
              className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
            />
          </div>

          <Input
            label="Quem tem direito?"
            id="svc-who"
            value={newService.whoCanUse}
            onChange={(e) => setNewService({ ...newService, whoCanUse: e.target.value })}
            required
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center">
            <Input
              label="Prazo Médio (dias úteis, 0 = Imediato)"
              id="svc-deadline"
              type="number"
              min={0}
              value={String(newService.averageDeadlineDays)}
              onChange={(e) =>
                setNewService({ ...newService, averageDeadlineDays: Number(e.target.value) })
              }
            />

            <div className="pt-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newService.isFree}
                  onChange={(e) => setNewService({ ...newService, isFree: e.target.checked })}
                  className="w-4 h-4 text-[#1351B4] rounded"
                />
                <span className="text-xs font-semibold text-gray-700">Serviço Gratuito</span>
              </label>
            </div>
          </div>

          {!newService.isFree && (
            <Input
              label="Valor da Taxa (R$)"
              id="svc-cost"
              type="number"
              step="0.01"
              min="0.01"
              placeholder="Ex: 42.00"
              value={newService.costAmount}
              onChange={(e) => setNewService({ ...newService, costAmount: e.target.value })}
              required
            />
          )}

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <Button type="button" variant="secondary" onClick={() => setIsCreateModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" variant="primary" isLoading={isSubmitting}>
              Publicar Serviço
            </Button>
          </div>
        </form>
      </Modal>

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

