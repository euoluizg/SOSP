"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  X,
  ChevronRight,
  ArrowLeft,
  FileCheck,
  ShieldAlert,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { getAppointmentByProtocol } from "@/services/apiClient";
import type { Appointment } from "@/types/api";

export default function AttachDocumentsPage() {
  const params = useParams();
  const router = useRouter();
  const protocol = params?.protocol as string;

  const [appointment, setAppointment] = useState<Appointment | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      try {
        const data = await getAppointmentByProtocol(protocol);
        setAppointment(data);
      } catch (err) {
        console.error("Erro ao carregar dados do protocolo:", err);
      } finally {
        setIsLoading(false);
      }
    }
    if (protocol) load();
  }, [protocol]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMessage(null);
    if (!e.target.files) return;

    const files = Array.from(e.target.files);
    const validFiles: File[] = [];

    for (const file of files) {
      // Regra RS-04: apenas .pdf, .jpg, .png até 10 MB
      const isPdf = file.type === "application/pdf" || file.name.endsWith(".pdf");
      const isJpg = file.type === "image/jpeg" || file.name.endsWith(".jpg") || file.name.endsWith(".jpeg");
      const isPng = file.type === "image/png" || file.name.endsWith(".png");

      if (!isPdf && !isJpg && !isPng) {
        setErrorMessage(`O arquivo ${file.name} possui formato inválido. Permitido apenas PDF, JPG e PNG (Regra RS-04).`);
        return;
      }

      if (file.size > 10 * 1024 * 1024) {
        setErrorMessage(`O arquivo ${file.name} excede o limite máximo permitido de 10 MB (Regra RS-04).`);
        return;
      }

      validFiles.push(file);
    }

    setSelectedFiles((prev) => [...prev, ...validFiles]);
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUploadSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFiles.length === 0) {
      setErrorMessage("Selecione ao menos um arquivo para anexar.");
      return;
    }

    setIsUploading(true);
    setErrorMessage(null);

    // Simulação do upload com antivírus (ClamAV)
    setTimeout(() => {
      setIsUploading(false);
      setUploadSuccess(true);
    }, 1200);
  };

  if (isLoading) {
    return (
      <div className="max-w-[800px] mx-auto py-10 px-4">
        <Skeleton className="h-6 w-48 mb-4" />
        <Skeleton className="h-10 w-2/3 mb-6" />
        <Skeleton className="h-60 w-full rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[800px] mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center text-xs text-gray-500 mb-6" aria-label="Breadcrumb">
          <Link href="/" className="hover:text-[#1351B4]">Início</Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <Link href="/cidadao/meus-agendamentos" className="hover:text-[#1351B4]">Meus Agendamentos</Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <Link href={`/cidadao/protocolos/${protocol}`} className="hover:text-[#1351B4]">
            Protocolo {protocol}
          </Link>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <span className="font-semibold text-gray-900" aria-current="page">
            Anexar Documentos
          </span>
        </nav>

        {/* Topo */}
        <div className="mb-8">
          <Link
            href={`/cidadao/protocolos/${protocol}`}
            className="inline-flex items-center text-sm font-semibold text-[#1351B4] hover:underline mb-3"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Voltar para o protocolo
          </Link>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900">
            Anexar Documentos ao Protocolo
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            Protocolo: <strong>{protocol}</strong> • Serviço: {appointment?.serviceName}
          </p>
        </div>

        {uploadSuccess ? (
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-green-200 text-center animate-fadeIn">
            <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="w-10 h-10" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">
              Documentos Anexados com Sucesso!
            </h2>
            <p className="mt-2 text-sm text-gray-600 max-w-md mx-auto">
              Os arquivos foram verificados e incorporados à sua solicitação. O atendente terá acesso aos anexos durante a triagem.
            </p>
            <div className="mt-6 flex justify-center gap-3">
              <Link href={`/cidadao/protocolos/${protocol}`}>
                <Button variant="primary">Voltar ao Acompanhamento</Button>
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={handleUploadSubmit} className="space-y-6">
            {errorMessage && (
              <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded-md flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                <p className="text-sm text-red-700">{errorMessage}</p>
              </div>
            )}

            {/* Zona de Drop / Upload */}
            <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border-2 border-dashed border-gray-300 hover:border-[#1351B4] transition-colors text-center relative">
              <input
                type="file"
                id="doc-upload"
                multiple
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="w-14 h-14 bg-blue-50 text-[#1351B4] rounded-2xl flex items-center justify-center mx-auto mb-3">
                <Upload className="w-7 h-7" />
              </div>
              <h3 className="text-base font-bold text-gray-900">
                Arraste os arquivos aqui ou clique para selecionar
              </h3>
              <p className="mt-1 text-xs text-gray-500">
                Formatos permitidos: <strong>PDF, JPG e PNG</strong> até <strong>10 MB</strong> por arquivo (Regra RS-04)
              </p>
            </div>

            {/* Lista de Arquivos Selecionados */}
            {selectedFiles.length > 0 && (
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
                <h3 className="text-sm font-bold text-gray-900 mb-3">
                  Arquivos prontos para envio ({selectedFiles.length})
                </h3>
                <ul className="space-y-2">
                  {selectedFiles.map((file, idx) => (
                    <li
                      key={idx}
                      className="p-3 bg-gray-50 rounded-xl border border-gray-200 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <FileCheck className="w-5 h-5 text-green-600 shrink-0" />
                        <div>
                          <span className="text-sm font-semibold text-gray-900 block truncate max-w-xs sm:max-w-md">
                            {file.name}
                          </span>
                          <span className="text-xs text-gray-500">
                            {(file.size / (1024 * 1024)).toFixed(2)} MB
                          </span>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeFile(idx)}
                        className="text-gray-400 hover:text-red-600 p-1 rounded-md"
                        aria-label={`Remover arquivo ${file.name}`}
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Ações */}
            <div className="flex justify-end gap-3">
              <Link href={`/cidadao/protocolos/${protocol}`}>
                <Button variant="secondary">Cancelar</Button>
              </Link>
              <Button
                type="submit"
                variant="primary"
                isLoading={isUploading}
                disabled={selectedFiles.length === 0}
                className="px-8 shadow-sm"
              >
                Enviar Documentos
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

