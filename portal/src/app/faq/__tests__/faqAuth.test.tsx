import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import FaqPage from "../page";
import * as apiClient from "@/services/apiClient";

// Mock do módulo de API
vi.mock("@/services/apiClient", async (importOriginal) => {
  const actual = await importOriginal<typeof apiClient>();
  return {
    ...actual,
    openQuestion: vi.fn(),
  };
});

describe("FAQ Autenticado & Auth Guard (RF-11, UC-14, RN-28)", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe("Cenário 1: Visitante Anônimo (Não Autenticado)", () => {
    it("deve exibir a lista de perguntas e respostas pública normalmente", () => {
      render(<FaqPage />);
      expect(screen.getByText("Perguntas Frequentes & Ajuda")).toBeInTheDocument();
      expect(
        screen.getByText("Quais documentos preciso levar no dia do atendimento?")
      ).toBeInTheDocument();
    });

    it("deve exibir o banner informativo de identificação necessária e ocultar o formulário", () => {
      render(<FaqPage />);

      const authGuard = screen.getByTestId("faq-auth-guard");
      expect(authGuard).toBeInTheDocument();
      expect(
        screen.getByText(
          "Para enviar uma dúvida diretamente à nossa equipe de atendimento do SOSP, é necessário estar identificado no portal."
        )
      ).toBeInTheDocument();

      // Formulário de envio não deve estar presente
      expect(screen.queryByTestId("faq-authenticated-form")).not.toBeInTheDocument();
    });

    it("deve conter link com redirecionamento seguro para /login?redirect=/faq e para cadastro", () => {
      render(<FaqPage />);

      const loginCta = screen.getByTestId("faq-login-cta");
      expect(loginCta).toHaveAttribute("href", "/login?redirect=/faq");

      const registerLink = screen.getByRole("link", { name: /cadastre-se gratuitamente/i });
      expect(registerLink).toHaveAttribute("href", "/cadastro?redirect=/faq");
    });
  });

  describe("Cenário 2: Cidadão Autenticado", () => {
    beforeEach(() => {
      localStorage.setItem("sosp_auth_token", "jwt-valid-token-example");
      localStorage.setItem(
        "sosp_user",
        JSON.stringify({
          fullName: "Maria dos Santos",
          email: "maria.santos@email.com",
        })
      );
    });

    it("deve exibir o formulário de envio pré-preenchido com dados do cidadão", () => {
      render(<FaqPage />);

      expect(screen.getByTestId("faq-authenticated-form")).toBeInTheDocument();
      expect(screen.queryByTestId("faq-auth-guard")).not.toBeInTheDocument();
      expect(screen.getByText(/Maria dos Santos/i)).toBeInTheDocument();

      const emailInput = screen.getByLabelText(/seu e-mail para resposta/i) as HTMLInputElement;
      expect(emailInput.value).toBe("maria.santos@email.com");
    });

    it("deve submeter a dúvida e exibir confirmação com protocolo gerado", async () => {
      const mockOpenQuestion = vi.mocked(apiClient.openQuestion);
      mockOpenQuestion.mockResolvedValueOnce({
        id: "qst-12345",
        protocolNumber: "20261109-1001",
        status: "open",
      });

      render(<FaqPage />);

      const subjectInput = screen.getByLabelText(/assunto da dúvida/i);
      const questionInput = screen.getByLabelText(/descreva sua dúvida ou solicitação/i);
      const submitBtn = screen.getByRole("button", { name: /enviar pergunta/i });

      fireEvent.change(subjectInput, { target: { value: "Agendamento RG Centro" } });
      fireEvent.change(questionInput, {
        target: { value: "Gostaria de saber se a 1ª via do RG precisa de foto 3x4 impressa." },
      });

      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(mockOpenQuestion).toHaveBeenCalledTimes(1);
        expect(mockOpenQuestion).toHaveBeenCalledWith(
          expect.objectContaining({
            citizenName: "Maria dos Santos",
            email: "maria.santos@email.com",
            subject: "Agendamento RG Centro",
            description: "Gostaria de saber se a 1ª via do RG precisa de foto 3x4 impressa.",
          })
        );
      });

      await waitFor(() => {
        const successBanner = screen.getByTestId("faq-success-banner");
        expect(successBanner).toBeInTheDocument();
        expect(screen.getByText("20261109-1001")).toBeInTheDocument();
      });
    });
  });

  describe("Cenário 3: Sessão Expirada / Erro 401 do Backend (RN-28)", () => {
    beforeEach(() => {
      localStorage.setItem("sosp_auth_token", "jwt-expired-token");
      localStorage.setItem(
        "sosp_user",
        JSON.stringify({ fullName: "José Pereira", email: "jose@email.com" })
      );
    });

    it("deve limpar o token local e exibir alerta de sessão expirada com CTA para login", async () => {
      const mockOpenQuestion = vi.mocked(apiClient.openQuestion);
      mockOpenQuestion.mockRejectedValueOnce({
        type: "about:blank",
        title: "Unauthorized",
        status: 401,
        detail: "Token de autenticação expirado ou inválido.",
      });

      render(<FaqPage />);

      const questionInput = screen.getByLabelText(/descreva sua dúvida ou solicitação/i);
      const submitBtn = screen.getByRole("button", { name: /enviar pergunta/i });

      fireEvent.change(questionInput, {
        target: { value: "Minha dúvida foi enviada com token expirado." },
      });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(mockOpenQuestion).toHaveBeenCalledTimes(1);
      });

      await waitFor(() => {
        // Token e usuário devem ter sido limpos
        expect(localStorage.getItem("sosp_auth_token")).toBeNull();
        expect(localStorage.getItem("sosp_user")).toBeNull();

        // O formulário desaparece e o alerta de sessão expirada é exibido no auth guard
        expect(screen.getByTestId("faq-auth-guard")).toBeInTheDocument();
        expect(screen.getByText(/sessão expirou por inatividade/i)).toBeInTheDocument();
        expect(screen.getByTestId("faq-login-cta")).toHaveAttribute(
          "href",
          "/login?redirect=/faq"
        );
      });
    });
  });
});

