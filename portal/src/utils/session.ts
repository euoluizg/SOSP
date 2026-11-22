import type { UserSession } from "@/types/api";

export const AUTH_TOKEN_KEY = "sosp_auth_token";
export const AUTH_USER_KEY = "sosp_user";
export const SESSION_CLEARED_EVENT = "sosp:session-cleared";
export const SESSION_UPDATED_EVENT = "sosp:session-updated";

export const INSTITUTIONAL_ROLES = [
  "server",
  "servant",
  "gestor",
  "manager",
  "admin",
  "superadmin",
] as const;

export const SERVER_ROLES = ["server", "servant"] as const;

export const MANAGER_ROLES = ["gestor", "manager", "admin", "superadmin"] as const;

/**
 * Indica se o papel informado pertence ao acesso institucional (servidor, gestor ou admin).
 */
export function isInstitutionalRole(role?: string | null): boolean {
  return !!role && (INSTITUTIONAL_ROLES as readonly string[]).includes(role);
}

/**
 * Indica se a rota atual pertence aos painéis restritos institucionais.
 */
export function isInstitutionalPath(pathname?: string | null): boolean {
  return !!pathname && (pathname.startsWith("/admin") || pathname.startsWith("/servidor"));
}

/**
 * Lê e interpreta com segurança os dados do usuário salvos em localStorage.
 */
export function getStoredUserSession(): Partial<UserSession> | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(AUTH_USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Partial<UserSession>;
  } catch {
    return null;
  }
}

/**
 * Remove token e metadados residuais de usuário e notifica os componentes ouvintes.
 */
export function clearAuthSessionStorage(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
  window.dispatchEvent(new Event(SESSION_CLEARED_EVENT));
}

/**
 * Notifica os componentes ouvintes que a sessão ativa foi atualizada em localStorage.
 */
export function notifyAuthSessionUpdated(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(SESSION_UPDATED_EVENT));
}
