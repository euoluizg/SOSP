"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Building2, Lock, Eye, EyeOff, AlertCircle, ArrowRight, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { maskCPF } from "@/utils/masks";
import { isValidCPF, sanitizeRedirectUrl } from "@/utils/validations";
import { loginCitizen } from "@/services/apiClient";
import type { ProblemDetails } from "@/types/api";

function InstitutionalLoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectParam = searchParams.get("redirect");
  const safeRedirect = sanitizeRedirectUrl(redirectParam);

  const [cpf, setCpf] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

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
      setFormError("Informe o seu CPF funcional.");
      return;
    }
    if (!isValidCPF(cpf)) {
      setFormError("CPF inválido. Verifique os dígitos informados.");
      return;
    }
    if (!password || password.length < 4) {
      setFormError("Informe a sua senha institucional.");
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      const res = await loginCitizen(cpf, password);
      setFailedAttempts(0);
      if (typeof window !== "undefined") {
        localStorage.setItem("sosp_auth_token", res.token);
        localStorage.setItem("sosp_user", JSON.stringify(res.citizen));
      }

      // Validação de perfil institucional
      const role = res.citizen?.role;
      if (role === "citizen") {
        setFormError(
          "Esta conta possui perfil de Cidadão. Por favor, acesse o portal do cidadão."
        );
        return;
      }

      if (safeRedirect) {
        router.push(safeRedirect);
      } else if (role === "server") {
        router.push("/servidor/painel");
      } else {
        router.push("/admin/orgaos");
      }
    } catch (err: unknown) {
      const problem = err as ProblemDetails;
      if (problem?.status === 429) {
        setLockoutSeconds(300);
        setFormError(
          problem.detail ||
            "Acesso temporariamente bloqueado por 5 minutos após 5 tentativas incorretas (Regra RN-29)."
        );
      } else if (problem?.status === 401) {
        const nextAttempts = failedAttempts + 1;
        setFailedAttempts(nextAttempts);
        if (nextAttempts >= 5) {
          setLockoutSeconds(300);
          setFormError(
            "Acesso bloqueado temporariamente por 5 minutos após 5 tentativas incorretas (Regra RN-29)."
          );
        } else {
          setFormError(
            `CPF ou senha incorretos. Tentativa ${nextAttempts} de 5 antes do bloqueio temporário.`
          );
        }
      } else {
        setFormError(
          problem?.detail ||
            "Não foi possível conectar ao servidor institucional. Verifique a conexão com o backend."
        );
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
    <div className="min-h-[calc(100vh-280px)] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 bg-slate-50">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="w-12 h-12 bg-[#0F2942] rounded-xl flex items-center justify-center text-white shadow-lg">
            <Building2 className="w-7 h-7" />
          </div>
        </div>
        <div className="mt-4 text-center">
          <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-[#1351B4] mb-2">
            Portal Institucional
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900">
            Acesso Restrito
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Para Servidores Públicos, Gestores e Administradores do SOSP
          </p>
        </div>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-xl rounded-2xl sm:px-10 border border-slate-200">
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
                    Acesso institucional temporariamente bloqueado
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

          {/* Formulário de Login Institucional */}
          <form className="space-y-5" onSubmit={handleLogin} noValidate>
            <Input
              label="CPF do Servidor ou Gestor"
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
                  Senha institucional
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
                  className="w-full px-4 py-3 pr-11 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0F2942] focus:border-[#0F2942] transition-all min-h-[44px]"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-1 rounded-md focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
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
              className="w-full justify-center py-3 text-base font-semibold shadow-md !bg-[#0F2942] hover:!bg-[#1351B4]"
            >
              Acessar Painel Institucional
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </form>

          {/* Link para Portal do Cidadão */}
          <div className="mt-6 pt-6 border-t border-gray-100 text-center">
            <Link
              href="/login"
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-gray-600 hover:text-[#1351B4]"
            >
              <ArrowLeft className="w-4 h-4" />
              Voltar ao login do cidadão
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function InstitutionalLoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[calc(100vh-280px)] flex items-center justify-center py-12 px-4 bg-slate-50">
          <p className="text-gray-500 text-sm">Carregando portal institucional...</p>
        </div>
      }
    >
      <InstitutionalLoginContent />
    </Suspense>
  );
}
