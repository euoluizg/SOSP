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

export default function RegisterPage() {
  const router = useRouter();

  // Estados dos 19 campos
  const [formData, setFormData] = useState({
    fullName: "",
    cpf: "",
    birthDate: "",
    gender: "",
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) {
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }

    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      setSubmitSuccess(true);
    }, 1200);
  };

  const passStrength = validatePasswordStrength(formData.password);

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

                {/* Barra de força da senha */}
                {formData.password && (
                  <div className="mt-3">
                    <div className="flex gap-1 h-1.5 mb-1">
                      {[1, 2, 3, 4].map((step) => (
                        <div
                          key={step}
                          className={`flex-1 rounded-full ${
                            passStrength.score >= step
                              ? passStrength.score <= 2
                                ? "bg-red-500"
                                : passStrength.score === 3
                                ? "bg-amber-500"
                                : "bg-green-500"
                              : "bg-gray-200"
                          }`}
                        />
                      ))}
                    </div>
                    <span className="text-xs text-gray-500">
                      {passStrength.score <= 2
                        ? "Senha fraca"
                        : passStrength.score === 3
                        ? "Senha média"
                        : "Senha forte e segura"}
                    </span>
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
                  <a href="#" className="text-[#1351B4] font-semibold underline">
                    Termos de Uso
                  </a>{" "}
                  e a{" "}
                  <a href="#" className="text-[#1351B4] font-semibold underline">
                    Política de Privacidade
                  </a>{" "}
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

