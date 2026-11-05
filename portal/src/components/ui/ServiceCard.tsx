import React from "react";
import Link from "next/link";
import { Service } from "@/types/api";
import { Tag } from "./Tag";

export interface ServiceCardProps {
  service: Service;
}

export const ServiceCard: React.FC<ServiceCardProps> = ({ service }) => {
  const channelLabels = {
    online: "Online",
    inPerson: "Presencial",
    hybrid: "Híbrido",
  };

  const costLabel = service.isFree ? "Gratuito" : `R$ ${service.costAmount?.toFixed(2).replace(".", ",")}`;
  const deadlineLabel = service.averageDeadlineDays === 0 ? "Imediato" : `Até ${service.averageDeadlineDays} dias`;

  return (
    <div className="flex flex-col justify-between rounded-lg border border-[#CBD2DC] bg-white p-5 shadow-sm hover:border-[#1351B4] hover:shadow-md transition-all">
      <div>
        {/* Tags de Canal e Categoria */}
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <Tag channel={service.channel} label={channelLabels[service.channel]} />
          <span className="text-xs font-medium text-[#4A5568] bg-[#F1F3F6] px-2.5 py-1 rounded-full border border-[#CBD2DC]">
            {service.category}
          </span>
        </div>

        {/* Nome do Serviço */}
        <h3 className="text-base font-bold text-[#101828] line-clamp-2 mb-1 hover:text-[#1351B4]">
          <Link href={`/servicos/${service.id}`} className="focus-visible:outline-none focus-visible:underline">
            {service.name}
          </Link>
        </h3>

        {/* Órgão Responsável */}
        <p className="text-xs font-semibold text-[#4A5568] mb-2">
          {service.agencyAcronym} · {service.agencyName}
        </p>

        {/* Descrição Curta */}
        <p className="text-xs text-[#667085] line-clamp-2 mb-4 leading-relaxed">
          {service.summary}
        </p>
      </div>

      <div>
        <hr className="border-[#F1F3F6] my-3" />

        {/* Metadados: Custo · Prazo · Unidades e Ação */}
        <div className="flex items-center justify-between text-xs text-[#4A5568]">
          <div className="flex flex-wrap items-center gap-1.5 font-medium">
            <span>{costLabel}</span>
            <span aria-hidden="true">·</span>
            <span>{deadlineLabel}</span>
            {service.unitCount > 0 && (
              <>
                <span aria-hidden="true">·</span>
                <span>{service.unitCount} {service.unitCount === 1 ? "unidade" : "unidades"}</span>
              </>
            )}
          </div>

          <Link
            href={`/servicos/${service.id}`}
            className="text-xs font-bold text-[#1351B4] hover:underline min-h-[36px] inline-flex items-center gap-1"
            aria-label={`Ver ficha orientativa de ${service.name}`}
          >
            Abrir serviço
            <span aria-hidden="true">→</span>
          </Link>
        </div>
      </div>
    </div>
  );
};

