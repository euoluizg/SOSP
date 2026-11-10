"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Building2,
  Plus,
  Search,
  Filter,
  CheckCircle2,
  AlertCircle,
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
import { getAgencies, updateAgency } from "@/services/apiClient";
import type { Agency, ProblemDetails } from "@/types/api";

export default function AdminAgenciesPage() {
  const [agencies, setAgencies] = useState<Agency[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [sphereFilter, setSphereFilter] = useState("all");
  const [isLoading, setIsLoading] = useState(true);

  // Modais de Criação, Edição e Desativação Lógica (RN-40)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingAgency, setEditingAgency] = useState<Agency | null>(null);
  const [deactivatingAgency, setDeactivatingAgency] = useState<Agency | null>(null);

  // Form State - Criação
  const [newAgency, setNewAgency] = useState({
    name: "",
    acronym: "",
    sphere: "state" as Agency["sphere"],
    description: "",
  });

  // Form State - Edição
  const [editForm, setEditForm] = useState({
    name: "",
    acronym: "",
    sphere: "state" as Agency["sphere"],
    description: "",
  });
  const [isSavingEdit, setIsSavingEdit] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);

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

  const handleStartEdit = (agency: Agency) => {
    setEditingAgency(agency);
    setEditForm({
      name: agency.name,
      acronym: agency.acronym,
      sphere: agency.sphere,
      description: agency.description || "",
    });
    setEditError(null);
    setIsEditModalOpen(true);
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingAgency) return;
    if (!editForm.name.trim() || !editForm.acronym.trim()) {
      setEditError("Sigla e nome do órgão são obrigatórios.");
      return;
    }

    setIsSavingEdit(true);
    setEditError(null);
    try {
      const updated = await updateAgency(editingAgency.id, {
        name: editForm.name.trim(),
        acronym: editForm.acronym.trim().toUpperCase(),
        sphere: editForm.sphere,
        description: editForm.description.trim(),
      });

      setAgencies((prev) =>
        prev.map((a) => (a.id === editingAgency.id ? { ...a, ...updated } : a))
      );
      setIsEditModalOpen(false);
      setEditingAgency(null);
      setSuccessToast(`Órgão ${updated.acronym} atualizado com sucesso!`);
      setTimeout(() => setSuccessToast(null), 4000);
    } catch (err: unknown) {
      const problem = err as ProblemDetails;
      setEditError(
        problem?.detail ||
          (problem?.errors && problem.errors.length > 0
            ? problem.errors.map((e) => e.message).join(", ")
            : "Erro ao atualizar órgão. Verifique suas permissões de gestor.")
      );
    } finally {
      setIsSavingEdit(false);
    }
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
                          <>
                            <Button
                              variant="secondary"
                              className="text-xs py-1 px-2.5"
                              onClick={() => handleStartEdit(agency)}
                            >
                              <Edit2 className="w-3.5 h-3.5 mr-1" />
                              Editar
                            </Button>
                            <Button
                              variant="danger"
                              className="text-xs py-1 px-2.5"
                              onClick={() => setDeactivatingAgency(agency)}
                            >
                              <Trash2 className="w-3.5 h-3.5 mr-1" />
                              Desativar
                            </Button>
                          </>
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

      {/* Notificação de Sucesso */}
      {successToast && (
        <div
          className="fixed bottom-6 right-6 z-50 bg-green-600 text-white px-5 py-3 rounded-xl shadow-xl flex items-center gap-3 animate-fadeIn"
          role="status"
          aria-live="polite"
        >
          <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          <span className="text-sm font-semibold">{successToast}</span>
        </div>
      )}

      {/* Modal de Edição de Órgão (Integrado ao backend PATCH /api/v1/agencies/{id}) */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setEditingAgency(null);
        }}
        title={`Editar Órgão: ${editingAgency?.acronym || ""}`}
      >
        <form onSubmit={handleSaveEdit} className="space-y-4">
          {editError && (
            <div className="p-3 bg-red-50 border-l-4 border-red-500 rounded text-xs text-red-700 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-red-500" />
              <span>{editError}</span>
            </div>
          )}

          <Input
            label="Sigla Oficial"
            id="edit-agency-acronym"
            placeholder="Ex.: DETRAN, SEFAZ, SEMED"
            value={editForm.acronym}
            onChange={(e) => setEditForm({ ...editForm, acronym: e.target.value })}
            required
            helperText="Identificador siglar público do órgão"
          />

          <Input
            label="Nome Completo do Órgão"
            id="edit-agency-name"
            placeholder="Ex.: Departamento Estadual de Trânsito de Alagoas"
            value={editForm.name}
            onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
            required
          />

          <Select
            label="Esfera Governamental"
            id="edit-agency-sphere"
            value={editForm.sphere}
            onChange={(e) =>
              setEditForm({ ...editForm, sphere: e.target.value as Agency["sphere"] })
            }
            options={[
              { value: "state", label: "Estadual" },
              { value: "municipal", label: "Municipal" },
              { value: "federal", label: "Federal" },
            ]}
          />

          <div>
            <label
              htmlFor="edit-agency-desc"
              className="block text-sm font-semibold text-gray-700 mb-1.5"
            >
              Descrição Institucional
            </label>
            <textarea
              id="edit-agency-desc"
              rows={3}
              value={editForm.description}
              onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
              placeholder="Competências e finalidade do órgão..."
              className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <Button
              type="button"
              variant="secondary"
              disabled={isSavingEdit}
              onClick={() => {
                setIsEditModalOpen(false);
                setEditingAgency(null);
              }}
            >
              Cancelar
            </Button>
            <Button type="submit" variant="primary" isLoading={isSavingEdit}>
              Salvar Alterações
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

