"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  Search,
  Download,
  ChevronRight,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Tag } from "@/components/ui/Tag";
import { Skeleton } from "@/components/ui/Skeleton";
import { getAuditEvents } from "@/services/apiClient";
import type { ProblemDetails } from "@/types/api";

interface AuditLog {
  id: string;
  actor: string;
  action: "CREATE" | "UPDATE" | "DEACTIVATE" | "LOGIN" | "CANCEL";
  targetTable: string;
  targetId: string;
  ipAddress: string;
  timestamp: string;
  details: string;
}

function normalizeAuditAction(raw: string): AuditLog["action"] {
  const upper = (raw || "").toUpperCase();
  if (upper.includes("CREATE")) return "CREATE";
  if (upper.includes("DEACTIVATE") || upper.includes("DELETE")) return "DEACTIVATE";
  if (upper.includes("CANCEL")) return "CANCEL";
  if (upper.includes("LOGIN") || upper.includes("AUTH")) return "LOGIN";
  return "UPDATE";
}

export default function AdminAuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [actionFilter, setActionFilter] = useState("all");

  useEffect(() => {
    let active = true;
    async function load() {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        const events = await getAuditEvents();
        if (!active) return;
        setLogs(
          events.map((e) => ({
            id: e.id,
            actor: e.actorUserId || "system",
            action: normalizeAuditAction(e.action),
            targetTable: e.targetTable,
            targetId: e.targetId || "-",
            ipAddress: e.ipAddress || "127.0.0.1",
            timestamp: e.createdAt,
            details: e.detail || e.action,
          }))
        );
      } catch (err: unknown) {
        if (!active) return;
        const problem = err as ProblemDetails;
        setErrorMessage(problem?.detail || "Não foi possível carregar os registros de auditoria.");
      } finally {
        if (active) setIsLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  const filteredLogs = logs.filter((log) => {
    if (actionFilter !== "all" && log.action !== actionFilter) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        log.actor.toLowerCase().includes(q) ||
        log.targetTable.toLowerCase().includes(q) ||
        log.targetId.toLowerCase().includes(q) ||
        log.details.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const getActionBadge = (action: AuditLog["action"]) => {
    switch (action) {
      case "CREATE":
        return { label: "Criação (CREATE)", variant: "success" as const };
      case "UPDATE":
        return { label: "Edição (UPDATE)", variant: "info" as const };
      case "DEACTIVATE":
        return { label: "Desativação (LOGICAL)", variant: "danger" as const };
      case "LOGIN":
        return { label: "Autenticação", variant: "neutral" as const };
      case "CANCEL":
        return { label: "Cancelamento", variant: "warning" as const };
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
            Trilha Imutável de Auditoria (RS-03, RN-39)
          </span>
        </nav>

        {/* Topo */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200 mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-red-50 text-red-600 rounded-2xl flex items-center justify-center">
              <ShieldAlert className="w-8 h-8" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-red-600">
                Segurança & Conformidade LGPD
              </span>
              <h1 className="text-2xl font-extrabold text-gray-900 mt-0.5">
                Logs e Auditoria do Sistema
              </h1>
              <p className="text-xs text-gray-500 mt-0.5">
                Registros imutáveis de transações, mutações de dados e acessos de servidores (RN-39, RS-03)
              </p>
            </div>
          </div>

          <Button
            variant="secondary"
            onClick={() => window.print()}
            className="text-xs font-semibold shadow-xs"
          >
            <Download className="w-4 h-4 mr-1.5" />
            Exportar Trilha de Auditoria
          </Button>
        </div>

        {/* Busca e Filtros */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-200 mb-8 flex flex-col sm:flex-row gap-4 justify-between items-center">
          <div className="relative w-full sm:w-96">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por ator, tabela, ID ou detalhe..."
              className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
            />
            <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <span className="text-xs text-gray-500">Ação:</span>
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="py-2 px-3 text-xs rounded-xl border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
            >
              <option value="all">Todas as ações</option>
              <option value="CREATE">Criação (CREATE)</option>
              <option value="UPDATE">Edição (UPDATE)</option>
              <option value="DEACTIVATE">Desativação (LOGICAL)</option>
              <option value="CANCEL">Cancelamento (CANCEL)</option>
              <option value="LOGIN">Autenticação (LOGIN)</option>
            </select>
          </div>
        </div>

        {errorMessage && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2 text-sm text-red-700">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Tabela de Logs */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          {isLoading ? (
            <div className="p-6 space-y-3" aria-busy="true">
              <Skeleton className="h-10 w-full rounded-lg" />
              <Skeleton className="h-10 w-full rounded-lg" />
              <Skeleton className="h-10 w-full rounded-lg" />
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="p-10 text-center text-sm text-gray-500">
              Nenhum evento de auditoria registrado até o momento para os filtros selecionados.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs sm:text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50 text-gray-600">
                    <th className="py-3.5 px-6 font-semibold">Data / Hora (UTC)</th>
                    <th className="py-3.5 px-6 font-semibold">Ator Responsável</th>
                    <th className="py-3.5 px-6 font-semibold">Ação Executada</th>
                    <th className="py-3.5 px-6 font-semibold">Tabela / ID Alvo</th>
                    <th className="py-3.5 px-6 font-semibold">IP Origem</th>
                    <th className="py-3.5 px-6 font-semibold">Descrição do Evento</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 font-mono text-xs">
                  {filteredLogs.map((log) => {
                    const badge = getActionBadge(log.action);
                    return (
                      <tr key={log.id} className="hover:bg-gray-50/70 transition-colors">
                        <td className="py-3.5 px-6 text-gray-500 whitespace-nowrap">
                          {log.timestamp.replace("T", " ").replace("Z", "")}
                        </td>
                        <td className="py-3.5 px-6 font-sans font-semibold text-gray-900 whitespace-nowrap">
                          {log.actor}
                        </td>
                        <td className="py-3.5 px-6 font-sans">
                          <Tag variant={badge.variant}>{badge.label}</Tag>
                        </td>
                        <td className="py-3.5 px-6 text-indigo-700 font-semibold whitespace-nowrap">
                          {log.targetTable} ({log.targetId})
                        </td>
                        <td className="py-3.5 px-6 text-gray-600">{log.ipAddress}</td>
                        <td className="py-3.5 px-6 font-sans text-gray-700">{log.details}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

