"use client";

import React from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";

export interface GovbrModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const GovbrModal: React.FC<GovbrModalProps> = ({ isOpen, onClose }) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Acesso Gov.br (Atualização Futura)"
      footer={
        <Button variant="primary" onClick={onClose} className="w-full sm:w-auto">
          Entendi, quero usar CPF e senha
        </Button>
      }
    >
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3 p-3 bg-[#EFF5FF] rounded-lg border border-[#1351B4]/20">
          <div className="w-10 h-10 rounded-full bg-[#1351B4] text-white flex items-center justify-center font-bold text-xs shrink-0">
            gov.br
          </div>
          <div>
            <span className="font-bold text-[#101828] text-sm block">Identidade Digital Gov.br</span>
            <span className="text-xs text-[#4A5568]">Planejada para a versão 2.0</span>
          </div>
        </div>

        {/* Mensagem Literal Mandatória — D10 / RF-02 / MSG-13 */}
        <p className="text-[#101828] font-medium text-sm leading-relaxed">
          A integração com o Gov.br estará disponível em uma futura atualização (v2.0). Utilize seu CPF e senha para entrar.
        </p>

        <p className="text-xs text-[#667085] leading-relaxed">
          No MVP atual, todos os cidadãos, servidores e administradores autenticam-se com segurança por meio de seu cadastro local no SOSP.
        </p>
      </div>
    </Modal>
  );
};

