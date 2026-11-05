import React from "react";
import Link from "next/link";

export const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-[#CBD2DC] mt-16 py-8 text-xs text-[#4A5568]">
      <div className="max-w-[1200px] mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <p className="font-semibold text-[#101828]">
            SOSP — Sistema de Orientação para Serviços Públicos
          </p>
          <p className="text-[#667085] mt-1">
            Governo do Estado de Alagoas · Parceria CESMAC
          </p>
        </div>

        <nav aria-label="Links institucionais do rodapé" className="flex flex-wrap items-center gap-6">
          <Link href="/acessibilidade" className="hover:underline">
            Acessibilidade
          </Link>
          <Link href="/privacidade" className="hover:underline">
            Privacidade e LGPD
          </Link>
          <Link href="/termos" className="hover:underline">
            Termos de Uso
          </Link>
          <Link href="https://www.gov.br" target="_blank" rel="noopener noreferrer" className="font-bold hover:underline">
            gov.br
          </Link>
        </nav>
      </div>
    </footer>
  );
};

