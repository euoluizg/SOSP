import React from "react";
import Link from "next/link";

export const GovBar: React.FC = () => {
  return (
    <div className="bg-[#002776] text-white text-xs py-1.5 px-4">
      <div className="max-w-[1200px] mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="https://www.gov.br"
            target="_blank"
            rel="noopener noreferrer"
            className="font-bold tracking-wider hover:underline flex items-center gap-1.5"
            aria-label="Portal do Governo Brasileiro (abre em nova aba)"
          >
            <span className="font-extrabold text-sm tracking-tighter">BRASIL</span>
            <span className="text-[10px] opacity-80">· GOVERNO DE ALAGOAS</span>
          </Link>
        </div>

        <nav aria-label="Acessibilidade rápida" className="flex items-center gap-4 text-xs">
          <Link href="#conteudo-principal" className="hover:underline">
            Ir para o conteúdo
          </Link>
          <span className="opacity-40" aria-hidden="true">|</span>
          <Link href="/acessibilidade" className="hover:underline">
            Acessibilidade
          </Link>
          <span className="opacity-40" aria-hidden="true">|</span>
          <Link href="/ajuda" className="hover:underline">
            Ajuda
          </Link>
        </nav>
      </div>
    </div>
  );
};

