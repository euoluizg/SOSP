import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import AdminLayout from "../layout";
import { AUTH_USER_KEY, AUTH_TOKEN_KEY } from "@/utils/session";

const mockReplace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: mockReplace,
    push: vi.fn(),
  }),
}));

describe("Proteção de Rotas Administrativas (AdminLayout)", () => {
  beforeEach(() => {
    localStorage.clear();
    mockReplace.mockClear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("deve bloquear servidor operacional e redirecionar imediatamente para /servidor/painel", () => {
    localStorage.setItem(AUTH_TOKEN_KEY, "server-token");
    localStorage.setItem(
      AUTH_USER_KEY,
      JSON.stringify({
        id: "server-001",
        fullName: "João Servidor Central",
        role: "server",
      })
    );

    render(
      <AdminLayout>
        <div data-testid="admin-content">Conteúdo Restrito</div>
      </AdminLayout>
    );

    expect(mockReplace).toHaveBeenCalledWith("/servidor/painel");
    expect(screen.queryByTestId("admin-content")).not.toBeInTheDocument();
  });

  it("deve permitir acesso para gestores e administradores (MANAGER_ROLES)", () => {
    localStorage.setItem(AUTH_TOKEN_KEY, "admin-token");
    localStorage.setItem(
      AUTH_USER_KEY,
      JSON.stringify({
        id: "admin-001",
        fullName: "Mozart Administrador",
        role: "admin",
      })
    );

    render(
      <AdminLayout>
        <div data-testid="admin-content">Conteúdo de Gestão Geral</div>
      </AdminLayout>
    );

    expect(screen.getByTestId("admin-content")).toBeInTheDocument();
    expect(mockReplace).not.toHaveBeenCalled();
  });
});

