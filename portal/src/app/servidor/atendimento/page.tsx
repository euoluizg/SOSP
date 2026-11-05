"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  FileCheck,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Clock,
  User,
  MapPin,
  ArrowLeft,
  ChevronRight,
  Shield,
  Send,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Tag } from "@/components/ui/Tag";

export default function ServerAttendancePage() {
  const [protocolNumber, setProtocolNumber] = useState("20261105-1042");
  const [checkedDocs, setCheckedDocs] = useState<Record<string, boolean>>({
    doc1: true,
    doc2: true,
    doc3: false,
  });
  const [status, setStatus] = useState<"in_progress" | "completed" | "needs_doc">("in_progress");

  const documents = [
    { id: "doc1", name: "Certidão de Nascimento ou Casamento (Original e Cópia)" },
    { id: "doc2", name: "Comprovante de Residência Atualizado (últimos 90 dias)" },
    { id: "doc3", name: "Comprovante de Inscrição no CPF" },
  ];

  const handleToggle = (id: string) => {
    setCheckedDocs((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const allChecked = Object.values(checkedDocs).every(Boolean);

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[1000px] mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center text-xs text-gray-500 mb-6" aria-label="Breadcrumb">
          <Link href="/servidor/painel" className="hover:text-[#1351B4]">Painel do Servidor</Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <span className="font-semibold text-gray-900" aria-current="page">
            Atendimento de Protocolo (Tela 18 / RF-09)
          </span>
        </nav>

        {/* Topo */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200 mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Tag variant={status === "completed" ? "success" : "info"}>
                {status === "completed" ? "Atendimento Concluído" : "Em Atendimento"}
              </Tag>
              <span className="text-xs font-mono font-bold text-gray-500 bg-gray-100 px-2.5 py-0.5 rounded">
                Protocolo: {protocolNumber}
              </span>
            </div>
            <h1 className="text-2xl font-extrabold text-gray-900 mt-1">
              Emitir Carteira de Identidade Nacional (CIN)
            </h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Cidadão: <strong>Carlos Eduardo Santos (CPF ***.789.012-**)</strong>
            </p>
          </div>

          <Link href="/servidor/painel">
            <Button variant="secondary" className="text-xs">
              <ArrowLeft className="w-4 h-4 mr-1.5" />
              Voltar ao Painel
            </Button>
          </Link>
        </div>

        {status === "completed" ? (
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-green-200 text-center animate-fadeIn">
            <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="w-10 h-10" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Atendimento Finalizado com Sucesso!</h2>
            <p className="mt-2 text-sm text-gray-600 max-w-md mx-auto">
              A biometria e a documentação do cidadão foram validadas no sistema. O protocolo foi atualizado para status "Concluído".
            </p>
            <div className="mt-6">
              <Link href="/servidor/painel">
                <Button variant="primary">Retornar para a Fila</Button>
              </Link>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Checklist de Documentação Presencial */}
            <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <h2 className="text-lg font-bold text-gray-900 mb-2">
                Conferência de Documentos Físicos Apresentados
              </h2>
              <p className="text-xs text-gray-500 mb-6">
                Marque cada documento original verificado pelo atendente no guichê presencial.
              </p>

              <div className="space-y-3">
                {documents.map((doc) => {
                  const isChecked = Boolean(checkedDocs[doc.id]);
                  return (
                    <div
                      key={doc.id}
                      onClick={() => handleToggle(doc.id)}
                      className={`p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between select-none ${
                        isChecked
                          ? "bg-green-50/60 border-green-300"
                          : "bg-gray-50 hover:bg-gray-100/70 border-gray-200"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <FileCheck
                          className={`w-5 h-5 ${
                            isChecked ? "text-green-600" : "text-gray-400"
                          }`}
                        />
                        <span className="text-sm font-semibold text-gray-900">{doc.name}</span>
                      </div>
                      <span
                        className={`text-xs font-bold px-2.5 py-1 rounded-md ${
                          isChecked
                            ? "bg-green-100 text-green-800"
                            : "bg-gray-200 text-gray-600"
                        }`}
                      >
                        {isChecked ? "Conferido" : "Pendente"}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Ações do Atendente */}
            <div className="flex flex-col sm:flex-row justify-between gap-3 pt-2">
              <Button
                variant="secondary"
                onClick={() => alert("Solicitação de documento pendente enviada por e-mail (UC-12).")}
                className="text-amber-700 border-amber-300 hover:bg-amber-50"
              >
                Solicitar Complementação de Anexos
              </Button>

              <Button
                variant="primary"
                onClick={() => setStatus("completed")}
                disabled={!allChecked}
                className="px-8 shadow-md"
              >
                <CheckCircle2 className="w-4 h-4 mr-2" />
                Concluir e Emitir Documento
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

