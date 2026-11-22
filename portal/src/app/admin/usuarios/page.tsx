"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Users,
  Plus,
  Search,
  Trash2,
  ChevronRight,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Tag } from "@/components/ui/Tag";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Modal } from "@/components/ui/Modal";
import { CriticalConfirmationModal } from "@/components/ui/CriticalConfirmationModal";
import {
  getInternalUsers,
  createInternalUser,
  deactivateInternalUser,
  getAgencies,
  getUnits,
} from "@/services/apiClient";
import type { Agency, Unit, ProblemDetails } from "@/types/api";

interface InternalUser {
  id: string;
  name: string;
  email: string;
  cpfMasked: string;
  registrationNumber: string;
  agencyName: string;
  role: "attendant" | "manager" | "admin";
  canManageCatalog: boolean;
  isActive: boolean;
}

function normalizeRoleForUi(role: string): InternalUser["role"] {
  if (role === "admin" || role === "superadmin" || role === "administrator") return "admin";
  if (role === "manager" || role === "gestor") return "manager";
  return "attendant";
}

function roleUiToApi(role: InternalUser["role"]): string {
  if (role === "admin") return "admin";
  if (role === "manager") return "gestor";
  return "server";
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<InternalUser[]>([]);
  const [agencies, setAgencies] = useState<Agency[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [deactivatingUser, setDeactivatingUser] = useState<InternalUser | null>(null);

  const [newUser, setNewUser] = useState({
    name: "",
    email: "",
    cpf: "",
    registrationNumber: "",
    agencyId: "",
    unitId: "",
    temporaryPassword: "",
    role: "attendant" as InternalUser["role"],
    canManageCatalog: false,
  });

  useEffect(() => {
    let active = true;
    async function load() {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        const [loadedUsers, loadedAgencies, loadedUnits] = await Promise.all([
          getInternalUsers(),
          getAgencies(),
          getUnits(),
        ]);
        if (!active) return;
        setAgencies(loadedAgencies);
        setUnits(loadedUnits);
        const agencyMap = new Map(loadedAgencies.map((a) => [a.id, a.name]));
        setUsers(
          loadedUsers.map((u) => ({
            id: u.id,
            name: u.fullName,
            email: u.email,
            cpfMasked: u.cpfMasked,
            registrationNumber: u.registrationNumber,
            agencyName: (u.agencyId && agencyMap.get(u.agencyId)) || "Administração Geral SOSP",
            role: normalizeRoleForUi(u.role),
            canManageCatalog: u.canManageCatalog,
            isActive: u.isActive,
          }))
        );
      } catch (err: unknown) {
        if (!active) return;
        const problem = err as ProblemDetails;
        setErrorMessage(problem?.detail || "Não foi possível carregar os usuários internos.");
      } finally {
        if (active) setIsLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUser.name || !newUser.email || !newUser.cpf || !newUser.registrationNumber) return;
    setErrorMessage(null);

    try {
      const created = await createInternalUser({
        fullName: newUser.name.trim(),
        cpf: newUser.cpf.replace(/\D/g, ""),
        email: newUser.email.trim(),
        registrationNumber: newUser.registrationNumber.trim().toUpperCase(),
        role: roleUiToApi(newUser.role),
        agencyId: newUser.agencyId || null,
        unitId: newUser.unitId || null,
        canManageCatalog: newUser.canManageCatalog,
        temporaryPassword: newUser.temporaryPassword || undefined,
      });
      const agencyName =
        agencies.find((a) => a.id === created.agencyId)?.name || "Administração Geral SOSP";
      setUsers((prev) => [
        {
          id: created.id,
          name: created.fullName,
          email: created.email,
          cpfMasked: created.cpfMasked,
          registrationNumber: created.registrationNumber,
          agencyName,
          role: normalizeRoleForUi(created.role),
          canManageCatalog: created.canManageCatalog,
          isActive: created.isActive,
        },
        ...prev,
      ]);
      setIsCreateModalOpen(false);
      setNewUser({
        name: "",
        email: "",
        cpf: "",
        registrationNumber: "",
        agencyId: "",
        unitId: "",
        temporaryPassword: "",
        role: "attendant",
        canManageCatalog: false,
      });
    } catch (err: unknown) {
      const problem = err as ProblemDetails;
      setErrorMessage(problem?.detail || "Erro ao cadastrar usuário interno.");
    }
  };

  const handleConfirmDeactivate = async () => {
    if (!deactivatingUser) return;
    try {
      await deactivateInternalUser(deactivatingUser.id);
      setUsers((prev) =>
        prev.map((u) =>
          u.id === deactivatingUser.id ? { ...u, isActive: false } : u
        )
      );
    } catch (err: unknown) {
      const problem = err as ProblemDetails;
      setErrorMessage(problem?.detail || "Erro ao revogar acesso do usuário.");
    } finally {
      setDeactivatingUser(null);
    }
  };

  const filteredUsers = users.filter((u) => {
    if (roleFilter !== "all" && u.role !== roleFilter) return false;
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      return (
        u.name.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q) ||
        u.agencyName.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const getRoleBadge = (role: InternalUser["role"]) => {
    switch (role) {
      case "admin":
        return { label: "Administrador Geral", variant: "danger" as const };
      case "manager":
        return { label: "Gestor da Unidade", variant: "warning" as const };
      case "attendant":
        return { label: "Atendente Operacional", variant: "info" as const };
    }
  };

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
            Usuários Internos e RBAC (RF-12)
          </span>
        </nav>

        {/* Topo */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200 mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-purple-50 text-purple-700 rounded-2xl flex items-center justify-center">
              <Users className="w-8 h-8" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-purple-700">
                Governança de Acessos SOSP
              </span>
              <h1 className="text-2xl font-extrabold text-gray-900 mt-0.5">
                Usuários Internos & Servidores
              </h1>
              <p className="text-xs text-gray-500 mt-0.5">
                Atendentes, gestores de órgãos e administradores do sistema com matriz RBAC (ADR-003)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="primary"
              className="text-xs font-semibold shadow-md"
              onClick={() => setIsCreateModalOpen(true)}
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Novo Usuário Interno
            </Button>
          </div>
        </div>

        {/* Busca e Filtros */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-200 mb-8 flex flex-col sm:flex-row gap-4 justify-between items-center">
          <div className="relative w-full sm:w-96">
            <input
              type="search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar por nome, e-mail ou órgão..."
              className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
            />
            <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <span className="text-xs text-gray-500">Perfil:</span>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="py-2 px-3 text-xs rounded-xl border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
            >
              <option value="all">Todos os papéis</option>
              <option value="attendant">Atendentes</option>
              <option value="manager">Gestores</option>
              <option value="admin">Administradores</option>
            </select>
          </div>
        </div>

        {/* Tabela de Usuários */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-gray-600">
                  <th className="py-3.5 px-6 font-semibold">Nome do Servidor</th>
                  <th className="py-3.5 px-6 font-semibold">Lotação / Órgão</th>
                  <th className="py-3.5 px-6 font-semibold">Papel RBAC</th>
                  <th className="py-3.5 px-6 font-semibold">Status</th>
                  <th className="py-3.5 px-6 font-semibold text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredUsers.map((user) => {
                  const roleBadge = getRoleBadge(user.role);
                  return (
                    <tr key={user.id} className="hover:bg-gray-50/70 transition-colors">
                      <td className="py-4 px-6">
                        <span className="font-bold text-gray-900 block">{user.name}</span>
                        <span className="text-xs text-gray-500">{user.email}</span>
                      </td>
                      <td className="py-4 px-6 text-gray-700">{user.agencyName}</td>
                      <td className="py-4 px-6">
                        <Tag variant={roleBadge.variant}>{roleBadge.label}</Tag>
                        {user.canManageCatalog && (
                          <span className="block text-[10px] font-semibold text-[#1351B4] mt-1">
                            ✓ Edita Catálogo (RN-35)
                          </span>
                        )}
                      </td>
                      <td className="py-4 px-6">
                        <Tag variant={user.isActive ? "success" : "danger"}>
                          {user.isActive ? "Ativo" : "Desativado"}
                        </Tag>
                      </td>
                      <td className="py-4 px-6 text-right">
                        {user.isActive && (
                          <Button
                            variant="danger"
                            className="text-xs py-1 px-3"
                            onClick={() => setDeactivatingUser(user)}
                          >
                            <Trash2 className="w-3.5 h-3.5 mr-1" />
                            Revogar Acesso
                          </Button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Modal de Criação de Usuário */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Cadastrar Novo Servidor ou Administrador"
      >
        <form onSubmit={handleCreateUser} className="space-y-4">
          <Input
            label="Nome Completo"
            id="u-name"
            placeholder="Nome do servidor"
            value={newUser.name}
            onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
            required
          />

          <Input
            label="E-mail Institucional"
            id="u-email"
            type="email"
            placeholder="servidor@sosp.al.gov.br"
            value={newUser.email}
            onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
            required
          />

          <Input
            label="CPF (11 dígitos)"
            id="u-cpf"
            placeholder="000.000.000-00"
            value={newUser.cpf}
            onChange={(e) => setNewUser({ ...newUser, cpf: e.target.value })}
            required
          />

          <Input
            label="Matrícula Funcional"
            id="u-reg"
            placeholder="Ex: SSP-2026"
            value={newUser.registrationNumber}
            onChange={(e) => setNewUser({ ...newUser, registrationNumber: e.target.value })}
            required
          />

          <Select
            label="Órgão de Lotação"
            id="u-agency"
            value={newUser.agencyId}
            onChange={(e) => setNewUser({ ...newUser, agencyId: e.target.value })}
            options={[
              { value: "", label: "Administração Geral SOSP (sem vínculo exclusivo)" },
              ...agencies.map((a) => ({ value: a.id, label: `${a.acronym} — ${a.name}` })),
            ]}
          />

          <Select
            label="Unidade de Atendimento (opcional)"
            id="u-unit"
            value={newUser.unitId}
            onChange={(e) => setNewUser({ ...newUser, unitId: e.target.value })}
            options={[
              { value: "", label: "Nenhuma unidade específica" },
              ...units.map((u) => ({ value: u.id, label: `${u.name} (${u.city})` })),
            ]}
          />

          <Input
            label="Senha Provisória (opcional — gerada com troca obrigatória)"
            id="u-pwd"
            type="password"
            placeholder="Deixe vazio para gerar automaticamente"
            value={newUser.temporaryPassword}
            onChange={(e) => setNewUser({ ...newUser, temporaryPassword: e.target.value })}
          />

          <Select
            label="Papel RBAC"
            id="u-role"
            value={newUser.role}
            onChange={(e) =>
              setNewUser({ ...newUser, role: e.target.value as InternalUser["role"] })
            }
            options={[
              { value: "attendant", label: "Atendente (Fila e Triagem)" },
              { value: "manager", label: "Gestor de Unidade (Relatórios e Escalas)" },
              { value: "admin", label: "Administrador Global (Acesso Total)" },
            ]}
          />

          <label className="flex items-center gap-2 pt-2 cursor-pointer">
            <input
              type="checkbox"
              checked={newUser.canManageCatalog}
              onChange={(e) => setNewUser({ ...newUser, canManageCatalog: e.target.checked })}
              className="w-4 h-4 text-[#1351B4] rounded"
            />
            <span className="text-xs text-gray-700 font-semibold">
              Permitir gerenciar e publicar fichas do catálogo de serviços (RN-35)
            </span>
          </label>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsCreateModalOpen(false)}
            >
              Cancelar
            </Button>
            <Button type="submit" variant="primary">
              Cadastrar Servidor
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal de Desativação */}
      <CriticalConfirmationModal
        isOpen={Boolean(deactivatingUser)}
        onClose={() => setDeactivatingUser(null)}
        onConfirm={handleConfirmDeactivate}
        title="Revogar Acesso do Servidor"
        description={`Confirma a revogação de acesso de ${deactivatingUser?.name} (${deactivatingUser?.email})? A exclusão é lógica (isActive = false) para manter a rastreabilidade imutável de auditoria (RN-40).`}
        confirmText="Revogar Acesso"
        cancelText="Voltar"
        isDestructive={true}
      />
    </div>
  );
}

