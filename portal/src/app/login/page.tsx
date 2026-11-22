"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ShieldCheck, Lock, User, Eye, EyeOff, AlertCircle, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { GovbrModal } from "@/components/features/auth/GovbrModal";
import { maskCPF } from "@/utils/masks";
import { isValidCPF, sanitizeRedirectUrl } from "@/utils/validations";
import { loginCitizen } from "@/services/apiClient";
import {
  AUTH_TOKEN_KEY,
  AUTH_USER_KEY,
  MANAGER_ROLES,
  notifyAuthSessionUpdated,
  SERVER_ROLES,
} from "@/utils/session";
import type { ProblemDetails } from "@/types/api";

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectParam = searchParams.get("redirect");
  const safeRedirect = sanitizeRedirectUrl(redirectParam);

  // Estados do formulário
  const [cpf, setCpf] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [isGovbrModalOpen, setIsGovbrModalOpen] = useState(false);

  // Regra RN-29: Bloqueio de 5 minutos após 5 tentativas inválidas consecutivas
  const [failedAttempts, setFailedAttempts] = useState(0);
  const [lockoutSeconds, setLockoutSeconds] = useState(0);

  useEffect(() => {
    if (lockoutSeconds <= 0) return;
    const interval = setInterval(() => {
      setLockoutSeconds((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [lockoutSeconds]);

  const handleCpfChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCpf(maskCPF(e.target.value));
    if (formError) setFormError(null);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (lockoutSeconds > 0) return;

    if (!cpf) {
      setFormError("Informe o seu CPF.");
      return;
    }
    if (!isValidCPF(cpf)) {
      setFormError("CPF inválido. Verifique os dígitos informados.");
      return;
    }
    if (!password || password.length < 4) {
      setFormError("Informe a sua senha cadastrada.");
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      const res = await loginCitizen(cpf, password);
      setFailedAttempts(0);
      if (typeof window !== "undefined") {
        localStorage.setItem(AUTH_TOKEN_KEY, res.token);
        localStorage.setItem(AUTH_USER_KEY, JSON.stringify(res.citizen));
        notifyAuthSessionUpdated();
      }
      const userRole = res.citizen?.role;
      if (safeRedirect) {
        router.push(safeRedirect);
      } else if (userRole && (SERVER_ROLES as readonly string[]).includes(userRole)) {
        router.push("/servidor/painel");
      } else if (userRole && (MANAGER_ROLES as readonly string[]).includes(userRole)) {
        router.push("/admin/orgaos");
      } else {
        router.push("/cidadao/meus-agendamentos");
      }
    } catch (err: unknown) {
      const problem = err as ProblemDetails;
      if (problem?.status === 429) {
        setLockoutSeconds(300);
        setFormError(problem.detail || "Conta temporariamente bloqueada por 5 minutos após 5 tentativas incorretas (Regra RN-29).");
      } else if (problem?.status === 401) {
        const nextAttempts = failedAttempts + 1;
        setFailedAttempts(nextAttempts);
        if (nextAttempts >= 5) {
          setLockoutSeconds(300);
          setFormError("Conta bloqueada temporariamente por 5 minutos após 5 tentativas incorretas (Regra RN-29).");
        } else {
          setFormError(`CPF ou senha incorretos. Tentativa ${nextAttempts} de 5 antes do bloqueio temporário.`);
        }
      } else {
        setFormError(problem?.detail || "Não foi possível conectar ao servidor. Verifique se o backend está em execução.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatLockoutTime = () => {
    const mins = Math.floor(lockoutSeconds / 60);
    const secs = lockoutSeconds % 60;
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  };

  return (
    <div className="min-h-[calc(100vh-280px)] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gray-50">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="w-12 h-12 bg-[#1351B4] rounded-xl flex items-center justify-center text-white shadow-lg">
            <ShieldCheck className="w-7 h-7" />
          </div>
        </div>
        <h1 className="mt-4 text-center text-2xl sm:text-3xl font-extrabold text-gray-900">
          Entrar no SOSP
        </h1>
        <p className="mt-2 text-center text-sm text-gray-600">
          Acesse seus agendamentos, orientações e serviços públicos
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-xl rounded-2xl sm:px-10 border border-gray-100">
          {/* Botão Gov.br — Regra D10 / RF-02 */}
          <div className="mb-6">
            <button
              type="button"
              onClick={() => setIsGovbrModalOpen(true)}
              className="w-full flex items-center justify-center gap-3 py-3 px-4 rounded-lg text-white font-semibold shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#1351B4]"
              style={{ backgroundColor: "#1351B4" }}
              aria-label="Entrar com a conta Gov.br (Abre modal informativo sobre v2.0)"
            >
              <span className="font-extrabold tracking-wide text-base">gov.br</span>
              <span className="text-sm font-medium border-l border-white/30 pl-3">
                Entrar com gov.br
              </span>
            </button>
            <p className="mt-2 text-xs text-center text-gray-500">
              Disponibilidade em atualização futura (v2.0).
            </p>
          </div>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center" aria-hidden="true">
              <div className="w-full border-t border-gray-200" />
            </div>
            <div className="relative flex justify-center text-xs uppercase tracking-wider">
              <span className="bg-white px-3 text-gray-500 font-semibold">
                Ou use seu CPF e senha
              </span>
            </div>
          </div>

          {/* Alerta de Erro ou Bloqueio (RN-29) */}
          {lockoutSeconds > 0 ? (
            <div
              className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-md"
              role="alert"
              aria-live="assertive"
            >
              <div className="flex items-start">
                <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                <div className="ml-3">
                  <h3 className="text-sm font-bold text-red-800">
                    Acesso temporariamente bloqueado
                  </h3>
                  <p className="text-xs text-red-700 mt-1">
                    Por motivo de segurança (Regra RN-29), aguarde o cronômetro para tentar novamente:
                  </p>
                  <p className="text-lg font-mono font-bold text-red-800 mt-2">
                    {formatLockoutTime()}
                  </p>
                </div>
              </div>
            </div>
          ) : formError ? (
            <div
              className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-md"
              role="alert"
              aria-live="polite"
            >
              <div className="flex">
                <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                <p className="ml-3 text-sm text-red-700">{formError}</p>
              </div>
            </div>
          ) : null}

          {/* Formulário de Login Local */}
          <form className="space-y-5" onSubmit={handleLogin} noValidate>
            <Input
              label="Número do CPF"
              id="cpf"
              name="cpf"
              type="text"
              inputMode="numeric"
              placeholder="000.000.000-00"
              value={cpf}
              onChange={handleCpfChange}
              disabled={lockoutSeconds > 0 || isSubmitting}
              required
              helperText="Digite apenas os 11 números do seu documento"
            />

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="password"
                  className="block text-sm font-semibold text-gray-700"
                >
                  Senha de acesso
                </label>
                <Link
                  href="/recuperar-senha"
                  className="text-xs font-semibold text-[#1351B4] hover:underline focus:outline-none focus:ring-2 focus:ring-[#1351B4] rounded"
                >
                  Esqueceu a senha?
                </Link>
              </div>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (formError) setFormError(null);
                  }}
                  disabled={lockoutSeconds > 0 || isSubmitting}
                  required
                  placeholder="Digite sua senha cadastrada"
                  className="w-full px-4 py-3 pr-11 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#1351B4] focus:border-[#1351B4] transition-all min-h-[44px]"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-1 rounded-md focus:outline-none focus:ring-2 focus:ring-[#1351B4]"
                  aria-label={showPassword ? "Ocultar senha" : "Exibir senha"}
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              isLoading={isSubmitting}
              disabled={lockoutSeconds > 0}
              className="w-full justify-center py-3 text-base font-semibold shadow-md"
            >
              Entrar no sistema
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </form>

          {/* Links de Rodapé */}
          <div className="mt-6 pt-6 border-t border-gray-100 text-center space-y-3">
            <p className="text-sm text-gray-600">
              Ainda não tem conta no SOSP?{" "}
              <Link
                href={safeRedirect ? `/cadastro?redirect=${encodeURIComponent(safeRedirect)}` : "/cadastro"}
                className="font-bold text-[#1351B4] hover:underline focus:outline-none focus:ring-2 focus:ring-[#1351B4] rounded"
              >
                Cadastre-se gratuitamente
              </Link>
            </p>
            <div className="pt-2 border-t border-gray-50">
              <p className="text-xs text-gray-500">
                É servidor público ou gestor institucional?{" "}
                <Link
                  href="/login/institucional"
                  className="font-semibold text-[#1351B4] hover:underline inline-flex items-center gap-1"
                >
                  Acesse o portal institucional
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Modal Informativo Gov.br — Regra D10 */}
      <GovbrModal
        isOpen={isGovbrModalOpen}
        onClose={() => setIsGovbrModalOpen(false)}
      />
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[calc(100vh-280px)] flex items-center justify-center py-12 px-4 bg-gray-50">
          <p className="text-gray-500 text-sm">Carregando...</p>
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}

