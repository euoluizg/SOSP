"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Users,
  Plus,
  Search,
  Shield,
  Trash2,
  ChevronRight,
  Building,
  KeyRound,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Tag } from "@/components/ui/Tag";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Modal } from "@/components/ui/Modal";
import { CriticalConfirmationModal } from "@/components/ui/CriticalConfirmationModal";

interface InternalUser {
  id: string;
  name: string;
  email: string;
  cpfMasked: string;
  agencyName: string;
  role: "attendant" | "manager" | "admin";
  canManageCatalog: boolean;
  isActive: boolean;
}

const INITIAL_USERS: InternalUser[] = [
  {
    id: "user-1",
    name: "Arthur Franco",
    email: "arthur.franco@sosp.al.gov.br",
    cpfMasked: "***.789.012-**",
    agencyName: "Secretaria de Estado da Segurança Pública",
    role: "attendant",
    canManageCatalog: true,
    isActive: true,
  },
  {
    id: "user-2",
    name: "Mozart Melo",
    email: "mozart.melo@sosp.al.gov.br",
    cpfMasked: "***.123.456-**",
    agencyName: "Governo do Estado de Alagoas",
    role: "admin",
    canManageCatalog: true,
    isActive: true,
  },
  {
    id: "user-3",
    name: "Luiz Gustavo",
    email: "luiz.gustavo@sosp.al.gov.br",
    cpfMasked: "***.456.789-**",
    agencyName: "Central Já! Centro",
    role: "manager",
    canManageCatalog: false,
    isActive: true,
  },
  {
    id: "user-4",
    name: "Carlos Atendente",
    email: "carlos.atendimento@sosp.al.gov.br",
    cpfMasked: "***.987.654-**",
    agencyName: "DETRAN-AL",
    role: "attendant",
    canManageCatalog: false,
    isActive: false,
  },
];

export default function AdminUsersPage() {
  const [users, setUsers] = useState<InternalUser[]>(INITIAL_USERS);
  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [deactivatingUser, setDeactivatingUser] = useState<InternalUser | null>(null);

  const [newUser, setNewUser] = useState({
    name: "",
    email: "",
    cpf: "",
    agencyName: "Central Já! Centro",
    role: "attendant" as InternalUser["role"],
    canManageCatalog: false,
  });

  const handleCreateUser = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUser.name || !newUser.email) return;

    const created: InternalUser = {
      id: `user-${Date.now()}`,
      name: newUser.name,
      email: newUser.email,
      cpfMasked: "***.***.***-**",
      agencyName: newUser.agencyName,
      role: newUser.role,
      canManageCatalog: newUser.canManageCatalog,
      isActive: true,
    };

    setUsers((prev) => [created, ...prev]);
    setIsCreateModalOpen(false);
    setNewUser({
      name: "",
      email: "",
      cpf: "",
      agencyName: "Central Já! Centro",
      role: "attendant",
      canManageCatalog: false,
    });
  };

  const handleConfirmDeactivate = () => {
    if (!deactivatingUser) return;
    setUsers((prev) =>
      prev.map((u) =>
        u.id === deactivatingUser.id ? { ...u, isActive: false } : u
      )
    );
    setDeactivatingUser(null);
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
            label="Órgão de Lotação"
            id="u-agency"
            value={newUser.agencyName}
            onChange={(e) => setNewUser({ ...newUser, agencyName: e.target.value })}
            required
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

