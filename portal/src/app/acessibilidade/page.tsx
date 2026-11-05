"use client";

import React from "react";
import Link from "next/link";
import { Accessibility, CheckCircle2, ArrowLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function AccessibilityStatementPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-[850px] mx-auto bg-white rounded-2xl p-6 sm:p-10 shadow-sm border border-gray-200">
        <Link href="/" className="inline-flex items-center text-xs font-semibold text-[#1351B4] hover:underline mb-6">
          <ArrowLeft className="w-3.5 h-3.5 mr-1" />
          Voltar para a página inicial
        </Link>

        <div className="flex items-center gap-4 pb-6 border-b border-gray-100 mb-8">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-[#1351B4] flex items-center justify-center">
            <Accessibility className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-[#1351B4]">
              Conformidade eMAG & WCAG 2.1 AA
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 mt-0.5">
              Declaração de Acessibilidade Digital
            </h1>
          </div>
        </div>

        <div className="prose prose-sm max-w-none text-gray-700 space-y-6 text-sm leading-relaxed">
          <p>
            O <strong>SOSP (Sistema de Orientação para Serviços Públicos)</strong> foi projetado e
            desenvolvido com o compromisso de assegurar o acesso pleno e irrestrito a todos os
            cidadãos alagoanos, incluindo pessoas com deficiência visual, motora, auditiva ou
            cognitiva, em conformidade com o <strong>Modelo de Acessibilidade em Governo Eletrônico (eMAG)</strong> e
            as diretrizes <strong>WCAG 2.1 nível AA</strong> (Requisito Não-Funcional RNF-06).
          </p>

          <h2 className="text-lg font-bold text-gray-900 pt-2">Recursos Implementados na Interface</h2>
          <ul className="space-y-2 list-none pl-0">
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0 mt-0.5" />
              <span><strong>Navegação Integral por Teclado:</strong> Todos os elementos interativos (botões, links, abas, modais) são acionáveis via teclas <kbd className="px-1.5 py-0.5 bg-gray-100 border rounded text-xs">Tab</kbd>, <kbd className="px-1.5 py-0.5 bg-gray-100 border rounded text-xs">Enter</kbd> e <kbd className="px-1.5 py-0.5 bg-gray-100 border rounded text-xs">Esc</kbd>.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0 mt-0.5" />
              <span><strong>Atalho para o Conteúdo (Skip-Link):</strong> Permite que usuários de leitores de tela pulem cabeçalhos institucionais diretamente para o conteúdo principal.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0 mt-0.5" />
              <span><strong>Contraste Aprimorado (4.5:1 mínimo):</strong> Combinações de cores estritamente testadas com fundo branco e tons de azul governamental.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0 mt-0.5" />
              <span><strong>Alvos de Toque Adequados:</strong> Dimensão mínima de 44 × 44 pixels em dispositivos móveis para facilitar acionamentos precisos.</span>
            </li>
          </ul>

          <h2 className="text-lg font-bold text-gray-900 pt-2">Canal de Comunicação</h2>
          <p>
            Caso você encontre qualquer dificuldade de acesso ou deseje sugerir melhorias de acessibilidade neste portal,
            por favor utilize nossa central de ajuda em <Link href="/faq" className="text-[#1351B4] underline font-semibold">Ajuda e FAQ</Link>.
          </p>
        </div>
      </div>
    </div>
  );
}

