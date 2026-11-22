import {
  Agency,
  Appointment,
  AppointmentSlot,
  AppointmentsReportSummary,
  AuditLogEntry,
  CitizenProfile,
  InternalUserAccount,
  LoginResponse,
  ProblemDetails,
  Protocol,
  Service,
  Unit,
  UserSession,
} from "@/types/api";
import { MOCK_AGENCIES, MOCK_SERVICES, MOCK_UNITS } from "@/mocks/demoData";
import {
  AUTH_TOKEN_KEY,
  clearAuthSessionStorage,
  getStoredUserSession,
  isInstitutionalPath,
  isInstitutionalRole,
} from "@/utils/session";

const USE_MOCK = process.env.NEXT_PUBLIC_API_MOCK !== "false";
export const IS_API_MOCK_MODE = USE_MOCK;
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

// Mock em memória para agendamentos do cidadão — Inicia estritamente vazio (Seção 8: Zero agendamentos fictícios)
let MOCK_APPOINTMENTS: Appointment[] = [];

export class ApiClient {
  private static async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${BASE_URL}${endpoint}`;
    let authToken = "";
    if (typeof window !== "undefined") {
      authToken = localStorage.getItem(AUTH_TOKEN_KEY) || "";
    }
    const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
    const headers: Record<string, string> = {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      Accept: "application/json",
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      ...(options.headers as Record<string, string>),
    };

    try {
      const res = await fetch(url, { ...options, headers });
      if (!res.ok) {
        if (res.status === 401 && typeof window !== "undefined") {
          const storedUser = getStoredUserSession();
          const wasInstitutional =
            isInstitutionalRole(storedUser?.role) ||
            isInstitutionalPath(window.location.pathname);

          clearAuthSessionStorage();

          if (!window.location.pathname.includes("/login")) {
            window.location.href = wasInstitutional
              ? "/sessao-expirada?tipo=institucional"
              : "/sessao-expirada";
          }
        }
        let problem: ProblemDetails;
        try {
          problem = await res.json();
        } catch {
          problem = {
            type: "about:blank",
            title: "Erro de Servidor",
            status: res.status,
            detail: "Ocorreu um erro inesperado no processamento da solicitação.",
          };
        }
        throw problem;
      }
      return (await res.json()) as T;
    } catch (err) {
      if ((err as ProblemDetails).status) {
        throw err;
      }
      throw {
        type: "about:blank",
        title: "Sem conexão",
        status: 0,
        detail: "Não foi possível conectar ao servidor. Verifique sua conexão.",
      } as ProblemDetails;
    }
  }

  /* --- Catálogo e Serviços --- */
  static async getServices(params?: {
    query?: string;
    category?: string;
    channel?: string;
    city?: string;
    agencyId?: string;
    page?: number;
    pageSize?: number;
  }): Promise<{
    items: Service[];
    total: number;
    page: number;
    pageSize: number;
    totalPages: number;
  }> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 80));
      let filtered = [...MOCK_SERVICES];

      if (params?.query) {
        const q = params.query.toLowerCase().trim();
        filtered = filtered.filter(
          (s) =>
            s.name.toLowerCase().includes(q) ||
            s.summary.toLowerCase().includes(q) ||
            s.description.toLowerCase().includes(q) ||
            s.agencyAcronym.toLowerCase().includes(q) ||
            (q === "tirar rg" && s.id === "servico-emitir-rg")
        );
      }

      if (params?.category && params.category !== "Todos") {
        filtered = filtered.filter((s) => s.category === params.category);
      }

      if (params?.agencyId) {
        filtered = filtered.filter((s) => s.agencyId === params.agencyId);
      }

      if (params?.channel && params.channel !== "Todos") {
        filtered = filtered.filter((s) => s.channel === params.channel);
      }

      const total = filtered.length;
      const pageSize = params?.pageSize || 10;
      const page = params?.page || 1;
      const start = (page - 1) * pageSize;
      const items = filtered.slice(start, start + pageSize);

      return {
        items,
        total,
        page,
        pageSize,
        totalPages: Math.max(1, Math.ceil(total / pageSize)),
      };
    }

    const search = new URLSearchParams();
    if (params?.query) search.set("query", params.query);
    if (params?.category && params.category !== "Todos") search.set("category", params.category);
    if (params?.channel && params.channel !== "Todos") search.set("channel", params.channel);
    if (params?.city) search.set("city", params.city);
    if (params?.agencyId) search.set("agencyId", params.agencyId);
    if (params?.page) search.set("page", String(params.page));
    if (params?.pageSize) search.set("pageSize", String(params.pageSize));
    const qs = search.toString();
    return this.request(`/services${qs ? `?${qs}` : ""}`);
  }

  static async createService(data: {
    name: string;
    category: string;
    channel: string;
    agencyId: string;
    description: string;
    whoCanUse?: string;
    isFree?: boolean;
    costAmount?: number | null;
    averageDeadlineDays?: number;
  }): Promise<Service> {
    if (USE_MOCK) {
      const created: Service = {
        id: `svc-${Date.now()}`,
        name: data.name,
        category: (data.category as Service["category"]) || "Documentos",
        channel: (data.channel as Service["channel"]) || "inPerson",
        agencyId: data.agencyId,
        agencyAcronym: "SOSP",
        agencyName: "Governo de Alagoas",
        isFree: data.isFree ?? true,
        costAmount: data.costAmount ?? null,
        averageDeadlineDays: data.averageDeadlineDays ?? 5,
        summary: data.description.slice(0, 160),
        description: data.description,
        whoCanUse: data.whoCanUse || "Cidadãos residentes em Alagoas.",
        updatedAt: new Date().toISOString(),
        unitCount: 1,
        documents: [],
        steps: [],
      };
      MOCK_SERVICES.unshift(created);
      return created;
    }
    return this.request("/services", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  static async deactivateService(id: string): Promise<Service> {
    if (USE_MOCK) {
      const found = MOCK_SERVICES.find((s) => s.id === id) || MOCK_SERVICES[0];
      return found;
    }
    return this.request(`/services/${id}`, { method: "DELETE" });
  }

  static async getServiceById(id: string): Promise<Service | null> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 60));
      return MOCK_SERVICES.find((s) => s.id === id) || null;
    }
    return this.request(`/services/${id}`);
  }

  /* --- Órgãos e Unidades --- */
  static async getAgencies(): Promise<Agency[]> {
    if (USE_MOCK) return MOCK_AGENCIES;
    return this.request("/agencies");
  }

  static async createAgency(data: {
    name: string;
    acronym: string;
    sphere: Agency["sphere"];
    description?: string;
  }): Promise<Agency> {
    if (USE_MOCK) {
      const created: Agency = {
        id: `agency-${Date.now()}`,
        name: data.name,
        acronym: data.acronym.toUpperCase(),
        sphere: data.sphere,
        description: data.description || "",
        isActive: true,
      };
      MOCK_AGENCIES.unshift(created);
      return created;
    }
    return this.request("/agencies", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  static async deactivateAgency(id: string): Promise<Agency> {
    if (USE_MOCK) {
      const idx = MOCK_AGENCIES.findIndex((a) => a.id === id);
      if (idx !== -1) {
        MOCK_AGENCIES[idx] = { ...MOCK_AGENCIES[idx], isActive: false };
        return MOCK_AGENCIES[idx];
      }
      return { id, name: "", acronym: "", sphere: "state", isActive: false };
    }
    return this.request(`/agencies/${id}`, { method: "DELETE" });
  }

  static async updateAgency(id: string, data: Partial<Agency>): Promise<Agency> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 150));
      const idx = MOCK_AGENCIES.findIndex((a) => a.id === id);
      if (idx === -1) {
        throw {
          type: "about:blank",
          title: "Órgão não encontrado",
          status: 404,
          detail: `Órgão com ID '${id}' não encontrado.`,
        } as ProblemDetails;
      }
      MOCK_AGENCIES[idx] = { ...MOCK_AGENCIES[idx], ...data };
      return MOCK_AGENCIES[idx];
    }
    return this.request(`/agencies/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  static async getUnits(agencyId?: string): Promise<Unit[]> {
    if (USE_MOCK) {
      if (agencyId) return MOCK_UNITS.filter((u) => u.agencyId === agencyId);
      return MOCK_UNITS;
    }
    return this.request(`/units${agencyId ? `?agencyId=${agencyId}` : ""}`);
  }

