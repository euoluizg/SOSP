"use client";

import React, { useState, useEffect, useMemo, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Search, X, ChevronRight } from "lucide-react";
import { Select } from "@/components/ui/Select";
import { ServiceCard } from "@/components/ui/ServiceCard";
import { Pagination } from "@/components/ui/Pagination";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { getServices, getAgencies } from "@/services/apiClient";
import type { Service, Agency, ServiceCategory, ServiceChannel } from "@/types/api";

function ServicesContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Estados locais sincronizados com a URL (RN-03)
  const initialQuery = searchParams.get("q") || "";
  const initialCategory = searchParams.get("categoria") || "";
  const initialAgency = searchParams.get("orgao") || "";
  const initialChannel = searchParams.get("canal") || "";
  const initialMunicipality = searchParams.get("municipio") || "";
  const initialPage = parseInt(searchParams.get("pagina") || "1", 10);

  const [query, setQuery] = useState(initialQuery);
  const [category, setCategory] = useState(initialCategory);
  const [agencyId, setAgencyId] = useState(initialAgency);
  const [channel, setChannel] = useState(initialChannel);
  const [municipality, setMunicipality] = useState(initialMunicipality);
  const [currentPage, setCurrentPage] = useState(initialPage);

  const [services, setServices] = useState<Service[]>([]);
  const [agencies, setAgencies] = useState<Agency[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Carrega serviços e órgãos
  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const [servicesRes, agenciesRes] = await Promise.all([
          getServices(),
          getAgencies(),
        ]);
        setServices(servicesRes.items);
        setAgencies(agenciesRes);
      } catch (err) {
        console.error("Erro ao carregar serviços:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  // Atualiza a URL quando os filtros mudam (RN-03)
  const updateUrlFilters = (newParams: Record<string, string | number>) => {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(newParams).forEach(([key, val]) => {
      if (val) {
        params.set(key, String(val));
      } else {
        params.delete(key);
      }
    });
    router.push(`/servicos?${params.toString()}`);
  };

  // Filtragem combinável por interseção (AND) conforme RN-04
  const filteredServices = useMemo(() => {
    return services.filter((svc) => {
      // 1. Busca por termo
      if (query.trim()) {
        const q = query.toLowerCase();
        const matchesName = svc.name.toLowerCase().includes(q);
        const matchesSummary = svc.summary.toLowerCase().includes(q);
        const matchesAgency =
          svc.agencyName.toLowerCase().includes(q) ||
          svc.agencyAcronym.toLowerCase().includes(q);
        if (!matchesName && !matchesSummary && !matchesAgency) return false;
      }
      // 2. Filtro de Categoria
      if (category && svc.category !== category) return false;
      // 3. Filtro de Órgão
      if (agencyId && svc.agencyId !== agencyId) return false;
      // 4. Filtro de Canal (online, inPerson, hybrid)
      if (channel && svc.channel !== channel) return false;
      // 5. Filtro de Município (RN-04 / D3)
      if (municipality) {
        const isCapitalOrRegional =
          municipality.toLowerCase() === "maceió" || municipality.toLowerCase() === "arapiraca";
        if (svc.channel === "inPerson" && !isCapitalOrRegional) {
          return false;
        }
      }

      return true;
    });
  }, [services, query, category, agencyId, channel, municipality]);

  // Paginação estrita de 10 itens por página (RN-05)
  const pageSize = 10;
  const totalPages = Math.ceil(filteredServices.length / pageSize) || 1;
  const paginatedServices = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredServices.slice(start, start + pageSize);
  }, [filteredServices, currentPage]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    updateUrlFilters({
      q: query,
      categoria: category,
      orgao: agencyId,
      canal: channel,
      municipio: municipality,
      pagina: 1,
    });
  };

  const clearFilters = () => {
    setQuery("");
    setCategory("");
    setAgencyId("");
    setChannel("");
    setMunicipality("");
    setCurrentPage(1);
    router.push("/servicos");
  };

  const hasActiveFilters = Boolean(query || category || agencyId || channel || municipality);

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[1200px] mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center text-xs text-gray-500 mb-6" aria-label="Breadcrumb">
          <a href="/" className="hover:text-[#1351B4]">Início</a>
          <ChevronRight className="w-3.5 h-3.5 mx-2 text-gray-400" />
          <span className="font-semibold text-gray-900" aria-current="page">
            Catálogo de Serviços
          </span>
        </nav>

        {/* Cabeçalho */}
        <div className="mb-8">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
            Serviços Públicos Disponíveis
          </h1>
          <p className="mt-2 text-sm text-gray-600 max-w-2xl">
            Encontre orientações completas, documentos necessários e agende atendimento presencial ou online.
          </p>
        </div>

        {/* Barra de Busca e Filtros Oficiais (RN-04) */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-200 mb-8">
          <form onSubmit={handleSearchSubmit} className="space-y-4">
            {/* Input de Busca */}
            <div className="relative">
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="O que você precisa hoje? Ex.: RG, CNH, IPTU, Vacina..."
                className="w-full pl-11 pr-4 py-3 rounded-xl border border-gray-300 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#1351B4] focus:border-[#1351B4] min-h-[44px]"
              />
              <Search className="w-5 h-5 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            </div>

            {/* Os 4 Filtros Combináveis (RN-04 / D3) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
              {/* Filtro 1: Categoria */}
              <Select
                label="Categoria"
                id="filter-category"
                value={category}
                onChange={(e) => {
                  setCategory(e.target.value);
                  setCurrentPage(1);
                  updateUrlFilters({ categoria: e.target.value, pagina: 1 });
                }}
                options={[
                  { value: "", label: "Todas as categorias" },
                  { value: "Documentos", label: "Documentos e Identificação" },
                  { value: "Transporte", label: "Transporte e Trânsito" },
                  { value: "Tributos", label: "Tributos e Finanças" },
                  { value: "Assistência Social", label: "Assistência Social" },
                  { value: "Saúde", label: "Saúde" },
                ]}
              />

              {/* Filtro 2: Órgão */}
              <Select
                label="Órgão Responsável"
                id="filter-agency"
                value={agencyId}
                onChange={(e) => {
                  setAgencyId(e.target.value);
                  setCurrentPage(1);
                  updateUrlFilters({ orgao: e.target.value, pagina: 1 });
                }}
                options={[
                  { value: "", label: "Todos os órgãos" },
                  ...agencies.map((ag) => ({
                    value: ag.id,
                    label: `${ag.acronym} - ${ag.name}`,
                  })),
                ]}
              />

              {/* Filtro 3: Canal (online, inPerson, hybrid) */}
              <Select
                label="Canal de Atendimento"
                id="filter-channel"
                value={channel}
                onChange={(e) => {
                  setChannel(e.target.value);
                  setCurrentPage(1);
                  updateUrlFilters({ canal: e.target.value, pagina: 1 });
                }}
                options={[
                  { value: "", label: "Todos os canais" },
                  { value: "online", label: "Online (100% digital)" },
                  { value: "inPerson", label: "Presencial (com agendamento)" },
                  { value: "hybrid", label: "Híbrido (digital e presencial)" },
                ]}
              />

              {/* Filtro 4: Município (RN-04 / D3) */}
              <Select
                label="Município"
                id="filter-municipality"
                value={municipality}
                onChange={(e) => {
                  setMunicipality(e.target.value);
                  setCurrentPage(1);
                  updateUrlFilters({ municipio: e.target.value, pagina: 1 });
                }}
                options={[
                  { value: "", label: "Todos os municípios" },
                  { value: "Maceió", label: "Maceió" },
                  { value: "Arapiraca", label: "Arapiraca" },
                  { value: "Rio Largo", label: "Rio Largo" },
                  { value: "Palmeira dos Índios", label: "Palmeira dos Índios" },
                  { value: "Penedo", label: "Penedo" },
                  { value: "União dos Palmares", label: "União dos Palmares" },
                  { value: "Delmiro Gouveia", label: "Delmiro Gouveia" },
                ]}
              />
            </div>

            {/* Ações e Resumo de Filtros */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-gray-100">
              <span className="text-xs text-gray-500 font-medium">
                {filteredServices.length}{" "}
                {filteredServices.length === 1
                  ? "serviço encontrado"
                  : "serviços encontrados"}
              </span>

              {hasActiveFilters && (
                <button
                  type="button"
                  onClick={clearFilters}
                  className="inline-flex items-center text-xs font-semibold text-red-600 hover:text-red-800 transition-colors"
                >
                  <X className="w-3.5 h-3.5 mr-1" />
                  Limpar todos os filtros
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Lista de Resultados / Estados de Carregamento / Erro Vazio (RN-13) */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((idx) => (
              <div
                key={idx}
                className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm"
              >
                <Skeleton className="h-5 w-24 mb-3" />
                <Skeleton className="h-7 w-3/4 mb-2" />
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-2/3 mb-6" />
                <div className="flex justify-between items-center pt-4 border-t border-gray-100">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-8 w-24 rounded-lg" />
                </div>
              </div>
            ))}
          </div>
        ) : filteredServices.length === 0 ? (
          // Mensagem literal MSG-01 conforme RN-13
          <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm">
            <EmptyState
              title="Nenhum serviço encontrado"
              description="Nenhum serviço encontrado. Tente outro termo ou categoria."
              actionLabel="Ver todos os serviços"
              onAction={clearFilters}
            />
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {paginatedServices.map((service) => (
                <ServiceCard key={service.id} service={service} />
              ))}
            </div>

            {/* Paginação Estrita (RN-05: 10 itens por página) */}
            {totalPages > 1 && (
              <div className="mt-10">
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={(page) => {
                    setCurrentPage(page);
                    updateUrlFilters({ pagina: page });
                    window.scrollTo({ top: 0, behavior: "smooth" });
                  }}
                />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function ServicesPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gray-500">Carregando catálogo...</div>}>
      <ServicesContent />
    </Suspense>
  );
}
