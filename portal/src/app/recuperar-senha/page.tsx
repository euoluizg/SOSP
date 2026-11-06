"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { KeyRound, Mail, CheckCircle2, ArrowLeft, ArrowRight, Clock } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { maskCPF } from "@/utils/masks";
import { isValidCPF, validatePasswordStrength } from "@/utils/validations";
import { recoverPassword, resetPassword } from "@/services/apiClient";
import type { ProblemDetails } from "@/types/api";

export default function PasswordRecoveryPage() {
  const router = useRouter();

  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [cpf, setCpf] = useState("");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Contador de expiração de 15 minutos do código (RN-30)
  const [secondsRemaining, setSecondsRemaining] = useState(15 * 60);

  useEffect(() => {
    if (step !== 2) return;
    const interval = setInterval(() => {
      setSecondsRemaining((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [step]);

  const handleCpfSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValidCPF(cpf)) {
      setError("Informe um CPF válido para recuperar a senha.");
      return;
    }
    setError(null);
    setIsLoading(true);

    try {
      await recoverPassword(cpf);
      setStep(2); // Avança para inserção do código
      setSecondsRemaining(15 * 60);
    } catch (err: unknown) {
      const problem = err as ProblemDetails;
      setError(problem?.detail || "Erro ao conectar ao servidor. Verifique sua conexão.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCodeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanCode = code.replace(/\D/g, "");
    if (cleanCode.length !== 6) {
      setError("O código de verificação deve ter exatamente 6 dígitos.");
      return;
    }
    if (secondsRemaining <= 0) {
      setError("O código expirou. Solicite um novo envio de código.");
      return;
    }
    setError(null);
    setStep(3); // Avança para nova senha
  };

  const handlePasswordReset = async (e: React.FormEvent) => {
    e.preventDefault();
    const strength = validatePasswordStrength(newPassword);
    if (!strength.isValid) {
      setError("A nova senha deve ter no mínimo 8 caracteres, maiúsculas, minúsculas, números e caracteres especiais.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("As senhas informadas não coincidem.");
      return;
    }
    setError(null);
    setIsLoading(true);

    try {
      await resetPassword(cpf, code, newPassword);
      setStep(4); // Sucesso
    } catch (err: unknown) {
      const problem = err as ProblemDetails;
      setError(problem?.detail || "Código inválido ou erro ao redefinir a senha.");
    } finally {
      setIsLoading(false);
    }
  };

  const formatTimer = () => {
    const mins = Math.floor(secondsRemaining / 60);
    const secs = secondsRemaining % 60;
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  };

  return (
    <div className="min-h-[calc(100vh-280px)] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gray-50">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center text-[#1351B4]">
            <KeyRound className="w-7 h-7" />
          </div>
        </div>
        <h1 className="mt-4 text-center text-2xl font-extrabold text-gray-900">
          Recuperação de Senha
        </h1>
        <p className="mt-1 text-center text-sm text-gray-600">
          Redefina sua senha de acesso em conformidade com a regra RN-30
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-xl rounded-2xl sm:px-10 border border-gray-100">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Passo 1: Informar CPF */}
          {step === 1 && (
            <form onSubmit={handleCpfSubmit} className="space-y-5">
              <p className="text-sm text-gray-600">
                Digite seu CPF. Enviaremos um código de 6 dígitos para o e-mail cadastrado na sua conta.
              </p>
              <Input
                label="Número do CPF"
                id="cpf"
                name="cpf"
                placeholder="000.000.000-00"
                value={cpf}
                onChange={(e) => {
                  setCpf(maskCPF(e.target.value));
                  setError(null);
                }}
                required
              />
              <Button
                type="submit"
                variant="primary"
                isLoading={isLoading}
                className="w-full justify-center"
              >
                Enviar código por e-mail
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </form>
          )}

          {/* Passo 2: Digitar código de 6 dígitos */}
          {step === 2 && (
            <form onSubmit={handleCodeSubmit} className="space-y-5">
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-3 text-xs text-blue-900">
                <Clock className="w-4 h-4 shrink-0 text-[#1351B4]" />
                <span>
                  Código enviado por e-mail! Válido por 15 minutos:{" "}
                  <strong>{formatTimer()}</strong>
                </span>
              </div>
              <Input
                label="Código de verificação (6 dígitos)"
                id="code"
                name="code"
                maxLength={6}
                placeholder="123456"
                value={code}
                onChange={(e) => {
                  setCode(e.target.value.replace(/\D/g, ""));
                  setError(null);
                }}
                required
                helperText="Verifique também sua caixa de spam ou lixo eletrônico"
              />
              <Button
                type="submit"
                variant="primary"
                isLoading={isLoading}
                className="w-full justify-center"
              >
                Validar código
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </form>
          )}

          {/* Passo 3: Criar nova senha */}
          {step === 3 && (
            <form onSubmit={handlePasswordReset} className="space-y-5">
              <p className="text-sm text-gray-600">
                Código validado com sucesso! Agora defina uma nova senha forte para sua conta.
              </p>
              <Input
                label="Nova senha"
                id="newPassword"
                name="newPassword"
                type="password"
                placeholder="Mínimo 8 caracteres"
                value={newPassword}
                onChange={(e) => {
                  setNewPassword(e.target.value);
                  setError(null);
                }}
                required
              />
              <Input
                label="Confirme a nova senha"
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                placeholder="Repita a nova senha"
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  setError(null);
                }}
                required
              />
              <Button
                type="submit"
                variant="primary"
                isLoading={isLoading}
                className="w-full justify-center"
              >
                Salvar nova senha
              </Button>
            </form>
          )}

          {/* Passo 4: Sucesso */}
          {step === 4 && (
            <div className="text-center py-4">
              <div className="w-14 h-14 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">Senha Alterada!</h2>
              <p className="mt-2 text-sm text-gray-600">
                Sua senha foi redefinida com segurança. Você já pode fazer login com as novas credenciais.
              </p>
              <div className="mt-6">
                <Button
                  variant="primary"
                  className="w-full justify-center"
                  onClick={() => router.push("/login")}
                >
                  Ir para a página de Login
                </Button>
              </div>
            </div>
          )}

          {/* Link para voltar */}
          {step !== 4 && (
            <div className="mt-6 pt-6 border-t border-gray-100 text-center">
              <Link
                href="/login"
                className="inline-flex items-center text-sm font-semibold text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft className="w-4 h-4 mr-1" />
                Voltar para o login
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