  static async createUnit(data: {
    agencyId: string;
    name: string;
    cep?: string;
    street: string;
    number?: string;
    neighborhood?: string;
    city: string;
    state: string;
    openingHours?: string;
    dailyLimit: number;
    isPcdAccessible: boolean;
    hasPriorityService?: boolean;
  }): Promise<Unit> {
    if (USE_MOCK) {
      const created: Unit = {
        id: `unit-${Date.now()}`,
        agencyId: data.agencyId,
        name: data.name,
        cep: data.cep || "57020-100",
        street: data.street,
        number: data.number || "S/N",
        neighborhood: data.neighborhood || "Centro",
        city: data.city,
        state: data.state,
        openingHours: data.openingHours || "08:00 às 17:00",
        dailyLimit: data.dailyLimit,
        isPcdAccessible: data.isPcdAccessible,
        hasPriorityService: data.hasPriorityService ?? true,
        isActive: true,
      };
      MOCK_UNITS.unshift(created);
      return created;
    }
    return this.request("/units", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  static async deactivateUnit(id: string): Promise<Unit> {
    if (USE_MOCK) {
      const idx = MOCK_UNITS.findIndex((u) => u.id === id);
      if (idx !== -1) {
        MOCK_UNITS[idx] = { ...MOCK_UNITS[idx], isActive: false };
        return MOCK_UNITS[idx];
      }
      return MOCK_UNITS[0];
    }
    return this.request(`/units/${id}`, { method: "DELETE" });
  }

  /* --- Agendamento e Slots (Slots de 30 min — RN-18) --- */
  static async getSlots(unitId: string, date: string): Promise<AppointmentSlot[]> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 80));
      const slots: AppointmentSlot[] = [
        { slotDate: date, startsAt: "08:00", endsAt: "08:30", capacity: 4, bookedCount: 2, isAvailable: true },
        { slotDate: date, startsAt: "08:30", endsAt: "09:00", capacity: 4, bookedCount: 1, isAvailable: true },
        { slotDate: date, startsAt: "09:00", endsAt: "09:30", capacity: 4, bookedCount: 4, isAvailable: false },
        { slotDate: date, startsAt: "09:30", endsAt: "10:00", capacity: 4, bookedCount: 3, isAvailable: true },
        { slotDate: date, startsAt: "10:00", endsAt: "10:30", capacity: 4, bookedCount: 0, isAvailable: true },
        { slotDate: date, startsAt: "10:30", endsAt: "11:00", capacity: 4, bookedCount: 1, isAvailable: true },
        { slotDate: date, startsAt: "11:00", endsAt: "11:30", capacity: 4, bookedCount: 2, isAvailable: true },
        { slotDate: date, startsAt: "13:30", endsAt: "14:00", capacity: 4, bookedCount: 1, isAvailable: true },
        { slotDate: date, startsAt: "14:00", endsAt: "14:30", capacity: 4, bookedCount: 2, isAvailable: true },
        { slotDate: date, startsAt: "14:30", endsAt: "15:00", capacity: 4, bookedCount: 0, isAvailable: true },
        { slotDate: date, startsAt: "15:00", endsAt: "15:30", capacity: 4, bookedCount: 1, isAvailable: true },
        { slotDate: date, startsAt: "15:30", endsAt: "16:00", capacity: 4, bookedCount: 4, isAvailable: false },
        { slotDate: date, startsAt: "16:00", endsAt: "16:30", capacity: 4, bookedCount: 2, isAvailable: true },
        { slotDate: date, startsAt: "16:30", endsAt: "17:00", capacity: 4, bookedCount: 1, isAvailable: true },
      ];
      return slots;
    }
    return this.request(`/units/${unitId}/slots?date=${date}`);
  }

  static async createAppointment(data: {
    serviceId: string;
    unitId: string;
    scheduledDate: string;
    scheduledTime: string;
  }): Promise<Appointment> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 200));
      const today = new Date().toISOString().slice(0, 10).replace(/-/g, "");
      const randomSeq = String(Math.floor(Math.random() * 9000) + 1000);
      const protocolNumber = `${today}-${randomSeq}`;

      const service = MOCK_SERVICES.find((s) => s.id === data.serviceId);
      const unit = MOCK_UNITS.find((u) => u.id === data.unitId);

      const newAppt: Appointment = {
        id: `appt-${Date.now()}`,
        protocolNumber,
        citizenId: "citizen-001",
        citizenName: "Cidadão de Testes",
        citizenCpfMasked: "***.456.789-**",
        serviceId: data.serviceId,
        serviceName: service?.name || "Serviço Público",
        agencyName: service?.agencyName || "Governo de Alagoas",
        unitId: data.unitId,
        unitName: unit?.name || "Unidade Central",
        unitAddress: unit ? `${unit.street}, ${unit.number} - ${unit.neighborhood}` : "Maceió - AL",
        scheduledDate: data.scheduledDate,
        scheduledTime: data.scheduledTime,
        status: "scheduled",
        createdAt: new Date().toISOString(),
      };

      MOCK_APPOINTMENTS.unshift(newAppt);
      return newAppt;
    }
    const idempotencyKey =
      typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
        ? crypto.randomUUID()
        : `idemp-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;

    return this.request("/appointments", {
      method: "POST",
      headers: {
        "Idempotency-Key": idempotencyKey,
      },
      body: JSON.stringify(data),
    });
  }

  /* --- Agendamentos do Cidadão --- */
  static async getCitizenAppointments(citizenId?: string): Promise<Appointment[]> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 100));
      if (!citizenId) return [...MOCK_APPOINTMENTS];
      return MOCK_APPOINTMENTS.filter((a) => a.citizenId === citizenId);
    }
    return this.request(`/citizens/${citizenId}/appointments`);
  }

  static async getAppointmentByProtocol(protocolNumber: string): Promise<Appointment | null> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 80));
      return MOCK_APPOINTMENTS.find((a) => a.protocolNumber === protocolNumber) || null;
    }
    return this.request(`/appointments/by-protocol/${protocolNumber}`);
  }

  static async cancelAppointment(appointmentId: string, reason?: string): Promise<void> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 150));
      const target = MOCK_APPOINTMENTS.find((a) => a.id === appointmentId);
      if (target) {
        target.status = "cancelled";
      }
      return;
    }
    return this.request(`/appointments/${appointmentId}/cancel`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
  }

  /* --- Autenticação e Cidadão (RF-01, RF-02, RN-28..30) --- */
  static async registerCitizen(data: Record<string, unknown>): Promise<Record<string, unknown>> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 300));
      return { id: "citizen-new", ...data };
    }
    return this.request("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  static async login(cpf: string, password: string): Promise<LoginResponse> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 300));
      if (password === "erro") {
        throw {
          type: "https://sosp.al.gov.br/errors/401",
          title: "Credenciais Inválidas",
          status: 401,
          detail: "CPF ou senha inválidos.",
        } as ProblemDetails;
      }

      // Suporte a servidor institucional com Matrícula (ex: 202XXXXX, SSP-1001) ou CPF
      const cleanUpper = cpf.toUpperCase().trim();
      if (
        cleanUpper.startsWith("202") ||
        cleanUpper.startsWith("SSP") ||
        cpf.replace(/\D/g, "") === "33366699957"
      ) {
        return {
          token: "simulated-jwt-token-server-001",
          tokenType: "Bearer",
          expiresIn: 1800,
          citizen: {
            id: "server-001",
            fullName: "João Servidor Central",
            cpf: "33366699957",
            registrationNumber: cleanUpper.startsWith("202") || cleanUpper.startsWith("SSP") ? cleanUpper : "SSP-1001",
            email: "joao.servidor@ssp.al.gov.br",
            role: "server",
            agencyId: "agency-ssp",
            unitId: "unit-centro",
            mustChangePassword: false,
          },
        };
      }

      return {
        token: "simulated-jwt-token-citizen-001",
        tokenType: "Bearer",
        expiresIn: 1800,
        citizen: {
          id: "citizen-001",
          fullName: "Cidadão de Testes",
          cpf: cpf.replace(/\D/g, ""),
          email: "cidadao@exemplo.com.br",
          role: "citizen",
          mustChangePassword: false,
        },
      };
    }
    const res = await this.request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ cpf, password }),
    });
    if (typeof window !== "undefined" && res.token) {
      localStorage.setItem("sosp_auth_token", res.token);
    }
    return res;
  }

  static async changePassword(
    currentPassword: string,
    newPassword: string,
    confirmPassword?: string
  ): Promise<{ message: string; token?: string; mustChangePassword?: boolean }> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 200));
      return { message: "Senha alterada com sucesso.", mustChangePassword: false };
    }
    const res = await this.request<{ message: string; token?: string; mustChangePassword?: boolean }>("/auth/change-password", {
      method: "POST",
      body: JSON.stringify({ currentPassword, newPassword, confirmPassword }),
    });
    if (typeof window !== "undefined" && res.token) {
      localStorage.setItem("sosp_auth_token", res.token);
    }
    return res;
  }

  static async recoverPassword(cpf: string): Promise<{ message: string; codeSimulated?: string }> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 200));
      const dynamicCode = String(Math.floor(100000 + Math.random() * 900000));
      return { message: "Código enviado para o e-mail cadastrado.", codeSimulated: dynamicCode };
    }
    return this.request("/auth/recover-password", {
      method: "POST",
      body: JSON.stringify({ cpf }),
    });
  }

  static async resetPassword(cpf: string, code: string, newPassword: string): Promise<{ message: string }> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 200));
      return { message: "Senha redefinida com sucesso." };
    }
    return this.request("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ cpf, code, newPassword }),
    });
  }

  static async getCitizenMe(): Promise<CitizenProfile> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 100));
      return {
        id: "citizen-001",
        cpf: "11144477705",
        fullName: "Cidadão de Testes",
        birthDate: "1990-05-15",
        email: "cidadao@exemplo.com.br",
        phone: "(82) 99988-7766",
        gender: "Não informado",
        isPcd: false,
        motherName: "Maria de Testes",
        cep: "57020-100",
        street: "Rua do Comércio",
        number: "123",
        neighborhood: "Centro",
        city: "Maceió",
        state: "AL",
      };
    }
    return this.request("/citizens/me");
  }

  /* --- Feedback, FAQ e Perguntas (RF-11) --- */
  static async getFaqs(): Promise<Array<{ id: string; category: string; question: string; answer: string }>> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 100));
      return [
        {
          id: "faq-01",
          category: "Geral",
          question: "Como agendar um atendimento no SOSP?",
          answer: "Basta acessar o portal, buscar o serviço desejado, escolher a unidade de atendimento, a data e o horário disponível em slots de 30 minutos.",
        },
        {
          id: "faq-02",
          category: "Gov.br",
          question: "Por que o botão Entrar com Gov.br abre uma mensagem de atualização?",
          answer: "A integração oficial federada com a conta Gov.br está planejada para a versão 2.0 do SOSP.",
        },
      ];
    }
    return this.request("/feedback/faq");
  }

  static async openQuestion(data: {
    citizenName: string;
    email: string;
    category: string;
    subject: string;
    description: string;
  }): Promise<{ id: string; protocolNumber: string; status: string }> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 200));
      const today = new Date().toISOString().slice(0, 10).replace(/-/g, "");
      return {
        id: `qst-${Date.now()}`,
        protocolNumber: `${today}-9999`,
        status: "open",
      };
    }
    return this.request("/questions", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /* --- Fila Operacional do Servidor, Anexos, Guia, Usuários Internos, Auditoria e Relatórios --- */
  static async getOperationalAppointments(params?: { status?: string; date?: string }): Promise<Appointment[]> {
    if (USE_MOCK) {
      return [...MOCK_APPOINTMENTS];
    }
    const search = new URLSearchParams();
    if (params?.status && params.status !== "all") search.set("status", params.status);
    if (params?.date) search.set("date", params.date);
    const qs = search.toString();
    return this.request(`/appointments/queue${qs ? `?${qs}` : ""}`);
  }

  static async updateAppointmentStatus(
    appointmentId: string,
    status: "scheduled" | "confirmed" | "in_progress" | "completed" | "no_show" | "cancelled",
    note?: string
  ): Promise<Appointment> {
    if (USE_MOCK) {
      const target = MOCK_APPOINTMENTS.find((a) => a.id === appointmentId);
      if (target) {
        target.status = status === "in_progress" ? "confirmed" : status;
        return { ...target };
      }
      throw { type: "about:blank", title: "Não encontrado", status: 404, detail: "Agendamento não encontrado." } as ProblemDetails;
    }
    return this.request(`/appointments/${appointmentId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, note: note || "" }),
    });
  }

  static async uploadProtocolAttachment(
    protocolNumber: string,
    file: File
  ): Promise<{ id: string; protocolNumber: string; fileName: string; fileSize: number; uploadedAt: string }> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 200));
      return {
        id: `doc-${Date.now()}`,
        protocolNumber,
        fileName: file.name,
        fileSize: file.size,
        uploadedAt: new Date().toISOString(),
      };
    }
    const formData = new FormData();
    formData.append("file", file);
    return this.request(`/protocols/${protocolNumber}/documents`, {
      method: "POST",
      body: formData,
    });
  }

  static async getServiceGuidance(serviceId: string): Promise<{ checkedItems: string[]; totalRequired?: number }> {
    if (USE_MOCK) {
      return { checkedItems: [] };
    }
    return this.request(`/guidance/services/${serviceId}`);
  }

  static async saveServiceChecklist(serviceId: string, checkedItems: string[]): Promise<{ checkedItems: string[] }> {
    if (USE_MOCK) {
      return { checkedItems };
    }
    return this.request(`/guidance/services/${serviceId}`, {
      method: "PUT",
      body: JSON.stringify({ checkedItems }),
    });
  }

  static async getInternalUsers(): Promise<InternalUserAccount[]> {
    if (USE_MOCK) {
      return [];
    }
    return this.request("/internal-users");
  }

  static async createInternalUser(data: {
    fullName: string;
    cpf: string;
    email: string;
    registrationNumber: string;
    role: string;
    agencyId?: string | null;
    unitId?: string | null;
    canManageCatalog: boolean;
    temporaryPassword?: string;
  }): Promise<InternalUserAccount> {
    if (USE_MOCK) {
      return {
        id: `user-${Date.now()}`,
        fullName: data.fullName,
        email: data.email,
        cpfMasked: "***.***.***-**",
        registrationNumber: data.registrationNumber,
        agencyId: data.agencyId || null,
        unitId: data.unitId || null,
        role: data.role,
        canManageCatalog: data.canManageCatalog,
        mustChangePassword: true,
        isActive: true,
      };
    }
    return this.request("/internal-users", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  static async deactivateInternalUser(userId: string): Promise<InternalUserAccount> {
    if (USE_MOCK) {
      return {
        id: userId,
        fullName: "",
        email: "",
        cpfMasked: "***.***.***-**",
        registrationNumber: "",
        role: "server",
        canManageCatalog: false,
        isActive: false,
      };
    }
    return this.request(`/internal-users/${userId}`, { method: "DELETE" });
  }

  static async getAuditEvents(): Promise<AuditLogEntry[]> {
    if (USE_MOCK) {
      return [];
    }
    return this.request("/audit");
  }

  static async getAppointmentsReport(params?: {
    startDate?: string;
    endDate?: string;
    agencyId?: string;
    unitId?: string;
  }): Promise<AppointmentsReportSummary> {
    if (USE_MOCK) {
      return {
        period: { start: params?.startDate || "2026-11-01", end: params?.endDate || "2026-11-30" },
        scope: { agencyId: params?.agencyId || null, unitId: params?.unitId || null },
        metrics: {
          totalAppointments: MOCK_APPOINTMENTS.length,
          scheduled: MOCK_APPOINTMENTS.filter((a) => a.status === "scheduled").length,
          inProgress: MOCK_APPOINTMENTS.filter((a) => a.status === "confirmed").length,
          completed: MOCK_APPOINTMENTS.filter((a) => a.status === "completed").length,
          cancelled: MOCK_APPOINTMENTS.filter((a) => a.status === "cancelled").length,
          noShow: MOCK_APPOINTMENTS.filter((a) => a.status === "no_show").length,
          attendanceRate: 0,
        },
        byService: [],
        recentQueue: MOCK_APPOINTMENTS,
      };
    }
    const search = new URLSearchParams();
    if (params?.startDate) search.set("startDate", params.startDate);
    if (params?.endDate) search.set("endDate", params.endDate);
    if (params?.agencyId) search.set("agencyId", params.agencyId);
    if (params?.unitId) search.set("unitId", params.unitId);
    const qs = search.toString();
    return this.request(`/reports/appointments${qs ? `?${qs}` : ""}`);
  }

  static async createReportExport(
    type: "csv" | "pdf",
    filters?: Record<string, unknown>
  ): Promise<{ exportId: string; status: string; downloadUrl: string }> {
    if (USE_MOCK) {
      return { exportId: `exp-${Date.now()}`, status: "done", downloadUrl: "" };
    }
    return this.request("/reports/exports", {
      method: "POST",
      body: JSON.stringify({ type, filters: filters || {} }),
    });
  }

  static logout(): void {
    if (typeof window !== "undefined") {
      clearAuthSessionStorage();
      sessionStorage.clear();
      if (!window.location.pathname.includes("/login")) {
        window.location.href = "/login";
      }
    }
  }

  static getAuthToken(): string | null {
    if (typeof window !== "undefined") {
      return localStorage.getItem(AUTH_TOKEN_KEY);
    }
    return null;
  }

  static isAuthenticated(): boolean {
    return !!this.getAuthToken();
  }
}

// Named exports for ease of consumption
export const getServices = ApiClient.getServices.bind(ApiClient);
export const createService = ApiClient.createService.bind(ApiClient);
export const deactivateService = ApiClient.deactivateService.bind(ApiClient);
export const getServiceById = ApiClient.getServiceById.bind(ApiClient);
export const getAgencies = ApiClient.getAgencies.bind(ApiClient);
export const createAgency = ApiClient.createAgency.bind(ApiClient);
export const updateAgency = ApiClient.updateAgency.bind(ApiClient);
export const deactivateAgency = ApiClient.deactivateAgency.bind(ApiClient);
export const getUnits = ApiClient.getUnits.bind(ApiClient);
export const createUnit = ApiClient.createUnit.bind(ApiClient);
export const deactivateUnit = ApiClient.deactivateUnit.bind(ApiClient);
export const getAppointmentSlots = ApiClient.getSlots.bind(ApiClient);
export const createAppointment = ApiClient.createAppointment.bind(ApiClient);
export const getCitizenAppointments = ApiClient.getCitizenAppointments.bind(ApiClient);
export const getOperationalAppointments = ApiClient.getOperationalAppointments.bind(ApiClient);
export const updateAppointmentStatus = ApiClient.updateAppointmentStatus.bind(ApiClient);
export const getAppointmentByProtocol = ApiClient.getAppointmentByProtocol.bind(ApiClient);
export const cancelAppointment = ApiClient.cancelAppointment.bind(ApiClient);
export const uploadProtocolAttachment = ApiClient.uploadProtocolAttachment.bind(ApiClient);
export const getServiceGuidance = ApiClient.getServiceGuidance.bind(ApiClient);
export const saveServiceChecklist = ApiClient.saveServiceChecklist.bind(ApiClient);
export const registerCitizen = ApiClient.registerCitizen.bind(ApiClient);
export const loginCitizen = ApiClient.login.bind(ApiClient);
export const logout = ApiClient.logout.bind(ApiClient);
export const isAuthenticated = ApiClient.isAuthenticated.bind(ApiClient);
export const recoverPassword = ApiClient.recoverPassword.bind(ApiClient);
export const resetPassword = ApiClient.resetPassword.bind(ApiClient);
export const changePassword = ApiClient.changePassword.bind(ApiClient);
export const getCitizenMe = ApiClient.getCitizenMe.bind(ApiClient);
export const getInternalUsers = ApiClient.getInternalUsers.bind(ApiClient);
export const createInternalUser = ApiClient.createInternalUser.bind(ApiClient);
export const deactivateInternalUser = ApiClient.deactivateInternalUser.bind(ApiClient);
export const getAuditEvents = ApiClient.getAuditEvents.bind(ApiClient);
export const getAppointmentsReport = ApiClient.getAppointmentsReport.bind(ApiClient);
export const createReportExport = ApiClient.createReportExport.bind(ApiClient);
export const getFaqs = ApiClient.getFaqs.bind(ApiClient);
export const openQuestion = ApiClient.openQuestion.bind(ApiClient);
