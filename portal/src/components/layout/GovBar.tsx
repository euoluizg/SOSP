import React from "react";
import Link from "next/link";

export const GovBar: React.FC = () => {
  return (
    <div className="bg-[#0C326F] text-white text-xs py-1.5 px-4 border-b border-[#082046]">
      <div className="max-w-[1200px] mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-bold text-xs tracking-wide text-white/95">
            SOSP • Sistema de Orientação para Serviços Públicos
          </span>
          <span className="hidden sm:inline-block text-[11px] text-white/70 bg-white/10 px-2 py-0.5 rounded-full font-medium">
            Projeto Acadêmico CESMAC
          </span>
        </div>

        <nav aria-label="Acessibilidade rápida" className="flex items-center gap-3 sm:gap-4 text-xs">
          <Link href="#conteudo-principal" className="hover:underline text-white/90">
            Ir para o conteúdo
          </Link>
          <span className="opacity-40" aria-hidden="true">|</span>
          <Link href="/acessibilidade" className="hover:underline text-white/90">
            Acessibilidade
          </Link>
          <span className="opacity-40" aria-hidden="true">|</span>
          <Link href="/ajuda" className="hover:underline text-white/90 font-medium">
            Ajuda
          </Link>
        </nav>
      </div>
    </div>
  );
};
