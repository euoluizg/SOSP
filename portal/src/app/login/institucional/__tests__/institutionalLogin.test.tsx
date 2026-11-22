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
    changePassword: vi.fn(),
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
    expect(localStorage.getItem("sosp_auth_token")).toBeNull();
    expect(localStorage.getItem("sosp_user")).toBeNull();
  });

  it("deve rejeitar perfil desconhecido sem gravar token no localStorage nem redirecionar", async () => {
    const mockLogin = vi.mocked(apiClient.loginCitizen);
    mockLogin.mockResolvedValueOnce({
      token: "jwt-token-unknown",
      tokenType: "Bearer",
      expiresIn: 3600,
      citizen: {
        id: "user-unknown",
        fullName: "Usuário Desconhecido",
        cpf: "77788899941",
        email: "unknown@exemplo.com",
        role: "guest",
      },
    });

    render(<InstitutionalLoginPage />);

    const cpfInput = screen.getByLabelText(/cpf do servidor ou gestor/i);
    const passInput = screen.getByLabelText(/senha institucional/i);
    const submitBtn = screen.getByRole("button", { name: /acessar painel institucional/i });

    fireEvent.change(cpfInput, { target: { value: "777.888.999-41" } });
    fireEvent.change(passInput, { target: { value: "SenhaForte@123" } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(
        screen.getByText(/perfil de acesso institucional não reconhecido/i)
      ).toBeInTheDocument();
    });

    expect(mockPush).not.toHaveBeenCalled();
    expect(localStorage.getItem("sosp_auth_token")).toBeNull();
    expect(localStorage.getItem("sosp_user")).toBeNull();
  });

  it("deve redirecionar servidor público para /servidor/painel e gravar sessão autorizada", async () => {
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
    expect(localStorage.getItem("sosp_auth_token")).toBe("jwt-token-server");
  });

  it("deve redirecionar gestor institucional para /admin/orgaos e gravar sessão autorizada", async () => {
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
    expect(localStorage.getItem("sosp_auth_token")).toBe("jwt-token-manager");
  });

  it("deve interceptar primeiro acesso com mustChangePassword=true e exibir fluxo de definição de nova senha", async () => {
    const mockLogin = vi.mocked(apiClient.loginCitizen);
    mockLogin.mockResolvedValueOnce({
      token: "temp-jwt-token-server",
      tokenType: "Bearer",
      expiresIn: 1800,
      citizen: {
        id: "server-001",
        fullName: "João Servidor Central",
        cpf: "33366699957",
        email: "joao.servidor@ssp.al.gov.br",
        role: "server",
        mustChangePassword: true,
      },
    });

    render(<InstitutionalLoginPage />);

    const cpfInput = screen.getByLabelText(/cpf do servidor ou gestor/i);
    const passInput = screen.getByLabelText(/senha institucional/i);
    const submitBtn = screen.getByRole("button", { name: /acessar painel institucional/i });

    fireEvent.change(cpfInput, { target: { value: "333.666.999-57" } });
    fireEvent.change(passInput, { target: { value: "TempSecret@123" } });
    fireEvent.click(submitBtn);

    // Deve exibir tela de primeiro acesso sem redirecionar de imediato
    await waitFor(() => {
      expect(screen.getByText("Primeiro Acesso Obrigatório")).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: /definição de nova senha/i })).toBeInTheDocument();
    });
    expect(mockPush).not.toHaveBeenCalled();

    // Deve conter campos para senha provisória atual, nova senha e confirmação
    expect(screen.getByLabelText(/senha provisória atual/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/nova senha permanente/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirme a nova senha/i)).toBeInTheDocument();
  });

  it("deve executar a alteração de senha provisória e prosseguir com acesso autorizado", async () => {
    const mockLogin = vi.mocked(apiClient.loginCitizen);
    const mockChangePassword = vi.mocked(apiClient.changePassword);

    mockLogin.mockResolvedValueOnce({
      token: "temp-jwt-token-server",
      tokenType: "Bearer",
      expiresIn: 1800,
      citizen: {
        id: "server-001",
        fullName: "João Servidor Central",
        cpf: "33366699957",
        email: "joao.servidor@ssp.al.gov.br",
        role: "server",
        mustChangePassword: true,
      },
    });

    mockChangePassword.mockResolvedValueOnce({
      message: "Senha institucional atualizada com sucesso!",
      token: "perm-jwt-token-server",
      mustChangePassword: false,
    });

    render(<InstitutionalLoginPage />);

    fireEvent.change(screen.getByLabelText(/cpf do servidor ou gestor/i), { target: { value: "333.666.999-57" } });
    fireEvent.change(screen.getByLabelText(/senha institucional/i), { target: { value: "TempSecret@123" } });
    fireEvent.click(screen.getByRole("button", { name: /acessar painel institucional/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/nova senha permanente/i)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText(/nova senha permanente/i), { target: { value: "NovaSenhaForte@2026" } });
    fireEvent.change(screen.getByLabelText(/confirme a nova senha/i), { target: { value: "NovaSenhaForte@2026" } });
    fireEvent.click(screen.getByRole("button", { name: /salvar nova senha e acessar/i }));

    await waitFor(() => {
      expect(mockChangePassword).toHaveBeenCalledWith(
        "TempSecret@123",
        "NovaSenhaForte@2026",
        "NovaSenhaForte@2026"
      );
      expect(screen.getByText(/senha institucional atualizada com sucesso!/i)).toBeInTheDocument();
    });
  });

  it("deve fechar o pop-up e limpar sessão temporária do localStorage ao cancelar ou pressionar Escape", async () => {
    const mockLogin = vi.mocked(apiClient.loginCitizen);
    mockLogin.mockResolvedValueOnce({
      token: "temp-jwt-token-admin",
      tokenType: "Bearer",
      expiresIn: 1800,
      citizen: {
        id: "admin-001",
        fullName: "Admin SOSP Geral",
        cpf: "99988877714",
        email: "admin@sosp.al.gov.br",
        role: "superadmin",
        mustChangePassword: true,
      },
    });

    render(<InstitutionalLoginPage />);

    fireEvent.change(screen.getByLabelText(/cpf do servidor ou gestor/i), {
      target: { value: "999.888.777-14" },
    });
    fireEvent.change(screen.getByLabelText(/senha institucional/i), {
      target: { value: "AdminSosp@2026!" },
    });
    fireEvent.click(screen.getByRole("button", { name: /acessar painel institucional/i }));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    expect(localStorage.getItem("sosp_auth_token")).toBe("temp-jwt-token-admin");
    expect(localStorage.getItem("sosp_user")).toContain("Admin SOSP Geral");

    fireEvent.click(screen.getByRole("button", { name: /cancelar e voltar para o login/i }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    expect(localStorage.getItem("sosp_auth_token")).toBeNull();
    expect(localStorage.getItem("sosp_user")).toBeNull();
  });
});

