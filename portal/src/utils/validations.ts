/**
 * SOSP — Funções de Validação de Regras de Negócio
 * Atende RF-01, RF-02, RN-29, RN-30
 */

export function isValidCPF(cpf: string): boolean {
  const clean = cpf.replace(/\D/g, "");
  if (clean.length !== 11) return false;

  // Rejeita sequências conhecidas de dígitos iguais
  if (/^(\d)\1{10}$/.test(clean)) return false;

  // Validação do 1º dígito verificador
  let sum = 0;
  for (let i = 0; i < 9; i++) {
    sum += parseInt(clean.charAt(i), 10) * (10 - i);
  }
  let remainder = (sum * 10) % 11;
  if (remainder === 10 || remainder === 11) remainder = 0;
  if (remainder !== parseInt(clean.charAt(9), 10)) return false;

  // Validação do 2º dígito verificador
  sum = 0;
  for (let i = 0; i < 10; i++) {
    sum += parseInt(clean.charAt(i), 10) * (11 - i);
  }
  remainder = (sum * 10) % 11;
  if (remainder === 10 || remainder === 11) remainder = 0;
  if (remainder !== parseInt(clean.charAt(10), 10)) return false;

  return true;
}

export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}

export function isValidBirthDate(dateString: string): { valid: boolean; message?: string } {
  if (!dateString) return { valid: false, message: "Data de nascimento é obrigatória." };

  const birth = new Date(dateString);
  if (isNaN(birth.getTime())) {
    return { valid: false, message: "Data de nascimento inválida." };
  }

  const today = new Date();
  if (birth > today) {
    return { valid: false, message: "A data de nascimento não pode ser no futuro." };
  }

  // Idade mínima de 12 anos (RF-01)
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }

  if (age < 12) {
    return { valid: false, message: "O cidadão deve ter no mínimo 12 anos para criar uma conta." };
  }

  return { valid: true };
}

export function validatePasswordStrength(password: string): {
  isValid: boolean;
  score: number; // 0 a 4
  feedback: string[];
} {
  const feedback: string[] = [];
  let score = 0;

  if (password.length >= 8) score++;
  else feedback.push("Mínimo de 8 caracteres");

  if (/[A-Z]/.test(password)) score++;
  else feedback.push("Pelo menos uma letra maiúscula");

  if (/[a-z]/.test(password)) score++;
  else feedback.push("Pelo menos uma letra minúscula");

  if (/\d/.test(password)) score++;
  else feedback.push("Pelo menos um número");

  if (/[^A-Za-z0-9]/.test(password)) score++;
  else feedback.push("Pelo menos um caractere especial (!@#$%^&*)");

  return {
    isValid: score >= 4,
    score: Math.min(score, 4),
    feedback,
  };
}

/**
 * Valida e sanitiza uma URL de redirecionamento contra ataques de Open Redirect (CWE-601).
 * Aceita estritamente caminhos relativos locais iniciados com '/', rejeitando URLs absolutas,
 * protocol-relative ('//'), sequências de escape ('/\', '\') e esquemas executáveis.
 */
export function sanitizeRedirectUrl(url: string | null | undefined): string | null {
  if (!url || typeof url !== "string") return null;

  const trimmed = url.trim();
  if (!trimmed) return null;

  // Rejeita caracteres de controle que podem burlar parsers
  if (/[\x00-\x1F\x7F]/.test(trimmed)) return null;

  // Rejeita caminhos que não comecem com '/' ou comecem com '//', '/\', '\\'
  if (!trimmed.startsWith("/") || trimmed.startsWith("//") || trimmed.startsWith("/\\") || trimmed.startsWith("\\")) {
    return null;
  }

  // Rejeita esquemas embutidos (ex.: /javascript:..., /http:...)
  if (/^\/[^?#]*[a-zA-Z][a-zA-Z0-9+.-]*:/.test(trimmed)) {
    return null;
  }

  try {
    const parsed = new URL(trimmed, "http://localhost");
    if (parsed.origin !== "http://localhost") {
      return null;
    }
    return `${parsed.pathname}${parsed.search}${parsed.hash}`;
  } catch {
    return null;
  }
}


