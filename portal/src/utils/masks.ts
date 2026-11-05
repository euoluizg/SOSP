/**
 * SOSP — Máscaras de Entrada para Formulários
 * Atende RF-01, RF-02 e padrões do Design System
 */

export function maskCPF(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 11);
  return digits
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
}

export function maskCEP(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 8);
  return digits.replace(/(\d{5})(\d{1,3})$/, "$1-$2");
}

export function maskPhone(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 11);
  if (digits.length <= 10) {
    // Fixo (XX) XXXX-XXXX
    return digits
      .replace(/(\d{2})(\d)/, "($1) $2")
      .replace(/(\d{4})(\d{1,4})$/, "$1-$2");
  }
  // Celular (XX) 9XXXX-XXXX
  return digits
    .replace(/(\d{2})(\d)/, "($1) $2")
    .replace(/(\d{5})(\d{1,4})$/, "$1-$2");
}

export function maskProtocol(value: string): string {
  // Protocolo AAAAMMDD-XXXX
  const clean = value.replace(/[^A-Za-z0-9]/g, "").toUpperCase().slice(0, 12);
  if (clean.length <= 8) return clean;
  return `${clean.slice(0, 8)}-${clean.slice(8, 12)}`;
}

export function cleanDigits(value: string): string {
  return value.replace(/\D/g, "");
}

