import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import RegisterPage from "../page";
import * as apiClient from "@/services/apiClient";

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

vi.mock("@/services/apiClient", async (importOriginal) => {
  const actual = await importOriginal<typeof apiClient>();
  return {
    ...actual,
    registerCitizen: vi.fn(),
  };
});

describe("Cadastro do Cidadão (RF-01, Autodeclaração de Gênero, Mensagem Verídica)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("deve renderizar campos obrigatórios e condicional de gênero 'Outro'", async () => {
    render(<RegisterPage />);

    expect(screen.getByRole("heading", { name: /criar conta no sosp/i })).toBeInTheDocument();

    const genderSelect = screen.getByLabelText(/sexo \/ gênero/i);
    expect(genderSelect).toBeInTheDocument();

    // Inicialmente o campo de descrição não deve existir
    expect(screen.queryByLabelText(/qual\? \(informe como você se identifica\)/i)).not.toBeInTheDocument();

    // Seleciona "Outro"
    fireEvent.change(genderSelect, { target: { value: "O" } });

    // Agora o campo deve aparecer
    const genderDescInput = screen.getByLabelText(/qual\? \(informe como você se identifica\)/i);
    expect(genderDescInput).toBeInTheDocument();
  });

  it("deve validar tamanho máximo de 120 caracteres para genderDescription", async () => {
    render(<RegisterPage />);

    const genderSelect = screen.getByLabelText(/sexo \/ gênero/i);
    fireEvent.change(genderSelect, { target: { value: "O" } });

    const genderDescInput = screen.getByLabelText(/qual\? \(informe como você se identifica\)/i);
    const longText = "A".repeat(121);
    fireEvent.change(genderDescInput, { target: { value: longText } });

    const submitBtn = screen.getByRole("button", { name: /cadastrar/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(
        screen.getByText(/a descrição de identidade de gênero não pode exceder 120 caracteres/i)
      ).toBeInTheDocument();
    });
  });

  it("deve submeter o cadastro com genderDescription e exibir mensagem de sucesso verídica sem falsa promessa de e-mail", async () => {
    const mockRegister = vi.mocked(apiClient.registerCitizen);
    mockRegister.mockResolvedValueOnce({ id: "citizen-new-001" });

    render(<RegisterPage />);

    // Preenche campos válidos
    fireEvent.change(screen.getByLabelText(/nome completo/i), { target: { value: "Cidadão Teste da Silva" } });
    fireEvent.change(screen.getByLabelText(/^cpf/i), { target: { value: "111.444.777-35" } });
    fireEvent.change(screen.getByLabelText(/data de nascimento/i), { target: { value: "1995-03-20" } });
    fireEvent.change(screen.getByLabelText(/sexo \/ gênero/i), { target: { value: "O" } });

    const genderDescInput = screen.getByLabelText(/qual\? \(informe como você se identifica\)/i);
    fireEvent.change(genderDescInput, { target: { value: "Não-binário" } });

    fireEvent.change(screen.getByLabelText(/nome da mãe/i), { target: { value: "Mãe do Cidadão Teste" } });
    fireEvent.change(screen.getByLabelText(/^e-mail/i), { target: { value: "cidadao.teste@exemplo.com" } });
    fireEvent.change(screen.getByLabelText(/confirme o e-mail/i), { target: { value: "cidadao.teste@exemplo.com" } });
    fireEvent.change(screen.getByLabelText(/telefone celular/i), { target: { value: "(82) 98877-6655" } });
    fireEvent.change(screen.getByLabelText(/cep/i), { target: { value: "57020-000" } });
    fireEvent.change(screen.getByLabelText(/logradouro/i), { target: { value: "Rua do Comércio" } });
    fireEvent.change(screen.getByLabelText(/número/i), { target: { value: "100" } });
    fireEvent.change(screen.getByLabelText(/bairro/i), { target: { value: "Centro" } });
    fireEvent.change(screen.getByLabelText(/município/i), { target: { value: "Maceió" } });
    fireEvent.change(screen.getByLabelText(/estado \(uf\)/i), { target: { value: "AL" } });

    fireEvent.change(screen.getByLabelText(/^senha de acesso/i), { target: { value: "SenhaForte@2026!" } });
    fireEvent.change(screen.getByLabelText(/confirme a senha/i), { target: { value: "SenhaForte@2026!" } });

    const termsCheckbox = screen.getByRole("checkbox");
    fireEvent.click(termsCheckbox);

    const submitBtn = screen.getByRole("button", { name: /cadastrar/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith(
        expect.objectContaining({
          fullName: "Cidadão Teste da Silva",
          cpf: "111.444.777-35",
          gender: "O",
          genderDescription: "Não-binário",
        })
      );
    });

    // Valida mensagem de sucesso verídica (sem menção a e-mail de confirmação enviado)
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /cadastro concluído com sucesso!/i })).toBeInTheDocument();
      expect(
        screen.getByText(/seu cadastro no sosp foi realizado com sucesso\. você já pode fazer login utilizando seu cpf e senha cadastrados/i)
      ).toBeInTheDocument();
      // Não deve conter a afirmação inverídica
      expect(
        screen.queryByText(/um e-mail de confirmação foi enviado/i)
      ).not.toBeInTheDocument();
    });
  });
});
