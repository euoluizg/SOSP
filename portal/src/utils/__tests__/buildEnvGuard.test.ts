import { describe, it, expect } from "vitest";
import { validateApiUrlForBuild, assertValidBuildEnv } from "../buildEnvGuard";

describe("Build Environment Guard (validateApiUrlForBuild)", () => {
  it("deve aceitar uma URL de API de staging válida com /api/v1", () => {
    const result = validateApiUrlForBuild("https://sosp-backend-staging.onrender.com/api/v1");
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it("deve aceitar uma URL de produção válida com /api/v1", () => {
    const result = validateApiUrlForBuild("https://api.sosp.gov.br/api/v1");
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it("deve rejeitar quando NEXT_PUBLIC_API_URL estiver ausente (undefined)", () => {
    const result = validateApiUrlForBuild(undefined);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("NEXT_PUBLIC_API_URL está ausente ou vazia.");
  });

  it("deve rejeitar quando NEXT_PUBLIC_API_URL for string vazia", () => {
    const result = validateApiUrlForBuild("   ");
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("NEXT_PUBLIC_API_URL está ausente ou vazia.");
  });

  it("deve rejeitar quando a URL não contiver /api/v1", () => {
    const result = validateApiUrlForBuild("https://sosp-backend-staging.onrender.com");
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes("deve conter obrigatoriamente '/api/v1'"))).toBe(true);
  });

  it("deve rejeitar quando a URL contiver localhost", () => {
    const result = validateApiUrlForBuild("http://localhost:8000/api/v1");
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes("não pode conter 'localhost'"))).toBe(true);
  });

  it("deve rejeitar quando a URL contiver 127.0.0.1", () => {
    const result = validateApiUrlForBuild("http://127.0.0.1:8000/api/v1");
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes("não pode conter 'localhost' ou '127.0.0.1'"))).toBe(true);
  });

  it("assertValidBuildEnv deve lançar erro explicativo para URL inválida", () => {
    expect(() => assertValidBuildEnv("http://localhost:8000")).toThrow(
      /\[SOSP BUILD GUARD\] Falha de validação/
    );
  });

  it("assertValidBuildEnv não deve lançar erro para URL válida", () => {
    expect(() => assertValidBuildEnv("https://sosp-backend-staging.onrender.com/api/v1")).not.toThrow();
  });
});
