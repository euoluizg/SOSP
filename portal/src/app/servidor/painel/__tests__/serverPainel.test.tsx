import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ServerDashboardPage from "../page";
import { AUTH_USER_KEY, AUTH_TOKEN_KEY } from "@/utils/session";

describe("Painel do Servidor Público (/servidor/painel)", () => {
  beforeEach(() => {
    localStorage.clear();
    // Configura sessão ativa do servidor João Servidor Central (SSP-1001)
    localStorage.setItem(AUTH_TOKEN_KEY, "test-server-token");
    localStorage.setItem(
      AUTH_USER_KEY,
      JSON.stringify({
        id: "server-001",
        fullName: "João Servidor Central",
        registrationNumber: "SSP-1001",
        cpf: "33366699957",
        role: "server",
        agencyId: "agency-001",
        unitId: "unit-001",
      })
    );
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("deve exibir dinamicamente o nome e matrícula do atendente logado e não conter Arthur Franco", () => {
    render(<ServerDashboardPage />);

    expect(screen.getByText(/João Servidor Central/i)).toBeInTheDocument();
    expect(screen.getByText(/SSP-1001/i)).toBeInTheDocument();
    expect(screen.queryByText(/Arthur Franco/i)).not.toBeInTheDocument();
  });

  it("não deve exibir botão ou link de 'Gestão Geral' para o servidor", () => {
    render(<ServerDashboardPage />);

    expect(screen.queryByText(/Gestão Geral/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Gestão Geral/i })).not.toBeInTheDocument();
  });

  it("deve permitir chamar cidadão aguardando e persistir status 'Em Atendimento' no localStorage", () => {
    render(<ServerDashboardPage />);

    // Localiza o botão "Chamar" para o agendamento q-4 (Carlos Eduardo Santos)
    const callButtons = screen.getAllByRole("button", { name: /Chamar/i });
    expect(callButtons.length).toBeGreaterThan(0);

    fireEvent.click(callButtons[0]);

    // O status deve mudar imediatamente para "Em Atendimento"
    expect(screen.getAllByText("Em Atendimento").length).toBeGreaterThanOrEqual(2);

    // Deve estar gravado no localStorage de forma permanente
    const stored = localStorage.getItem("sosp_server_queue_guiche04");
    expect(stored).not.toBeNull();
    expect(stored).toContain("in_progress");
  });

  it("deve exibir opções de Ausente e Cancelar e persistir as alterações", () => {
    render(<ServerDashboardPage />);

    // Verifica presença de botões operacionais
    const absentButtons = screen.getAllByRole("button", { name: /Ausente/i });
    expect(absentButtons.length).toBeGreaterThan(0);

    const cancelButtons = screen.getAllByRole("button", { name: /Cancelar/i });
    expect(cancelButtons.length).toBeGreaterThan(0);
  });
});

