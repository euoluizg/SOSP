import React from "react";
import Link from "next/link";
import { ExternalLink } from "lucide-react";

export const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-[#CBD2DC] mt-16 py-8 text-xs text-[#4A5568]">
      <div className="max-w-[1200px] mx-auto px-4 space-y-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <p className="font-bold text-sm text-[#101828]">
              SOSP — Sistema de Orientação para Serviços Públicos
            </p>
            <p className="text-[#1351B4] font-medium mt-1">
              Projeto acadêmico desenvolvido por estudantes do CESMAC.
            </p>
            <p className="text-gray-500 text-[11px] mt-1 max-w-xl leading-relaxed">
              Aviso institucional: O SOSP é um projeto de pesquisa e extensão acadêmica do curso de
              Engenharia de Software do Centro Universitário CESMAC. Esta plataforma não representa
              um canal oficial do governo estadual ou federal.
            </p>
          </div>

          <nav aria-label="Links institucionais do rodapé" className="flex flex-wrap items-center gap-6">
            <Link href="/ajuda" className="hover:text-[#1351B4] hover:underline transition-colors">
              Ajuda
            </Link>
            <Link href="/acessibilidade" className="hover:text-[#1351B4] hover:underline transition-colors">
              Acessibilidade
            </Link>
            <Link href="/privacidade" className="hover:text-[#1351B4] hover:underline transition-colors">
              Privacidade e LGPD
            </Link>
            <Link href="/termos" className="hover:text-[#1351B4] hover:underline transition-colors">
              Termos de Uso
            </Link>
            <Link
              href="https://www.gov.br"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 font-bold text-[#1351B4] hover:underline transition-colors"
              title="Acesso ao portal oficial Gov.br (abre em nova aba)"
            >
              <span>Portal Gov.br</span>
              <ExternalLink className="w-3 h-3" />
            </Link>
          </nav>
        </div>

        <div className="border-t border-gray-100 pt-4 text-center md:text-left text-[11px] text-gray-400">
          © {new Date().getFullYear()} SOSP · Centro Universitário CESMAC · Todos os direitos reservados para fins acadêmicos.
        </div>
      </div>
    </footer>
  );
};
