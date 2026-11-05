"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  MapPin,
  Plus,
  Search,
  CheckCircle2,
  XCircle,
  Building,
  ChevronRight,
  Trash2,
  Clock,
  Users,
  Accessibility,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Tag } from "@/components/ui/Tag";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Modal } from "@/components/ui/Modal";
import { CriticalConfirmationModal } from "@/components/ui/CriticalConfirmationModal";
import { getUnits, getAgencies } from "@/services/apiClient";
import type { Unit, Agency } from "@/types/api";

export default function AdminUnitsPage() {
  const [units, setUnits] = useState<Unit[]>([]);
  const [agencies, setAgencies] = useState<Agency[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [deactivatingUnit, setDeactivatingUnit] = useState<Unit | null>(null);

  const [newUnit, setNewUnit] = useState({
    name: "",
    agencyId: "",
    street: "",
    number: "",
    neighborhood: "",
    city: "Maceió",
    state: "AL",
    cep: "",
    openingHours: "08:00 às 17:00",
    dailyLimit: 60,
    isPcdAccessible: true,
  });

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      try {
        const [loadedUnits, loadedAgencies] = await Promise.all([
          getUnits(),
          getAgencies(),
        ]);
        setUnits(loadedUnits);
        setAgencies(loadedAgencies);
        if (loadedAgencies.length > 0) {
          setNewUnit((prev) => ({ ...prev, agencyId: loadedAgencies[0].id }));
        }
      } catch (err) {
        console.error("Erro ao carregar unidades:", err);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  const handleCreateUnit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUnit.name || !newUnit.street) return;

    const created: Unit = {
      id: `unit-${Date.now()}`,
      agencyId: newUnit.agencyId,
      name: newUnit.name,
      cep: newUnit.cep || "57000-000",
      street: newUnit.street,
      number: newUnit.number || "S/N",
      neighborhood: newUnit.neighborhood || "Centro",
      city: newUnit.city,
      state: newUnit.state,
      openingHours: newUnit.openingHours,
      dailyLimit: Number(newUnit.dailyLimit),
      isPcdAccessible: newUnit.isPcdAccessible,
      hasPriorityService: true,
      isActive: true,
    };

    setUnits((prev) => [created, ...prev]);
    setIsCreateModalOpen(false);
  };

  const handleConfirmDeactivate = () => {
    if (!deactivatingUnit) return;
    setUnits((prev) =>
      prev.map((u) =>
        u.id === deactivatingUnit.id ? { ...u, isActive: false } : u
      )
    );
    setDeactivatingUnit(null);
  };

  const filteredUnits = units.filter((u) => {
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      return (
        u.name.toLowerCase().includes(q) ||
        u.city.toLowerCase().includes(q) ||
        u.neighborhood.toLowerCase().includes(q)
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
            Unidades de Atendimento (RF-04)
          </span>
        </nav>

        {/* Topo com Ações */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200 mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-emerald-50 text-emerald-700 rounded-2xl flex items-center justify-center">
              <MapPin className="w-8 h-8" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-700">
                Gestão de Infraestrutura SOSP
              </span>
              <h1 className="text-2xl font-extrabold text-gray-900 mt-0.5">
                Unidades e Postos Presenciais
              </h1>
              <p className="text-xs text-gray-500 mt-0.5">
                Centrais Já!, postos de atendimento, limites de vagas diárias e acessibilidade
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/admin/orgaos">
              <Button variant="secondary" className="text-xs">
                <Building className="w-4 h-4 mr-1.5" />
                Órgãos
              </Button>
            </Link>
            <Button
              variant="primary"
              className="text-xs font-semibold shadow-md"
              onClick={() => setIsCreateModalOpen(true)}
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Nova Unidade
            </Button>
          </div>
        </div>

        {/* Busca */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-200 mb-8">
          <div className="relative w-full sm:w-96">
            <input
              type="search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar por nome da unidade, bairro ou cidade..."
              className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
            />
            <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          </div>
        </div>

        {/* Grid de Unidades */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredUnits.map((unit) => (
            <div
              key={unit.id}
              className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200 hover:border-emerald-300 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <Tag variant={unit.isActive ? "success" : "danger"}>
                    {unit.isActive ? "Ativa" : "Desativada"}
                  </Tag>
                  {unit.isPcdAccessible && (
                    <span className="flex items-center gap-1 text-[11px] font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-md">
                      <Accessibility className="w-3.5 h-3.5" />
                      Acessível PCD
                    </span>
                  )}
                </div>

                <h3 className="text-lg font-bold text-gray-900 mb-1">{unit.name}</h3>
                <p className="text-xs text-gray-600 mb-4">
                  {unit.street}, {unit.number} — {unit.neighborhood}, {unit.city}/{unit.state}
                </p>

                <div className="space-y-2 text-xs text-gray-500 pt-3 border-t border-gray-100">
                  <div className="flex items-center gap-2">
                    <Clock className="w-3.5 h-3.5 text-gray-400" />
                    <span>Expediente: {unit.openingHours}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users className="w-3.5 h-3.5 text-gray-400" />
                    <span>Capacidade: <strong>{unit.dailyLimit} vagas/dia</strong></span>
                  </div>
                </div>
              </div>

              <div className="pt-4 mt-4 border-t border-gray-100 flex justify-end">
                {unit.isActive && (
                  <Button
                    variant="danger"
                    className="text-xs py-1 px-3"
                    onClick={() => setDeactivatingUnit(unit)}
                  >
                    <Trash2 className="w-3.5 h-3.5 mr-1" />
                    Desativar
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Modal de Criação de Unidade */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Cadastrar Nova Unidade de Atendimento"
      >
        <form onSubmit={handleCreateUnit} className="space-y-4">
          <Input
            label="Nome da Unidade"
            id="unit-name"
            placeholder="Ex.: Central Já! Shopping Pátio Maceió"
            value={newUnit.name}
            onChange={(e) => setNewUnit({ ...newUnit, name: e.target.value })}
            required
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Logradouro"
              id="unit-street"
              placeholder="Rua, Av..."
              value={newUnit.street}
              onChange={(e) => setNewUnit({ ...newUnit, street: e.target.value })}
              required
            />
            <Input
              label="Número"
              id="unit-num"
              placeholder="123 ou S/N"
              value={newUnit.number}
              onChange={(e) => setNewUnit({ ...newUnit, number: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Bairro"
              id="unit-neigh"
              placeholder="Bairro"
              value={newUnit.neighborhood}
              onChange={(e) => setNewUnit({ ...newUnit, neighborhood: e.target.value })}
              required
            />
            <Input
              label="Cidade"
              id="unit-city"
              value={newUnit.city}
              onChange={(e) => setNewUnit({ ...newUnit, city: e.target.value })}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Horário de Atendimento"
              id="unit-hours"
              placeholder="08:00 às 17:00"
              value={newUnit.openingHours}
              onChange={(e) => setNewUnit({ ...newUnit, openingHours: e.target.value })}
            />
            <Input
              label="Capacidade Diária (Vagas)"
              id="unit-cap"
              type="number"
              value={String(newUnit.dailyLimit)}
              onChange={(e) => setNewUnit({ ...newUnit, dailyLimit: Number(e.target.value) })}
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
              Salvar Unidade
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal de Desativação Lógica */}
      <CriticalConfirmationModal
        isOpen={Boolean(deactivatingUnit)}
        onClose={() => setDeactivatingUnit(null)}
        onConfirm={handleConfirmDeactivate}
        title="Desativar Unidade de Atendimento"
        description={`Confirma a desativação da unidade ${deactivatingUnit?.name}? Novos agendamentos presenciais para este endereço serão bloqueados (RN-40).`}
        confirmText="Sim, Desativar Unidade"
        cancelText="Voltar"
        isDestructive={true}
      />
    </div>
  );
}

