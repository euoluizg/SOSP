import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "../Button";
import { Tag } from "../Tag";
import { Modal } from "../Modal";
import { GovbrModal } from "@/components/features/auth/GovbrModal";

describe("UI Core Components (Design System & WCAG 2.1 AA)", () => {
  describe("Button Component", () => {
    it("deve renderizar o botão com o texto correto e responder ao clique", () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Confirmar Agendamento</Button>);

      const btn = screen.getByRole("button", { name: /confirmar agendamento/i });
      expect(btn).toBeInTheDocument();
      fireEvent.click(btn);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it("deve exibir estado de carregamento e desabilitar o botão", () => {
      render(<Button isLoading>Processando</Button>);
      const btn = screen.getByRole("button");
      expect(btn).toBeDisabled();
      expect(btn).toHaveAttribute("aria-busy", "true");
    });

    it("deve aplicar classes correspondentes à variante 'danger'", () => {
      render(<Button variant="danger">Excluir Conta</Button>);
      const btn = screen.getByRole("button", { name: /excluir conta/i });
      expect(btn.className).toContain("bg-[#E52207]");
    });
  });

  describe("Tag Component", () => {
    it("deve renderizar a tag com texto e variante apropriada", () => {
      render(<Tag variant="success">Disponível</Tag>);
      expect(screen.getByText("Disponível")).toBeInTheDocument();
    });

    it("deve aplicar estilo para canal 'online'", () => {
      const { container } = render(<Tag channel="online">100% Digital</Tag>);
      expect(container.firstChild).toHaveClass("bg-[#EFF5FF]");
    });
  });

  describe("Modal Component (Acessibilidade & Fechamento)", () => {
    it("não deve renderizar quando isOpen for falso", () => {
      render(
        <Modal isOpen={false} onClose={vi.fn()} title="Título Teste">
          <p>Conteúdo do Modal</p>
        </Modal>
      );
      expect(screen.queryByText("Conteúdo do Modal")).not.toBeInTheDocument();
    });

    it("deve renderizar quando isOpen for verdadeiro", () => {
      render(
        <Modal isOpen={true} onClose={vi.fn()} title="Título Teste">
          <p>Conteúdo do Modal</p>
        </Modal>
      );
      expect(screen.getByText("Conteúdo do Modal")).toBeInTheDocument();
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    it("deve acionar onClose ao pressionar a tecla Escape", () => {
      const handleClose = vi.fn();
      render(
        <Modal isOpen={true} onClose={handleClose} title="Título Teste">
          <p>Modal com Escape</p>
        </Modal>
      );
      fireEvent.keyDown(window, { key: "Escape" });
      expect(handleClose).toHaveBeenCalledTimes(1);
    });
  });

  describe("GovbrModal Component (Mensagem Literal D10 / RF-02)", () => {
    it("deve exibir a mensagem mandatória de integração com Gov.br na v2.0", () => {
      render(<GovbrModal isOpen={true} onClose={vi.fn()} />);

      const mandatoryMessage =
        "A integração com o Gov.br estará disponível em uma futura atualização (v2.0). Utilize seu CPF e senha para entrar.";
      expect(screen.getByText(mandatoryMessage)).toBeInTheDocument();

      const confirmButton = screen.getByRole("button", {
        name: /entendi, quero usar cpf e senha/i,
      });
      expect(confirmButton).toBeInTheDocument();
    });
  });
});

