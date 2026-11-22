import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import SessionExpiredPage from "../page";
import { Header } from "@/components/layout/Header";

let mockPathname = "/sessao-expirada";
const mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
  usePathname: () => mockPathname,
  useSearchParams: () => ({
    get: (key: string) => mockSearchParams.get(key),
  }),
}));

describe("Sessão Expirada e Limpeza de Cabeçalho (RN-28)", () => {
  beforeEach(() => {
    localStorage.clear();
    mockPathname = "/sessao-expirada";
    Array.from(mockSearchParams.keys()).forEach((k) => mockSearchParams.delete(k));
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("deve limpar sessão residual de administrador e direcionar CTA para /login/institucional", async () => {
    localStorage.setItem("sosp_auth_token", "expired-admin-token");
    localStorage.setItem(
      "sosp_user",
      JSON.stringify({
        id: "admin-001",
        fullName: "Admin SOSP Geral",
        role: "superadmin",
      })
    );

    render(
      <>
        <Header />
        <SessionExpiredPage />
      </>
    );

    await waitFor(() => {
      expect(localStorage.getItem("sosp_auth_token")).toBeNull();
      expect(localStorage.getItem("sosp_user")).toBeNull();
    });

    expect(screen.getByRole("heading", { name: /sua sessão expirou/i })).toBeInTheDocument();
    expect(screen.queryByText(/olá, admin/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /painel gestor/i })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /entrar/i })).toHaveAttribute("href", "/login");

    const loginLink = screen.getByRole("link", { name: /fazer login novamente/i });
    expect(loginLink).toHaveAttribute("href", "/login/institucional");
  });

  it("deve respeitar query param tipo=institucional mesmo sem usuário no localStorage", async () => {
    mockSearchParams.set("tipo", "institucional");
    mockSearchParams.set("redirect", "/admin/orgaos");

    render(<SessionExpiredPage />);

    await waitFor(() => {
      const loginLink = screen.getByRole("link", { name: /fazer login novamente/i });
      expect(loginLink).toHaveAttribute(
        "href",
        "/login/institucional?redirect=%2Fadmin%2Forgaos"
      );
    });
  });

  it("deve ocultar sessão no Header quando não há token e direcionar cidadão comum para /login", async () => {
    mockPathname = "/";
    localStorage.setItem(
      "sosp_user",
      JSON.stringify({
        id: "admin-001",
        fullName: "Admin SOSP Geral",
        role: "superadmin",
      })
    );

    const { unmount } = render(<Header />);

    expect(screen.queryByText(/olá, admin/i)).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /entrar/i })).toBeInTheDocument();
    unmount();

    mockPathname = "/sessao-expirada";
    localStorage.setItem(
      "sosp_user",
      JSON.stringify({
        id: "citizen-001",
        fullName: "Cidadão Comum",
        role: "citizen",
      })
    );
    render(<SessionExpiredPage />);

    await waitFor(() => {
      expect(screen.getByRole("link", { name: /fazer login novamente/i })).toHaveAttribute(
        "href",
        "/login"
      );
      expect(localStorage.getItem("sosp_user")).toBeNull();
    });
  });

  it("não deve exibir Painel Gestor no Header enquanto troca de senha obrigatória estiver pendente", () => {
    mockPathname = "/login/institucional";
    localStorage.setItem("sosp_auth_token", "temp-token");
    localStorage.setItem(
      "sosp_user",
      JSON.stringify({
        id: "admin-001",
        fullName: "Admin SOSP Geral",
        role: "superadmin",
        mustChangePassword: true,
      })
    );

    render(<Header />);

    expect(screen.queryByText(/olá, admin/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /painel gestor/i })).not.toBeInTheDocument();
  });

  it("deve exibir Olá, Admin e Painel Gestor quando sessão definitiva estiver ativa", () => {
    mockPathname = "/admin/orgaos";
    localStorage.setItem("sosp_auth_token", "valid-perm-token");
    localStorage.setItem(
      "sosp_user",
      JSON.stringify({
        id: "admin-001",
        fullName: "Admin SOSP Geral",
        role: "superadmin",
        mustChangePassword: false,
      })
    );

    render(<Header />);

    expect(screen.getByText(/olá, admin/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /painel gestor/i })).toHaveAttribute(
      "href",
      "/admin/orgaos"
    );
  });
});
