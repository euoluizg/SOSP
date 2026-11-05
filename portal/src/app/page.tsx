"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { MOCK_SERVICES } from "@/mocks/demoData";
import { ServiceCard } from "@/components/ui/ServiceCard";
import { Button } from "@/components/ui/Button";

export default function HomePage() {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      router.push(`/servicos?q=${encodeURIComponent(searchTerm.trim())}`);
    } else {
      router.push("/servicos");
    }
  };

  const quickShortcuts = [
    { label: "Tirar RG", query: "tirar rg" },
    { label: "CNH", query: "CNH" },
    { label: "IPTU", query: "IPTU" },
    { label: "CadÚnico", query: "CadÚnico" },
    { label: "Saúde", query: "Saúde" },
    { label: "Agendamentos", query: "Agendamento" },
  ];

  return (
    <div className="sosp-container py-8 md:py-12">
      {/* Bloco Hero Principal */}
      <section className="bg-gradient-to-b from-[#EFF5FF] to-white rounded-2xl p-6 md:p-12 border border-[#1351B4]/20 shadow-xs mb-10">
        <div className="max-w-3xl">
          <span className="text-xs font-bold uppercase tracking-wider text-[#1351B4] bg-white px-3 py-1 rounded-full border border-[#1351B4]/20 inline-block mb-4">
            Portal do Cidadão
          </span>

          <h1 className="text-2xl md:text-4xl font-extrabold text-[#101828] tracking-tight leading-tight mb-3">
            O que você precisa resolver hoje?
          </h1>

          <p className="text-sm md:text-base text-[#4A5568] leading-relaxed mb-8">
            Encontre serviços públicos, acompanhe solicitações e organize seus atendimentos presenciais em um só lugar.
          </p>

          {/* Barra de Busca com Botão */}
          <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-2 max-w-2xl mb-4">
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#667085]">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Busque por serviço, órgão ou palavra-chave (ex: tirar rg)"
                className="w-full pl-11 pr-4 py-3 rounded-lg border border-[#CBD2DC] bg-white text-[#101828] text-sm focus-visible:outline-2 focus-visible:outline-[#1351B4] min-h-[48px] shadow-xs"
                aria-label="Buscar serviços por palavra-chave"
              />
            </div>
            <Button type="submit" variant="primary" size="lg" className="sm:w-auto w-full">
              Buscar
            </Button>
          </form>

          {/* Atalhos Rápidos */}
          <div className="flex flex-wrap items-center gap-2 pt-2">
            <span className="text-xs text-[#667085] font-semibold mr-1">Mais buscados:</span>
            {quickShortcuts.map((sc) => (
              <button
                key={sc.label}
                type="button"
                onClick={() => router.push(`/servicos?q=${encodeURIComponent(sc.query)}`)}
                className="text-xs font-semibold px-3 py-1.5 rounded-full bg-white border border-[#CBD2DC] text-[#4A5568] hover:border-[#1351B4] hover:text-[#1351B4] hover:bg-[#EFF5FF] transition-colors cursor-pointer"
              >
                {sc.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Grid de Serviços Mais Buscados */}
      <section className="mb-12">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl md:text-2xl font-bold text-[#101828]">
              Serviços mais buscados
            </h2>
            <p className="text-xs md:text-sm text-[#4A5568] mt-1">
              Orientações claras sobre o que levar, onde ir e prazos oficiais
            </p>
          </div>

          <Link
            href="/servicos"
            className="text-sm font-bold text-[#1351B4] hover:underline flex items-center gap-1"
          >
            Ver catálogo completo
            <span aria-hidden="true">→</span>
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {MOCK_SERVICES.slice(0, 3).map((service) => (
            <ServiceCard key={service.id} service={service} />
          ))}
        </div>
      </section>

      {/* Destaque Institucional — Como Funciona o SOSP */}
      <section className="bg-white rounded-xl border border-[#CBD2DC] p-6 md:p-8 shadow-xs">
        <h2 className="text-lg md:text-xl font-bold text-[#101828] mb-6">
          Como o SOSP ajuda você a economizar tempo
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex gap-4">
            <div className="w-10 h-10 rounded-lg bg-[#EFF5FF] text-[#1351B4] font-bold flex items-center justify-center shrink-0">
              1
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#101828] mb-1">Ficha Orientativa em 8 Blocos</h3>
              <p className="text-xs text-[#4A5568] leading-relaxed">
                Descubra o que é, quem tem direito, documentos obrigatórios e custos antes de sair de casa.
              </p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="w-10 h-10 rounded-lg bg-[#EFF5FF] text-[#1351B4] font-bold flex items-center justify-center shrink-0">
              2
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#101828] mb-1">Checklist Interativo & PDF</h3>
              <p className="text-xs text-[#4A5568] leading-relaxed">
                Marque os documentos que já tem e baixe a lista impressa para não esquecer nada no balcão.
              </p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="w-10 h-10 rounded-lg bg-[#EFF5FF] text-[#1351B4] font-bold flex items-center justify-center shrink-0">
              3
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#101828] mb-1">Agendamento & Protocolo</h3>
              <p className="text-xs text-[#4A5568] leading-relaxed">
                Escolha dia e horário em slots de 30 minutos e acompanhe a linha do tempo em tempo real.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

