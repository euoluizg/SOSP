import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import AjudaPage from "../page";

describe("Central de Ajuda (Figma Parity, UC-14, D11)", () => {
  it("deve renderizar o cabeçalho da Central de Ajuda e o aviso acadêmico CESMAC", () => {
    render(<AjudaPage />);
    expect(
      screen.getByRole("heading", { name: /como podemos ajudar você hoje\?/i })
    ).toBeInTheDocument();
    expect(
      screen.getByText(/projeto acadêmico de graduação no centro universitário cesmac/i)
    ).toBeInTheDocument();
  });

  it("deve listar os 5 tópicos essenciais de ajuda ao cidadão", () => {
    render(<AjudaPage />);
    expect(screen.getByText("Como criar sua conta de cidadão")).toBeInTheDocument();
    expect(screen.getByText("Como pesquisar serviços e consultar exigências")).toBeInTheDocument();
    expect(screen.getByText("Como agendar seu atendimento presencial")).toBeInTheDocument();
    expect(screen.getByText("Regras de cancelamento e remarcação")).toBeInTheDocument();
    expect(screen.getByText("Acompanhar protocolos e andamento")).toBeInTheDocument();
  });

  it("deve filtrar tópicos conforme o termo digitado na busca", () => {
    render(<AjudaPage />);
    const searchInput = screen.getByLabelText(/buscar tópicos de ajuda/i);

    fireEvent.change(searchInput, { target: { value: "cancelamento" } });

    expect(screen.getByText("Regras de cancelamento e remarcação")).toBeInTheDocument();
    expect(screen.queryByText("Como criar sua conta de cidadão")).not.toBeInTheDocument();
  });

  it("deve abrir e fechar o passo a passo do tópico ao clicar no cabeçalho", () => {
    render(<AjudaPage />);
    const topicButton = screen.getByRole("button", {
      name: /como agendar seu atendimento presencial/i,
    });

    // Clica para expandir
    fireEvent.click(topicButton);
    expect(
      screen.getByText(/na ficha do serviço desejado, clique no botão 'agendar atendimento'\./i)
    ).toBeInTheDocument();

    // Clica novamente para recolher
    fireEvent.click(topicButton);
    expect(
      screen.queryByText(/na ficha do serviço desejado, clique no botão 'agendar atendimento'\./i)
    ).not.toBeInTheDocument();
  });
});
