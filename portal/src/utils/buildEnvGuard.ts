/**
 * SOSP — Build Environment Guard
 * Valida se as variáveis de ambiente obrigatórias de build do Portal estão corretas.
 *
 * Regras:
 * 1. NEXT_PUBLIC_API_URL deve estar presente e não vazia.
 * 2. NEXT_PUBLIC_API_URL deve conter obrigatoriamente '/api/v1'.
 * 3. NEXT_PUBLIC_API_URL não pode conter 'localhost' ou '127.0.0.1' em builds de staging/produção.
 */

export interface BuildEnvValidationResult {
  valid: boolean;
  errors: string[];
}

export function validateApiUrlForBuild(apiUrl: string | undefined): BuildEnvValidationResult {
  const errors: string[] = [];

  if (!apiUrl || apiUrl.trim() === "") {
    errors.push("NEXT_PUBLIC_API_URL está ausente ou vazia.");
    return { valid: false, errors };
  }

  const trimmed = apiUrl.trim();

  if (!trimmed.includes("/api/v1")) {
    errors.push(`NEXT_PUBLIC_API_URL ('${trimmed}') deve conter obrigatoriamente '/api/v1'.`);
  }

  const lower = trimmed.toLowerCase();
  if (lower.includes("localhost") || lower.includes("127.0.0.1")) {
    errors.push(`NEXT_PUBLIC_API_URL ('${trimmed}') não pode conter 'localhost' ou '127.0.0.1' em builds.`);
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

export function assertValidBuildEnv(apiUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL): void {
  const result = validateApiUrlForBuild(apiUrl);
  if (!result.valid) {
    const errorDetails = result.errors.map((e) => `  - ${e}`).join("\n");
    throw new Error(
      `\n❌ [SOSP BUILD GUARD] Falha de validação das variáveis de ambiente de build:\n${errorDetails}\n\nDefina NEXT_PUBLIC_API_URL com a URL pública da API REST (ex.: https://sosp-backend-staging.onrender.com/api/v1).\n`
    );
  }
}
