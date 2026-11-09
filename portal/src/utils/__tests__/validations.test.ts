import { describe, it, expect } from "vitest";
import {
  isValidCPF,
  isValidEmail,
  isValidBirthDate,
  validatePasswordStrength,
  sanitizeRedirectUrl,
} from "../validations";

describe("Validations (RF-01, RF-02, RN-29, RN-30)", () => {
  describe("isValidCPF", () => {
    it("deve validar CPFs válidos conhecidos", () => {
      // CPFs matematicamente válidos para testes
      expect(isValidCPF("52998224725")).toBe(true);
      expect(isValidCPF("529.982.247-25")).toBe(true);
      expect(isValidCPF("00000000191")).toBe(true);
    });

    it("deve rejeitar sequências conhecidas de dígitos repetidos", () => {
      expect(isValidCPF("111.111.111-11")).toBe(false);
      expect(isValidCPF("00000000000")).toBe(false);
      expect(isValidCPF("99999999999")).toBe(false);
    });

    it("deve rejeitar CPFs com tamanho inválido ou caracteres alfabéticos", () => {
      expect(isValidCPF("123456789")).toBe(false);
      expect(isValidCPF("123456789012")).toBe(false);
      expect(isValidCPF("abc.def.ghi-jk")).toBe(false);
    });

    it("deve rejeitar CPFs com dígitos verificadores incorretos", () => {
      expect(isValidCPF("52998224720")).toBe(false); // Último dígito errado
      expect(isValidCPF("52998224715")).toBe(false); // Penúltimo dígito errado
    });
  });

  describe("isValidEmail", () => {
    it("deve validar e-mails com formato correto", () => {
      expect(isValidEmail("cidadao@exemplo.com.br")).toBe(true);
      expect(isValidEmail("usuario.teste@al.gov.br")).toBe(true);
    });

    it("deve rejeitar e-mails inválidos", () => {
      expect(isValidEmail("sem-arroba.com")).toBe(false);
      expect(isValidEmail("@sem-usuario.com")).toBe(false);
      expect(isValidEmail("sem-dominio@")).toBe(false);
      expect(isValidEmail("")).toBe(false);
    });
  });

  describe("isValidBirthDate (RF-01: Idade mínima de 12 anos)", () => {
    it("deve rejeitar data no futuro", () => {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      const res = isValidBirthDate(tomorrow.toISOString().slice(0, 10));
      expect(res.valid).toBe(false);
      expect(res.message).toBe("A data de nascimento não pode ser no futuro.");
    });

    it("deve rejeitar cidadão com menos de 12 anos", () => {
      const tenYearsAgo = new Date();
      tenYearsAgo.setFullYear(tenYearsAgo.getFullYear() - 10);
      const res = isValidBirthDate(tenYearsAgo.toISOString().slice(0, 10));
      expect(res.valid).toBe(false);
      expect(res.message).toBe("O cidadão deve ter no mínimo 12 anos para criar uma conta.");
    });

    it("deve aceitar cidadão com exatamente ou mais de 12 anos", () => {
      const twentyYearsAgo = new Date();
      twentyYearsAgo.setFullYear(twentyYearsAgo.getFullYear() - 20);
      const res = isValidBirthDate(twentyYearsAgo.toISOString().slice(0, 10));
      expect(res.valid).toBe(true);
    });

    it("deve rejeitar data vazia ou inválida", () => {
      expect(isValidBirthDate("").valid).toBe(false);
      expect(isValidBirthDate("data-invalida").valid).toBe(false);
    });
  });

  describe("validatePasswordStrength (Política de Senhas Fortes)", () => {
    it("deve aprovar senha com todos os requisitos (maiúscula, minúscula, número, especial, >=8)", () => {
      const res = validatePasswordStrength("S0sp@2026!Fort3");
      expect(res.isValid).toBe(true);
      expect(res.score).toBe(4);
      expect(res.feedback).toHaveLength(0);
    });

    it("deve reprovar senhas fracas ou curtas e retornar feedback detalhado", () => {
      const res = validatePasswordStrength("12345");
      expect(res.isValid).toBe(false);
      expect(res.score).toBeLessThan(4);
      expect(res.feedback).toContain("Mínimo de 8 caracteres");
      expect(res.feedback).toContain("Pelo menos uma letra maiúscula");
      expect(res.feedback).toContain("Pelo menos uma letra minúscula");
    });
  });

  describe("sanitizeRedirectUrl (Proteção contra Open Redirect — CWE-601)", () => {
    it("deve aceitar caminhos relativos legítimos", () => {
      expect(sanitizeRedirectUrl("/faq")).toBe("/faq");
      expect(sanitizeRedirectUrl("/cidadao/meus-agendamentos")).toBe("/cidadao/meus-agendamentos");
      expect(sanitizeRedirectUrl("/faq?categoria=docs")).toBe("/faq?categoria=docs");
      expect(sanitizeRedirectUrl("/faq?q=termo#ajuda")).toBe("/faq?q=termo#ajuda");
    });

    it("deve rejeitar URLs absolutas externas com protocolo http ou https", () => {
      expect(sanitizeRedirectUrl("https://evil.com")).toBeNull();
      expect(sanitizeRedirectUrl("http://evil.com/faq")).toBeNull();
      expect(sanitizeRedirectUrl("https://portal.sosp.workers.dev.attacker.com")).toBeNull();
    });

    it("deve rejeitar URLs protocol-relative ('//')", () => {
      expect(sanitizeRedirectUrl("//evil.com")).toBeNull();
      expect(sanitizeRedirectUrl("//evil.com/faq")).toBeNull();
      expect(sanitizeRedirectUrl("///evil.com")).toBeNull();
    });

    it("deve rejeitar caracteres de escape e barras invertidas ('/\\', '\\')", () => {
      expect(sanitizeRedirectUrl("/\\evil.com")).toBeNull();
      expect(sanitizeRedirectUrl("\\evil.com")).toBeNull();
      expect(sanitizeRedirectUrl("/\\\\evil.com")).toBeNull();
    });

    it("deve rejeitar esquemas executáveis perigosos (javascript:, data:, vbscript:)", () => {
      expect(sanitizeRedirectUrl("javascript:alert(1)")).toBeNull();
      expect(sanitizeRedirectUrl("/javascript:alert(1)")).toBeNull();
      expect(sanitizeRedirectUrl("data:text/html,<script>alert(1)</script>")).toBeNull();
      expect(sanitizeRedirectUrl("/data:text/html")).toBeNull();
    });

    it("deve retornar null para valores vazios, nulos ou indefinidos", () => {
      expect(sanitizeRedirectUrl(null)).toBeNull();
      expect(sanitizeRedirectUrl(undefined)).toBeNull();
      expect(sanitizeRedirectUrl("")).toBeNull();
      expect(sanitizeRedirectUrl("   ")).toBeNull();
      expect(sanitizeRedirectUrl("/\x00evil")).toBeNull();
    });
  });
});

