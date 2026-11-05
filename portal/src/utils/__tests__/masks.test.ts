import { describe, it, expect } from "vitest";
import { maskCPF, maskCEP, maskPhone, maskProtocol, cleanDigits } from "../masks";

describe("Input Masks (RF-01, RF-02, RN-20)", () => {
  it("deve aplicar máscara de CPF corretamente (XXX.XXX.XXX-XX)", () => {
    expect(maskCPF("12345678901")).toBe("123.456.789-01");
    expect(maskCPF("123")).toBe("123");
    expect(maskCPF("123456")).toBe("123.456");
    expect(maskCPF("123456789")).toBe("123.456.789");
  });

  it("deve aplicar máscara de CEP corretamente (XXXXX-XXX)", () => {
    expect(maskCEP("57000000")).toBe("57000-000");
    expect(maskCEP("57020")).toBe("57020");
    expect(maskCEP("57020100")).toBe("57020-100");
  });

  it("deve aplicar máscara de Telefone fixo e celular", () => {
    // Fixo (10 dígitos)
    expect(maskPhone("8233151000")).toBe("(82) 3315-1000");
    // Celular (11 dígitos com 9)
    expect(maskPhone("82999887766")).toBe("(82) 99988-7766");
  });

  it("deve formatar protocolo no padrão AAAAMMDD-XXXX (RN-20)", () => {
    expect(maskProtocol("202611051042")).toBe("20261105-1042");
    expect(maskProtocol("20261105")).toBe("20261105");
  });

  it("deve limpar caracteres não numéricos com cleanDigits", () => {
    expect(cleanDigits("123.456.789-01")).toBe("12345678901");
    expect(cleanDigits("(82) 99988-7766")).toBe("82999887766");
    expect(cleanDigits("57020-100")).toBe("57020100");
  });
});

