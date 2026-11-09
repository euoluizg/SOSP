import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import MeusAgendamentosPage from "../page";
import * as apiClient from "@/services/apiClient";

vi.mock("@/services/apiClient", async (importOriginal) => {
  const actual = await importOriginal<typeof apiClient>();
  return {
    ...actual,
    getCitizenAppointments: vi.fn(),
  };
});

describe("Meus Agendamentos (Figma Parity, Zero Fakes, RN-21, RN-22)", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("deve exibir estado orientativo para visitante não autenticado com CTA para login", async () => {
    render(<MeusAgendamentosPage />);

    expect(
      screen.getByRole("heading", { name: /seus agendamentos em um só lugar/i })
    ).toBeInTheDocument();
    expect(
      screen.getByText(/entre na sua conta ou cadastre-se para visualizar, acompanhar e gerenciar seus agendamentos/i)
    ).toBeInTheDocument();

    const loginLink = screen.getByRole("link", { name: /entrar na minha conta/i });
    expect(loginLink).toHaveAttribute(
      "href",
      "/login?redirect=/cidadao/meus-agendamentos"
    );
  });

  it("deve exibir estado vazio verídico (zero fakes) para cidadão autenticado sem agendamentos", async () => {
    localStorage.setItem("sosp_auth_token", "jwt-token-test");
    localStorage.setItem(
      "sosp_user",
      JSON.stringify({ id: "citizen-001", fullName: "Maria dos Santos" })
    );

    const mockGetAppointments = vi.mocked(apiClient.getCitizenAppointments);
    mockGetAppointments.mockResolvedValueOnce([]);

    render(<MeusAgendamentosPage />);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /você ainda não possui agendamentos/i })
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText(/encontre um serviço público e escolha um horário para realizar seu primeiro agendamento/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /explorar serviços/i })
    ).toHaveAttribute("href", "/servicos");
  });

  it("deve listar agendamentos reais divididos entre ativos e histórico", async () => {
    localStorage.setItem("sosp_auth_token", "jwt-token-test");
    localStorage.setItem(
      "sosp_user",
      JSON.stringify({ id: "citizen-001", fullName: "Maria dos Santos" })
    );

    const mockGetAppointments = vi.mocked(apiClient.getCitizenAppointments);
    mockGetAppointments.mockResolvedValueOnce([
      {
        id: "appt-active-1",
        serviceId: "servico-emitir-rg",
        serviceName: "Emissão de Carteira de Identidade (CIN)",
        agencyName: "Secretaria de Segurança Pública",
        unitId: "unidade-centro",
        unitName: "Central Já! Centro",
        unitAddress: "Rua do Comércio, 123",
        scheduledDate: "2026-11-20",
        scheduledTime: "09:30",
        protocolNumber: "20261120-1234",
        status: "scheduled",
        citizenId: "citizen-001",
        citizenName: "Maria dos Santos",
        citizenCpfMasked: "***.444.777-**",
        createdAt: "2026-11-09T10:00:00Z",
      },
      {
        id: "appt-history-1",
        serviceId: "servico-cnh-renovacao",
        serviceName: "Renovação da CNH",
        agencyName: "Departamento Estadual de Trânsito",
        unitId: "unidade-shopping",
        unitName: "Central Já! Mangabeiras",
        unitAddress: "Av. Gustavo Paiva, 2990",
        scheduledDate: "2026-10-10",
        scheduledTime: "14:00",
        protocolNumber: "20261010-5678",
        status: "completed",
        citizenId: "citizen-001",
        citizenName: "Maria dos Santos",
        citizenCpfMasked: "***.444.777-**",
        createdAt: "2026-10-01T10:00:00Z",
      },
    ]);

    render(<MeusAgendamentosPage />);

    await waitFor(() => {
      expect(screen.getByText("Emissão de Carteira de Identidade (CIN)")).toBeInTheDocument();
      expect(screen.getByText(/20261120-1234/)).toBeInTheDocument();
      expect(screen.getByText("Renovação da CNH")).toBeInTheDocument();
      expect(screen.getByText(/20261010-5678/)).toBeInTheDocument();
    });
  });
});
