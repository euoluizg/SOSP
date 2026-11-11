"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Building2,
  Eye,
  EyeOff,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  KeyRound,
  CheckCircle2,
  ShieldCheck,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { maskCPF } from "@/utils/masks";
import { isValidCPF, sanitizeRedirectUrl } from "@/utils/validations";
import { loginCitizen, changePassword } from "@/services/apiClient";
import type { ProblemDetails, UserSession } from "@/types/api";

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

  // Estados para fluxo de Primeiro Acesso (Troca Obrigatória de Senha Provisória)
  const [mustChangePasswordMode, setMustChangePasswordMode] = useState(false);
  const [authenticatedUser, setAuthenticatedUser] = useState<UserSession | null>(null);
  const [currentPasswordForChange, setCurrentPasswordForChange] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [changePasswordError, setChangePasswordError] = useState<string | null>(null);
  const [changePasswordSuccess, setChangePasswordSuccess] = useState<string | null>(null);
  const [isChangingPassword, setIsChangingPassword] = useState(false);

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

      // Validação estrita de perfil institucional antes de iniciar sessão (RN-35, RN-36, ADR-003)
      const role = res.citizen?.role;
      const allowedRoles = ["server", "servant", "gestor", "manager", "admin", "superadmin"];

      if (role === "citizen") {
        setFormError(
          "Esta conta possui perfil de Cidadão. Por favor, acesse o portal do cidadão."
        );
        return;
      }

      if (!role || !allowedRoles.includes(role)) {
        setFormError(
          "Perfil de acesso institucional não reconhecido ou sem permissão de acesso a este painel."
        );
        return;
      }

      setFailedAttempts(0);

      // Interceptação obrigatória de Primeiro Acesso (mustChangePassword)
      if (res.citizen?.mustChangePassword) {
        setMustChangePasswordMode(true);
        setAuthenticatedUser(res.citizen);
        setCurrentPasswordForChange(password);
        if (typeof window !== "undefined") {
          localStorage.setItem("sosp_auth_token", res.token);
          localStorage.setItem("sosp_user", JSON.stringify(res.citizen));
        }
        return;
      }

      // Sessão regular estabelecida
      if (typeof window !== "undefined") {
        localStorage.setItem("sosp_auth_token", res.token);
        localStorage.setItem("sosp_user", JSON.stringify(res.citizen));
      }

      if (safeRedirect) {
        router.push(safeRedirect);
      } else if (role === "server" || role === "servant") {
        router.push("/servidor/painel");
      } else {
        // gestor, manager, admin, superadmin
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

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setChangePasswordError(null);

    if (!currentPasswordForChange) {
      setChangePasswordError("Informe a senha provisória atual.");
      return;
    }
    if (!newPassword || newPassword.length < 8) {
      setChangePasswordError("A nova senha deve ter no mínimo 8 caracteres.");
      return;
    }
    if (newPassword === currentPasswordForChange) {
      setChangePasswordError("A nova senha deve ser diferente da senha provisória atual.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setChangePasswordError("A confirmação de senha não coincide com a nova senha.");
      return;
    }

    setIsChangingPassword(true);
    try {
      const res = await changePassword(currentPasswordForChange, newPassword, confirmPassword);
      setChangePasswordSuccess(res.message || "Senha atualizada com sucesso!");

      const role = authenticatedUser?.role;
      if (typeof window !== "undefined") {
        if (res.token) {
          localStorage.setItem("sosp_auth_token", res.token);
        }
        if (authenticatedUser) {
          localStorage.setItem(
            "sosp_user",
            JSON.stringify({ ...authenticatedUser, mustChangePassword: false })
          );
        }
      }

      setTimeout(() => {
        if (safeRedirect) {
          router.push(safeRedirect);
        } else if (role === "server" || role === "servant") {
          router.push("/servidor/painel");
        } else {
          router.push("/admin/orgaos");
        }
      }, 1000);
    } catch (err: unknown) {
      const problem = err as ProblemDetails;
      setChangePasswordError(
        problem?.detail || "Não foi possível alterar a senha provisória. Tente novamente."
      );
    } finally {
      setIsChangingPassword(false);
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
          {/* Formulário Normal de Login Institucional */}
          <div>
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

            <form className="space-y-5" onSubmit={handleLogin} noValidate>
              <div>
                <label
                  htmlFor="cpf"
                  className="block text-sm font-semibold text-gray-700 mb-1.5"
                >
                  CPF do Servidor ou Gestor
                </label>
                <input
                  id="cpf"
                  name="cpf"
                  type="text"
                  autoComplete="username"
                  required
                  value={cpf}
                  onChange={handleCpfChange}
                  disabled={isSubmitting || lockoutSeconds > 0}
                  placeholder="000.000.000-00"
                  maxLength={14}
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#0F2942] focus:border-transparent min-h-[44px]"
                  aria-describedby="cpf-hint"
                />
                <p id="cpf-hint" className="text-xs text-gray-500 mt-1">
                  Digite apenas os 11 números do seu documento
                </p>
              </div>

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
                    className="text-xs font-semibold text-[#1351B4] hover:underline"
                  >
                    Esqueceu a senha?
                  </Link>
                </div>
                <div className="relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={isSubmitting || lockoutSeconds > 0}
                    placeholder="••••••••••••"
                    className="w-full px-4 py-3 pr-11 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#0F2942] focus:border-transparent min-h-[44px]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-1 cursor-pointer focus:outline-none min-h-[44px] min-w-[44px] flex items-center justify-center"
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
                className="w-full justify-center py-3 text-base font-semibold shadow-md !bg-[#0F2942] hover:!bg-[#1351B4] cursor-pointer"
              >
                Acessar Painel Institucional
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </form>

            <div className="mt-8 pt-6 border-t border-gray-100 text-center">
              <Link
                href="/login"
                className="inline-flex items-center text-sm font-medium text-gray-600 hover:text-[#0F2942] transition-colors"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Voltar ao login do cidadão
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Pop-up Modal no Meio da Tela para Definição de Nova Senha no Primeiro Acesso */}
      {mustChangePasswordMode && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-password-title"
        >
          <div className="w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden animate-in zoom-in-95 duration-200 max-h-[92vh] flex flex-col">
            {/* Header do Pop-up */}
            <div className="p-6 bg-slate-50 border-b border-slate-200 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3.5">
                <div className="w-12 h-12 bg-[#0F2942] rounded-xl flex items-center justify-center text-white shadow-md shrink-0">
                  <KeyRound className="w-6 h-6" />
                </div>
                <div>
                  <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-[#1351B4] mb-1">
                    Primeiro Acesso Obrigatório
                  </span>
                  <h2 id="modal-password-title" className="text-xl font-extrabold text-gray-900">
                    Definição de Nova Senha
                  </h2>
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  setMustChangePasswordMode(false);
                  setFormError(null);
                  setChangePasswordError(null);
                }}
                className="text-gray-400 hover:text-gray-600 p-2 rounded-lg hover:bg-slate-200/50 transition-colors cursor-pointer min-h-[44px] min-w-[44px] flex items-center justify-center"
                aria-label="Fechar pop-up e voltar ao login"
              >
                <span className="text-xl font-bold leading-none">&times;</span>
              </button>
            </div>

            {/* Corpo do Pop-up */}
            <div className="p-6 sm:p-8 overflow-y-auto">
              <div className="mb-5 p-3.5 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-2.5">
                <ShieldCheck className="w-5 h-5 text-[#1351B4] shrink-0 mt-0.5" />
                <p className="text-xs text-blue-900 leading-relaxed">
                  Esta conta foi provisionada com credencial provisória. Por conformidade com a política
                  de segurança (ADR-003), é obrigatório cadastrar uma senha permanente no primeiro acesso.
                </p>
              </div>

              {changePasswordSuccess ? (
                <div
                  className="mb-6 p-4 bg-green-50 border-l-4 border-green-500 rounded-md"
                  role="alert"
                  aria-live="polite"
                >
                  <div className="flex">
                    <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
                    <p className="ml-3 text-sm text-green-800 font-medium">{changePasswordSuccess}</p>
                  </div>
                </div>
              ) : null}

              {changePasswordError ? (
                <div
                  className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-md"
                  role="alert"
                  aria-live="polite"
                >
                  <div className="flex">
                    <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                    <p className="ml-3 text-sm text-red-700">{changePasswordError}</p>
                  </div>
                </div>
              ) : null}

              <form className="space-y-4" onSubmit={handleChangePassword} noValidate>
                <div>
                  <label htmlFor="currentPassword" className="block text-sm font-semibold text-gray-700 mb-1.5">
                    Senha provisória atual
                  </label>
                  <div className="relative">
                    <input
                      id="currentPassword"
                      name="currentPassword"
                      type={showCurrentPassword ? "text" : "password"}
                      value={currentPasswordForChange}
                      onChange={(e) => setCurrentPasswordForChange(e.target.value)}
                      disabled={isChangingPassword || !!changePasswordSuccess}
                      required
                      className="w-full px-4 py-3 pr-11 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#0F2942] min-h-[44px]"
                    />
                    <button
                      type="button"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-1"
                      aria-label={showCurrentPassword ? "Ocultar senha" : "Exibir senha"}
                    >
                      {showCurrentPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label htmlFor="newPassword" className="block text-sm font-semibold text-gray-700 mb-1.5">
                    Nova senha permanente
                  </label>
                  <div className="relative">
                    <input
                      id="newPassword"
                      name="newPassword"
                      type={showNewPassword ? "text" : "password"}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      disabled={isChangingPassword || !!changePasswordSuccess}
                      required
                      placeholder="Mínimo 8 caracteres"
                      className="w-full px-4 py-3 pr-11 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#0F2942] min-h-[44px]"
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-1"
                      aria-label={showNewPassword ? "Ocultar senha" : "Exibir senha"}
                    >
                      {showNewPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Deve conter maiúsculas, minúsculas, números e caracteres especiais.
                  </p>
                </div>

                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-semibold text-gray-700 mb-1.5">
                    Confirme a nova senha
                  </label>
                  <div className="relative">
                    <input
                      id="confirmPassword"
                      name="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      disabled={isChangingPassword || !!changePasswordSuccess}
                      required
                      placeholder="Repita a nova senha"
                      className="w-full px-4 py-3 pr-11 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#0F2942] min-h-[44px]"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-1"
                      aria-label={showConfirmPassword ? "Ocultar senha" : "Exibir senha"}
                    >
                      {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  isLoading={isChangingPassword}
                  disabled={!!changePasswordSuccess}
                  className="w-full justify-center py-3 text-base font-semibold shadow-md !bg-[#0F2942] hover:!bg-[#1351B4] mt-2 cursor-pointer"
                >
                  Salvar Nova Senha e Acessar
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </form>

              <div className="mt-4 pt-4 border-t border-gray-100 text-center">
                <button
                  type="button"
                  onClick={() => {
                    setMustChangePasswordMode(false);
                    setFormError(null);
                    setChangePasswordError(null);
                  }}
                  className="text-xs font-semibold text-gray-500 hover:text-gray-700 cursor-pointer min-h-[44px] inline-flex items-center"
                >
                  Cancelar e voltar para o login
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
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
