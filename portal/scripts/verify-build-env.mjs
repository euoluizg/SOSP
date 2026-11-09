#!/usr/bin/env node
/**
 * SOSP — Pre-build Environment Verifier
 * Executado antes de 'next build' e 'opennextjs-cloudflare build'.
 */

const apiUrl = process.env.NEXT_PUBLIC_API_URL;
const errors = [];

if (!apiUrl || apiUrl.trim() === "") {
  errors.push("NEXT_PUBLIC_API_URL está ausente ou vazia.");
} else {
  const trimmed = apiUrl.trim();
  if (!trimmed.includes("/api/v1")) {
    errors.push(`NEXT_PUBLIC_API_URL ('${trimmed}') deve conter obrigatoriamente '/api/v1'.`);
  }
  const lower = trimmed.toLowerCase();
  if (lower.includes("localhost") || lower.includes("127.0.0.1")) {
    errors.push(`NEXT_PUBLIC_API_URL ('${trimmed}') não pode conter 'localhost' ou '127.0.0.1' em builds.`);
  }
}

if (errors.length > 0) {
  console.error("\n❌ [SOSP BUILD GUARD] Bloqueio de Build — Variáveis de Ambiente Inválidas:");
  for (const err of errors) {
    console.error(`  - ${err}`);
  }
  console.error("\nDefina NEXT_PUBLIC_API_URL corretamente antes de construir o portal (ex.: https://sosp-backend-staging.onrender.com/api/v1).\n");
  process.exit(1);
}

console.log(`✓ [SOSP BUILD GUARD] Variável NEXT_PUBLIC_API_URL validada com sucesso: ${apiUrl}`);
