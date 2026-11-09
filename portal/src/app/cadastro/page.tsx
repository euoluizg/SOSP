"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  User,
  Mail,
  Phone,
  MapPin,
  Lock,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Eye,
  EyeOff,
  ArrowLeft,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { CriticalConfirmationModal } from "@/components/ui/CriticalConfirmationModal";
import { maskCPF, maskCEP, maskPhone } from "@/utils/masks";
import {
  isValidCPF,
  isValidEmail,
  isValidBirthDate,
  validatePasswordStrength,
} from "@/utils/validations";
import { registerCitizen } from "@/services/apiClient";
import type { ProblemDetails } from "@/types/api";

export default function RegisterPage() {
  const router = useRouter();

  // Estados dos 19 campos
  const [formData, setFormData] = useState({
    fullName: "",
    cpf: "",
    birthDate: "",
    gender: "",
    genderDescription: "",
    motherName: "",
    isPcd: false,
    disabilityType: "",
    email: "",
    confirmEmail: "",
    mobilePhone: "",
    landlinePhone: "",
    cep: "",
    street: "",
    number: "",
    complement: "",
    neighborhood: "",
    city: "",
    state: "",
    password: "",
    confirmPassword: "",
    acceptTerms: false,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [isSearchingCep, setIsSearchingCep] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);

  // Manipuladores de input
  const handleChange = (
    field: string,
    value: string | boolean
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const updated = { ...prev };
        delete updated[field];
        return updated;
      });
    }
  };

  // Autopreenchimento de CEP via ViaCEP com fallback manual (RF-01)
  const handleCepBlur = async () => {
    const rawCep = formData.cep.replace(/\D/g, "");
    if (rawCep.length !== 8) return;

    setIsSearchingCep(true);
    try {
      const res = await fetch(`https://viacep.com.br/ws/${rawCep}/json/`);
      const data = await res.json();
      if (!data.erro) {
        setFormData((prev) => ({
          ...prev,
          street: data.logradouro || prev.street,
          neighborhood: data.bairro || prev.neighborhood,
          city: data.localidade || prev.city,
          state: data.uf || prev.state,
        }));
      }
    } catch {
      // Fallback silencioso para preenchimento manual
    } finally {
      setIsSearchingCep(false);
    }
  };

  // Validação completa antes do envio
  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.fullName.trim() || formData.fullName.trim().length < 3) {
      newErrors.fullName = "Nome completo é obrigatório (mínimo 3 caracteres).";
    }

    if (!isValidCPF(formData.cpf)) {
      newErrors.cpf = "CPF inválido. Verifique os números informados.";
    }

    const birthCheck = isValidBirthDate(formData.birthDate);
    if (!birthCheck.valid) {
      newErrors.birthDate = birthCheck.message || "Data de nascimento inválida.";
    }

    if (!formData.motherName.trim()) {
      newErrors.motherName = "Nome da mãe é obrigatório para conferência cadastral.";
    }

    if (formData.isPcd && !formData.disabilityType.trim()) {
      newErrors.disabilityType = "Por favor, especifique o tipo de deficiência.";
    }

    if (!isValidEmail(formData.email)) {
      newErrors.email = "Informe um e-mail válido.";
    }

    if (formData.email !== formData.confirmEmail) {
      newErrors.confirmEmail = "Os e-mails informados não coincidem.";
    }

    const mobileDigits = formData.mobilePhone.replace(/\D/g, "");
    if (mobileDigits.length < 10) {
      newErrors.mobilePhone = "Celular de contato é obrigatório.";
    }

    const cepDigits = formData.cep.replace(/\D/g, "");
    if (cepDigits.length !== 8) {
      newErrors.cep = "CEP é obrigatório (8 dígitos).";
    }

    if (!formData.street.trim()) newErrors.street = "Logradouro é obrigatório.";
    if (!formData.number.trim()) newErrors.number = "Número é obrigatório.";
    if (!formData.neighborhood.trim()) newErrors.neighborhood = "Bairro é obrigatório.";
    if (!formData.city.trim()) newErrors.city = "Município é obrigatório.";
    if (!formData.state.trim()) newErrors.state = "UF é obrigatório.";

    const passCheck = validatePasswordStrength(formData.password);
    if (!passCheck.isValid) {
      newErrors.password =
        "A senha deve conter no mínimo 8 caracteres, maiúsculas, minúsculas, números e caracteres especiais.";
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "As senhas não coincidem.";
    }

    if (!formData.acceptTerms) {
      newErrors.acceptTerms = "Você deve aceitar os Termos de Uso e Política de Privacidade.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError(null);
    if (!validateForm()) {
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }

    setIsSubmitting(true);
    try {
      await registerCitizen({
        fullName: formData.fullName,
        cpf: formData.cpf,
        birthDate: formData.birthDate,
        gender: formData.gender,
        motherName: formData.motherName,
        email: formData.email,
        phone: formData.mobilePhone || formData.landlinePhone,
        mobilePhone: formData.mobilePhone,
        landlinePhone: formData.landlinePhone,
        password: formData.password,
        isPcd: formData.isPcd,
        pcdDetails: formData.disabilityType,
        disabilityType: formData.disabilityType,
        cep: formData.cep,
        zipCode: formData.cep,
        street: formData.street,
        number: formData.number,
        complement: formData.complement,
        neighborhood: formData.neighborhood,
        city: formData.city,
        state: formData.state,
      });
      setSubmitSuccess(true);
    } catch (err: unknown) {
      const problem = err as ProblemDetails;
      if (problem?.errors && problem.errors.length > 0) {
        const mappedErrors: Record<string, string> = {};
        problem.errors.forEach((e) => {
          mappedErrors[e.field] = e.message;
        });
        setErrors((prev) => ({ ...prev, ...mappedErrors }));
        setApiError(problem.detail || "Verifique os campos destacados em vermelho.");
      } else {
        setApiError(problem?.detail || "Erro ao conectar ao servidor. Tente novamente mais tarde.");
      }
      window.scrollTo({ top: 0, behavior: "smooth" });
    } finally {
      setIsSubmitting(false);
    }
  };

  const passStrength = validatePasswordStrength(formData.password);

  const passwordCriteria = [
    { label: "Mínimo de 8 caracteres", met: formData.password.length >= 8 },
    { label: "Pelo menos uma letra maiúscula (A-Z)", met: /[A-Z]/.test(formData.password) },
    { label: "Pelo menos uma letra minúscula (a-z)", met: /[a-z]/.test(formData.password) },
    { label: "Pelo menos um número (0-9)", met: /\d/.test(formData.password) },
    { label: "Pelo menos um caractere especial (!@#$%...)", met: /[^A-Za-z0-9]/.test(formData.password) },
  ];

  if (submitSuccess) {
    return (
      <div className="min-h-[calc(100vh-280px)] flex items-center justify-center py-12 px-4 bg-gray-50">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center border border-green-100 animate-fadeIn">
          <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-5">
            <CheckCircle2 className="w-10 h-10" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Cadastro Concluído com Sucesso!</h2>
          <p className="mt-3 text-sm text-gray-600 leading-relaxed">
            Seu cadastro no SOSP foi registrado com sucesso. Um e-mail de confirmação foi enviado
            para <span className="font-semibold text-gray-900">{formData.email}</span>.
          </p>
          <div className="mt-8">
            <Button
              variant="primary"
              className="w-full justify-center py-3 text-base"
              onClick={() => router.push("/login")}
            >
              Fazer Login Agora
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        {/* Cabeçalho */}
        <div className="mb-8">
          <Link
            href="/login"
            className="inline-flex items-center text-sm font-semibold text-[#1351B4] hover:underline mb-4 focus:outline-none focus:ring-2 focus:ring-[#1351B4] rounded"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Voltar para o login
          </Link>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900">
            Criar conta no SOSP
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Preencha seus dados para ter acesso a agendamentos, checklists e acompanhamento de serviços
            públicos.
          </p>
        </div>

        {/* Formulário Principal */}
        <form onSubmit={handleSubmit} className="space-y-8" noValidate>
          {apiError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3 text-red-700 text-sm font-medium">
              <AlertCircle className="w-5 h-5 shrink-0 text-red-600" />
              <span>{apiError}</span>
            </div>
          )}

          {/* Seção 1: Dados Pessoais */}
          <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
            <div className="flex items-center gap-3 pb-4 mb-6 border-b border-gray-100">
              <div className="w-10 h-10 rounded-lg bg-blue-50 text-[#1351B4] flex items-center justify-center">
                <User className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-gray-900">1. Dados Pessoais</h2>
                <p className="text-xs text-gray-500">Informações de identificação oficial</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <Input
                  label="Nome completo"
                  id="fullName"
                  name="fullName"
                  placeholder="Nome idêntico ao RG ou certidão"
                  value={formData.fullName}
                  onChange={(e) => handleChange("fullName", e.target.value)}
                  error={errors.fullName}
                  required
                />
              </div>

              <div>
                <Input
                  label="CPF"
                  id="cpf"
                  name="cpf"
                  placeholder="000.000.000-00"
                  value={formData.cpf}
                  onChange={(e) => handleChange("cpf", maskCPF(e.target.value))}
                  error={errors.cpf}
                  required
                  helperText="Apenas números"
                />
              </div>

              <div>
                <Input
                  label="Data de nascimento"
                  id="birthDate"
                  name="birthDate"
                  type="date"
                  value={formData.birthDate}
                  onChange={(e) => handleChange("birthDate", e.target.value)}
                  error={errors.birthDate}
                  required
                  helperText="Mínimo 12 anos completos"
                />
              </div>

              <div>
                <Select
                  label="Sexo / Gênero"
                  id="gender"
                  name="gender"
                  value={formData.gender}
                  onChange={(e) => handleChange("gender", e.target.value)}
                  options={[
                    { value: "", label: "Selecione uma opção" },
                    { value: "F", label: "Feminino" },
                    { value: "M", label: "Masculino" },
                    { value: "O", label: "Outro" },
                    { value: "N", label: "Prefiro não informar" },
                  ]}
                />
                {formData.gender === "O" && (
                  <div className="mt-3 animate-fadeIn" aria-live="polite">
                    <Input
                      label="Qual? (informe como você se identifica)"
                      id="genderDescription"
                      name="genderDescription"
                      placeholder="Informe sua identidade de gênero"
                      value={formData.genderDescription}
                      onChange={(e) => handleChange("genderDescription", e.target.value)}
                      error={errors.genderDescription}
                      helperText="Opcional. Campo destinado à inclusão e respeito à sua identidade."
                    />
                  </div>
                )}
              </div>

              <div>
                <Input
                  label="Nome da mãe"
                  id="motherName"
                  name="motherName"
                  placeholder="Nome completo da genitora"
                  value={formData.motherName}
                  onChange={(e) => handleChange("motherName", e.target.value)}
                  error={errors.motherName}
                  required
                />
              </div>

              {/* PCD Sim/Não e condicional */}
              <div className="sm:col-span-2 pt-2">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Pessoa com Deficiência (PCD)?
                </label>
                <div className="flex gap-4">
                  <label className="inline-flex items-center">
                    <input
                      type="radio"
                      name="isPcd"
                      checked={formData.isPcd === false}
                      onChange={() => handleChange("isPcd", false)}
                      className="w-4 h-4 text-[#1351B4] focus:ring-[#1351B4]"
                    />
                    <span className="ml-2 text-sm text-gray-700">Não</span>
                  </label>
                  <label className="inline-flex items-center">
                    <input
                      type="radio"
                      name="isPcd"
                      checked={formData.isPcd === true}
                      onChange={() => handleChange("isPcd", true)}
                      className="w-4 h-4 text-[#1351B4] focus:ring-[#1351B4]"
                    />
                    <span className="ml-2 text-sm text-gray-700">Sim</span>
                  </label>
                </div>

                {formData.isPcd && (
                  <div className="mt-3 animate-fadeIn">
                    <Input
                      label="Qual o tipo de deficiência?"
                      id="disabilityType"
                      name="disabilityType"
                      placeholder="Ex.: Visual, Auditiva, Motora, Intelectual, etc."
                      value={formData.disabilityType}
                      onChange={(e) => handleChange("disabilityType", e.target.value)}
                      error={errors.disabilityType}
                      required
                      helperText="Utilizado para garantir atendimento preferencial e acessibilidade"
                    />
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Seção 2: Contato */}
          <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
            <div className="flex items-center gap-3 pb-4 mb-6 border-b border-gray-100">
              <div className="w-10 h-10 rounded-lg bg-green-50 text-green-700 flex items-center justify-center">
                <Mail className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-gray-900">2. Contato</h2>
                <p className="text-xs text-gray-500">Para envio de protocolos e avisos de agendamento</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Input
                  label="E-mail"
                  id="email"
                  name="email"
                  type="email"
                  placeholder="exemplo@email.com"
                  value={formData.email}
                  onChange={(e) => handleChange("email", e.target.value)}
                  error={errors.email}
                  required
                />
              </div>

              <div>
                <Input
                  label="Confirme o e-mail"
                  id="confirmEmail"
                  name="confirmEmail"
                  type="email"
                  placeholder="Repita o seu e-mail"
                  value={formData.confirmEmail}
                  onChange={(e) => handleChange("confirmEmail", e.target.value)}
                  error={errors.confirmEmail}
                  required
                />
              </div>

              <div>
                <Input
                  label="Telefone celular"
                  id="mobilePhone"
                  name="mobilePhone"
                  placeholder="(00) 90000-0000"
                  value={formData.mobilePhone}
                  onChange={(e) => handleChange("mobilePhone", maskPhone(e.target.value))}
                  error={errors.mobilePhone}
                  required
                />
              </div>

              <div>
                <Input
                  label="Telefone fixo (opcional)"
                  id="landlinePhone"
                  name="landlinePhone"
                  placeholder="(00) 0000-0000"
                  value={formData.landlinePhone}
                  onChange={(e) => handleChange("landlinePhone", maskPhone(e.target.value))}
                />
              </div>
            </div>
          </div>

          {/* Seção 3: Endereço Residencial com ViaCEP */}
          <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
            <div className="flex items-center gap-3 pb-4 mb-6 border-b border-gray-100">
              <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center">
                <MapPin className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-gray-900">3. Endereço Residencial</h2>
                <p className="text-xs text-gray-500">
                  Preenchimento automático via CEP com suporte a edição manual
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="sm:col-span-1">
                <Input
                  label="CEP"
                  id="cep"
                  name="cep"
                  placeholder="00000-000"
                  value={formData.cep}
                  onChange={(e) => handleChange("cep", maskCEP(e.target.value))}
                  onBlur={handleCepBlur}
                  error={errors.cep}
                  required
                  helperText={isSearchingCep ? "Buscando endereço no ViaCEP..." : "Digite o CEP para autopreencher"}
                />
              </div>

              <div className="sm:col-span-2">
                <Input
                  label="Logradouro"
                  id="street"
                  name="street"
                  placeholder="Rua, Avenida, Praça..."
                  value={formData.street}
                  onChange={(e) => handleChange("street", e.target.value)}
                  error={errors.street}
                  required
                />
              </div>

              <div>
                <Input
                  label="Número"
                  id="number"
                  name="number"
                  placeholder="Ex: 123 ou S/N"
                  value={formData.number}
                  onChange={(e) => handleChange("number", e.target.value)}
                  error={errors.number}
                  required
                />
              </div>

              <div className="sm:col-span-2">
                <Input
                  label="Complemento (opcional)"
                  id="complement"
                  name="complement"
                  placeholder="Apto, Bloco, Casa 2..."
                  value={formData.complement}
                  onChange={(e) => handleChange("complement", e.target.value)}
                />
              </div>

              <div>
                <Input
                  label="Bairro"
                  id="neighborhood"
                  name="neighborhood"
                  placeholder="Bairro"
                  value={formData.neighborhood}
                  onChange={(e) => handleChange("neighborhood", e.target.value)}
                  error={errors.neighborhood}
                  required
                />
              </div>

              <div>
                <Input
                  label="Município"
                  id="city"
                  name="city"
                  placeholder="Cidade"
                  value={formData.city}
                  onChange={(e) => handleChange("city", e.target.value)}
                  error={errors.city}
                  required
                />
              </div>

              <div>
                <Input
                  label="Estado (UF)"
                  id="state"
                  name="state"
                  placeholder="AL, SP, RJ..."
                  maxLength={2}
                  value={formData.state}
                  onChange={(e) => handleChange("state", e.target.value.toUpperCase())}
                  error={errors.state}
                  required
                />
              </div>
            </div>
          </div>

          {/* Seção 4: Segurança da Senha */}
          <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-200">
            <div className="flex items-center gap-3 pb-4 mb-6 border-b border-gray-100">
              <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-700 flex items-center justify-center">
                <Lock className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-gray-900">4. Senha de Acesso</h2>
                <p className="text-xs text-gray-500">Crie uma senha forte para proteção da sua conta</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-semibold text-gray-700 mb-1.5"
                >
                  Senha de acesso <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    value={formData.password}
                    onChange={(e) => handleChange("password", e.target.value)}
                    placeholder="Mínimo 8 caracteres"
                    className="w-full px-4 py-3 pr-11 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#1351B4] transition-all min-h-[44px]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-1 rounded-md"
                    aria-label={showPassword ? "Ocultar senha" : "Exibir senha"}
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                {errors.password && (
                  <p className="mt-1 text-xs text-red-600">{errors.password}</p>
                )}

                {/* Barra de força da senha com badge textual */}
                {formData.password && (
                  <div className="mt-3" aria-live="polite">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-gray-700">Força da senha:</span>
                      <span
                        className={`text-xs font-bold px-2 py-0.5 rounded ${
                          passStrength.score <= 1
                            ? "bg-red-100 text-red-700"
                            : passStrength.score === 2
                            ? "bg-amber-100 text-amber-700"
                            : passStrength.score === 3
                            ? "bg-blue-100 text-[#1351B4]"
                            : "bg-green-100 text-green-700"
                        }`}
                      >
                        {passStrength.score <= 1
                          ? "Fraca"
                          : passStrength.score === 2
                          ? "Razoável"
                          : passStrength.score === 3
                          ? "Boa"
                          : "Forte"}
                      </span>
                    </div>
                    <div className="flex gap-1 h-2 mb-2">
                      {[1, 2, 3, 4].map((step) => (
                        <div
                          key={step}
                          className={`flex-1 rounded-full transition-all duration-300 ${
                            passStrength.score >= step
                              ? passStrength.score <= 1
                                ? "bg-red-500"
                                : passStrength.score === 2
                                ? "bg-amber-500"
                                : passStrength.score === 3
                                ? "bg-blue-500"
                                : "bg-green-500"
                              : "bg-gray-200"
                          }`}
                        />
                      ))}
                    </div>

                    {/* Checklist dinâmico dos 5 critérios */}
                    <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-100 space-y-1.5 text-xs">
                      <p className="font-semibold text-gray-700 mb-1">Critérios de segurança:</p>
                      {passwordCriteria.map((c, i) => (
                        <div key={i} className="flex items-center gap-2">
                          {c.met ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-green-600 flex-shrink-0" />
                          ) : (
                            <div className="w-3.5 h-3.5 rounded-full border border-gray-300 flex-shrink-0" />
                          )}
                          <span className={c.met ? "text-green-700 font-medium" : "text-gray-500"}>
                            {c.label}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div>
                <label
                  htmlFor="confirmPassword"
                  className="block text-sm font-semibold text-gray-700 mb-1.5"
                >
                  Confirme a senha <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    value={formData.confirmPassword}
                    onChange={(e) => handleChange("confirmPassword", e.target.value)}
                    placeholder="Repita a mesma senha"
                    className="w-full px-4 py-3 pr-11 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#1351B4] transition-all min-h-[44px]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-1 rounded-md"
                    aria-label={showConfirmPassword ? "Ocultar senha" : "Exibir senha"}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
                {formData.confirmPassword && (
                  <div className="mt-2 text-xs flex items-center gap-1.5" aria-live="polite">
                    {formData.password === formData.confirmPassword ? (
                      <span className="text-green-600 font-medium flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> As senhas conferem
                      </span>
                    ) : (
                      <span className="text-amber-600 font-medium flex items-center gap-1">
                        <AlertCircle className="w-3.5 h-3.5" /> As senhas ainda não coincidem
                      </span>
                    )}
                  </div>
                )}
                {errors.confirmPassword && (
                  <p className="mt-1 text-xs text-red-600">{errors.confirmPassword}</p>
                )}
              </div>
            </div>

            {/* Aceite dos Termos de Uso (RF-01) */}
            <div className="mt-6 pt-6 border-t border-gray-100">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.acceptTerms}
                  onChange={(e) => handleChange("acceptTerms", e.target.checked)}
                  className="mt-1 w-5 h-5 text-[#1351B4] border-gray-300 rounded focus:ring-[#1351B4]"
                />
                <span className="text-sm text-gray-700 leading-snug">
                  Li e concordo com os{" "}
                  <Link href="/termos" target="_blank" className="text-[#1351B4] font-semibold underline hover:text-[#0F2942]">
                    Termos de Uso
                  </Link>{" "}
                  e a{" "}
                  <Link href="/privacidade" target="_blank" className="text-[#1351B4] font-semibold underline hover:text-[#0F2942]">
                    Política de Privacidade
                  </Link>{" "}
                  do SOSP, em conformidade com a Lei Geral de Proteção de Dados (LGPD).
                </span>
              </label>
              {errors.acceptTerms && (
                <p className="mt-2 text-xs text-red-600">{errors.acceptTerms}</p>
              )}
            </div>
          </div>

          {/* Botões de Ação do Formulário */}
          <div className="flex flex-col-reverse sm:flex-row justify-end gap-4 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsCancelModalOpen(true)}
              className="w-full sm:w-auto"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={isSubmitting}
              className="w-full sm:w-auto px-8"
            >
              Cadastrar
            </Button>
          </div>
        </form>
      </div>

      {/* Modal de Cancelamento com Mensagem Literal MSG-06 */}
      <CriticalConfirmationModal
        isOpen={isCancelModalOpen}
        onClose={() => setIsCancelModalOpen(false)}
        onConfirm={() => router.push("/login")}
        title="Cancelar Cadastro"
        description="Todas as alterações serão perdidas. Deseja realmente cancelar?"
        confirmText="Sim, cancelar"
        cancelText="Não, continuar"
        isDestructive={true}
      />
    </div>
  );
}

