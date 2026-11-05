"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Building2,
  Plus,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Edit2,
  Trash2,
  ChevronRight,
  Shield,
  Layers,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Tag } from "@/components/ui/Tag";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Modal } from "@/components/ui/Modal";
import { CriticalConfirmationModal } from "@/components/ui/CriticalConfirmationModal";
import { getAgencies } from "@/services/apiClient";
import type { Agency } from "@/types/api";

export default function AdminAgenciesPage() {
  const [agencies, setAgencies] = useState<Agency[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [sphereFilter, setSphereFilter] = useState("all");
  const [isLoading, setIsLoading] = useState(true);

  // Modais de Criação e Desativação Lógica (RN-40)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [deactivatingAgency, setDeactivatingAgency] = useState<Agency | null>(null);

  // Form State
  const [newAgency, setNewAgency] = useState({
    name: "",
    acronym: "",
    sphere: "state" as Agency["sphere"],
    description: "",
  });

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      try {
        const data = await getAgencies();
        setAgencies(data);
      } catch (err) {
        console.error("Erro ao carregar órgãos:", err);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  const handleCreateAgency = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAgency.name || !newAgency.acronym) return;

    const created: Agency = {
      id: `agency-${Date.now()}`,
      name: newAgency.name,
      acronym: newAgency.acronym.toUpperCase(),
      sphere: newAgency.sphere,
      description: newAgency.description,
      isActive: true,
    };

    setAgencies((prev) => [created, ...prev]);
    setIsCreateModalOpen(false);
    setNewAgency({ name: "", acronym: "", sphere: "state", description: "" });
  };

  const handleConfirmDeactivate = () => {
    if (!deactivatingAgency) return;
    // Exclusão Lógica Obrigatória (RN-40, RS-05): isActive = false
    setAgencies((prev) =>
      prev.map((a) =>
        a.id === deactivatingAgency.id ? { ...a, isActive: false } : a
      )
    );
    setDeactivatingAgency(null);
  };

  const filteredAgencies = agencies.filter((a) => {
    if (sphereFilter !== "all" && a.sphere !== sphereFilter) return false;
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      return (
        a.name.toLowerCase().includes(q) ||
        a.acronym.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const getSphereLabel = (sphere: Agency["sphere"]) => {
    switch (sphere) {
      case "municipal":
        return "Municipal";
      case "state":
        return "Estadual";
      case "federal":
        return "Federal";
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[1200px] mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center text-xs text-gray-500 mb-6" aria-label="Breadcrumb">
          <Link href="/" className="hover:text-[#1351B4]">Início</Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <Link href="/servidor/painel" className="hover:text-[#1351B4]">Área do Servidor</Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <span className="font-semibold text-gray-900" aria-current="page">
            Gestão de Órgãos Públicos
          </span>
        </nav>

        {/* Topo com Ações */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200 mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-indigo-50 text-indigo-700 rounded-2xl flex items-center justify-center">
              <Building2 className="w-8 h-8" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-700">
                Administração do Catálogo SOSP
              </span>
              <h1 className="text-2xl font-extrabold text-gray-900 mt-0.5">
                Órgãos e Entidades Públicas
              </h1>
              <p className="text-xs text-gray-500 mt-0.5">
                Cadastro de secretarias, departamentos e esferas governamentais conveniadas
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/admin/servicos">
              <Button variant="secondary" className="text-xs">
                <Layers className="w-4 h-4 mr-1.5" />
                Gerenciar Serviços
              </Button>
            </Link>
            <Button
              variant="primary"
              className="text-xs font-semibold shadow-md"
              onClick={() => setIsCreateModalOpen(true)}
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Novo Órgão
            </Button>
          </div>
        </div>

        {/* Barra de Filtros e Busca */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-200 mb-8">
          <div className="flex flex-col sm:flex-row gap-4 justify-between items-center">
            <div className="relative w-full sm:w-96">
              <input
                type="search"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Buscar por nome ou sigla (ex.: DETRAN, SEFAZ)..."
                className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
              />
              <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            </div>

            <div className="flex items-center gap-3 w-full sm:w-auto">
              <span className="text-xs text-gray-500">Esfera:</span>
              <select
                value={sphereFilter}
                onChange={(e) => setSphereFilter(e.target.value)}
                className="py-2 px-3 text-xs rounded-xl border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
              >
                <option value="all">Todas as esferas</option>
                <option value="state">Estadual</option>
                <option value="municipal">Municipal</option>
                <option value="federal">Federal</option>
              </select>
            </div>
          </div>
        </div>

        {/* Tabela de Órgãos */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-gray-600">
                  <th className="py-3.5 px-6 font-semibold">Sigla</th>
                  <th className="py-3.5 px-6 font-semibold">Nome do Órgão</th>
                  <th className="py-3.5 px-6 font-semibold">Esfera</th>
                  <th className="py-3.5 px-6 font-semibold">Status</th>
                  <th className="py-3.5 px-6 font-semibold text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredAgencies.map((agency) => (
                  <tr key={agency.id} className="hover:bg-gray-50/70 transition-colors">
                    <td className="py-4 px-6 font-extrabold text-[#1351B4]">
                      {agency.acronym}
                    </td>
                    <td className="py-4 px-6">
                      <span className="font-semibold text-gray-900 block">{agency.name}</span>
                      {agency.description && (
                        <span className="text-xs text-gray-500 line-clamp-1">
                          {agency.description}
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-6">
                      <span className="px-2.5 py-1 rounded-md bg-gray-100 text-gray-700 font-medium text-xs">
                        {getSphereLabel(agency.sphere)}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <Tag variant={agency.isActive ? "success" : "danger"}>
                        {agency.isActive ? "Ativo" : "Inativo"}
                      </Tag>
                    </td>
                    <td className="py-4 px-6 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {agency.isActive && (
                          <Button
                            variant="danger"
                            className="text-xs py-1 px-2.5"
                            onClick={() => setDeactivatingAgency(agency)}
                          >
                            <Trash2 className="w-3.5 h-3.5 mr-1" />
                            Desativar
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Modal de Criação de Órgão */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Cadastrar Novo Órgão Público"
      >
        <form onSubmit={handleCreateAgency} className="space-y-4">
          <Input
            label="Sigla Oficial"
            id="agency-acronym"
            placeholder="Ex.: DETRAN, SEFAZ, SEMED"
            value={newAgency.acronym}
            onChange={(e) => setNewAgency({ ...newAgency, acronym: e.target.value })}
            required
          />

          <Input
            label="Nome Completo do Órgão"
            id="agency-name"
            placeholder="Ex.: Departamento Estadual de Trânsito de Alagoas"
            value={newAgency.name}
            onChange={(e) => setNewAgency({ ...newAgency, name: e.target.value })}
            required
          />

          <Select
            label="Esfera Governamental"
            id="agency-sphere"
            value={newAgency.sphere}
            onChange={(e) =>
              setNewAgency({ ...newAgency, sphere: e.target.value as Agency["sphere"] })
            }
            options={[
              { value: "state", label: "Estadual" },
              { value: "municipal", label: "Municipal" },
              { value: "federal", label: "Federal" },
            ]}
          />

          <div>
            <label
              htmlFor="agency-desc"
              className="block text-sm font-semibold text-gray-700 mb-1.5"
            >
              Descrição Institucional
            </label>
            <textarea
              id="agency-desc"
              rows={3}
              value={newAgency.description}
              onChange={(e) => setNewAgency({ ...newAgency, description: e.target.value })}
              placeholder="Competências e finalidade do órgão..."
              className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsCreateModalOpen(false)}
            >
              Cancelar
            </Button>
            <Button type="submit" variant="primary">
              Salvar Órgão
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal de Desativação Lógica Obrigatória (RN-40, RS-05) */}
      <CriticalConfirmationModal
        isOpen={Boolean(deactivatingAgency)}
        onClose={() => setDeactivatingAgency(null)}
        onConfirm={handleConfirmDeactivate}
        title="Desativar Órgão Público"
        description={`Tem certeza que deseja desativar o órgão ${deactivatingAgency?.name} (${deactivatingAgency?.acronym})? Conforme a regra de auditoria (RN-40), a exclusão física é proibida. O registro sofrerá desativação lógica (isActive = false, deletedAt = NOW()).`}
        confirmText="Sim, Desativar Órgão"
        cancelText="Voltar"
        isDestructive={true}
      />
    </div>
  );
}

