import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import InstitutionalLoginPage from "../page";
import * as apiClient from "@/services/apiClient";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  useSearchParams: () => ({
    get: vi.fn().mockReturnValue(null),
  }),
}));

vi.mock("@/services/apiClient", async (importOriginal) => {
  const actual = await importOriginal<typeof apiClient>();
  return {
    ...actual,
    loginCitizen: vi.fn(),
  };
});

describe("Login Institucional (ADR-003, RN-35, RN-36)", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("deve renderizar o cabeçalho de acesso restrito institucional", () => {
    render(<InstitutionalLoginPage />);

    expect(screen.getByText("Portal Institucional")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /acesso restrito/i })
    ).toBeInTheDocument();
    expect(
      screen.getByText(/para servidores públicos, gestores e administradores do sosp/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /acessar painel institucional/i })
    ).toBeInTheDocument();
  });

  it("deve rejeitar tentativa de login de cidadão comum com mensagem explicativa", async () => {
    const mockLogin = vi.mocked(apiClient.loginCitizen);
    mockLogin.mockResolvedValueOnce({
      token: "jwt-token-citizen",
      tokenType: "Bearer",
      expiresIn: 3600,
      citizen: {
        id: "citizen-001",
        fullName: "Cidadão Comum",
        cpf: "11144477735",
        email: "cidadao@exemplo.com",
        role: "citizen",
      },
    });

    render(<InstitutionalLoginPage />);

    const cpfInput = screen.getByLabelText(/cpf do servidor ou gestor/i);
    const passInput = screen.getByLabelText(/senha institucional/i);
    const submitBtn = screen.getByRole("button", { name: /acessar painel institucional/i });

    fireEvent.change(cpfInput, { target: { value: "111.444.777-35" } });
    fireEvent.change(passInput, { target: { value: "SenhaForte@123" } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(
        screen.getByText(/esta conta possui perfil de cidadão\. por favor, acesse o portal do cidadão\./i)
      ).toBeInTheDocument();
    });

    expect(mockPush).not.toHaveBeenCalled();
  });

  it("deve redirecionar servidor público para /servidor/painel", async () => {
    const mockLogin = vi.mocked(apiClient.loginCitizen);
    mockLogin.mockResolvedValueOnce({
      token: "jwt-token-server",
      tokenType: "Bearer",
      expiresIn: 3600,
      citizen: {
        id: "servant-001",
        fullName: "Servidor Já! Centro",
        cpf: "33366699957",
        email: "servidor@sosp.al.gov.br",
        role: "server",
      },
    });

    render(<InstitutionalLoginPage />);

    const cpfInput = screen.getByLabelText(/cpf do servidor ou gestor/i);
    const passInput = screen.getByLabelText(/senha institucional/i);
    const submitBtn = screen.getByRole("button", { name: /acessar painel institucional/i });

    fireEvent.change(cpfInput, { target: { value: "333.666.999-57" } });
    fireEvent.change(passInput, { target: { value: "Servidor@123" } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/servidor/painel");
    });
  });

  it("deve redirecionar gestor institucional para /admin/orgaos", async () => {
    const mockLogin = vi.mocked(apiClient.loginCitizen);
    mockLogin.mockResolvedValueOnce({
      token: "jwt-token-manager",
      tokenType: "Bearer",
      expiresIn: 3600,
      citizen: {
        id: "manager-001",
        fullName: "Gestor SEFAZ",
        cpf: "55588811194",
        email: "gestor.sefaz@sosp.al.gov.br",
        role: "gestor",
      },
    });

    render(<InstitutionalLoginPage />);

    const cpfInput = screen.getByLabelText(/cpf do servidor ou gestor/i);
    const passInput = screen.getByLabelText(/senha institucional/i);
    const submitBtn = screen.getByRole("button", { name: /acessar painel institucional/i });

    fireEvent.change(cpfInput, { target: { value: "555.888.111-94" } });
    fireEvent.change(passInput, { target: { value: "Gestor@123" } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/admin/orgaos");
    });
  });
});
