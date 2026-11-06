import { Agency, Appointment, AppointmentSlot, CitizenProfile, ProblemDetails, Protocol, Service, Unit } from "@/types/api";
import { MOCK_AGENCIES, MOCK_SERVICES, MOCK_UNITS } from "@/mocks/demoData";

const USE_MOCK = process.env.NEXT_PUBLIC_API_MOCK !== "false";
const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

// Mock em memória para agendamentos do cidadão
let MOCK_APPOINTMENTS: Appointment[] = [
  {
    id: "appt-001",
    protocolNumber: "20261105-1042",
    citizenId: "citizen-001",
    citizenName: "Cidadão de Testes",
    citizenCpfMasked: "***.456.789-**",
    serviceId: "servico-emitir-rg",
    serviceName: "Emitir Carteira de Identidade Nacional (CIN)",
    agencyName: "Secretaria de Estado da Segurança Pública",
    unitId: "unidade-centro",
    unitName: "Central Já! Centro",
    unitAddress: "Rua do Comércio, 123 - Centro, Maceió - AL",
    scheduledDate: "2026-11-10",
    scheduledTime: "09:30",
    status: "scheduled",
    createdAt: "2026-11-05T10:00:00Z",
  },
  {
    id: "appt-002",
    protocolNumber: "20261015-8831",
    citizenId: "citizen-001",
    citizenName: "Cidadão de Testes",
    citizenCpfMasked: "***.456.789-**",
    serviceId: "servico-renovar-cnh",
    serviceName: "Renovação da Carteira Nacional de Habilitação (CNH)",
    agencyName: "Departamento Estadual de Trânsito (DETRAN-AL)",
    unitId: "unidade-farol",
    unitName: "Central Já! Shopping Farol",
    unitAddress: "Av. Fernandes Lima, 500 - Farol, Maceió - AL",
    scheduledDate: "2026-10-18",
    scheduledTime: "14:00",
    status: "completed",
    createdAt: "2026-10-15T09:12:00Z",
  },
];

export class ApiClient {
  private static async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${BASE_URL}${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...options.headers,
    };

    try {
      const res = await fetch(url, { ...options, headers });
      if (!res.ok) {
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
  static async getServices(params?: { query?: string; category?: string; channel?: string; page?: number }): Promise<{
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

      if (params?.channel && params.channel !== "Todos") {
        filtered = filtered.filter((s) => s.channel === params.channel);
      }

      const total = filtered.length;
      const pageSize = 10;
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

    const queryParams = new URLSearchParams(params as Record<string, string>).toString();
    return this.request(`/services?${queryParams}`);
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

  static async getUnits(agencyId?: string): Promise<Unit[]> {
    if (USE_MOCK) {
      if (agencyId) return MOCK_UNITS.filter((u) => u.agencyId === agencyId);
      return MOCK_UNITS;
    }
    return this.request(`/units${agencyId ? `?agencyId=${agencyId}` : ""}`);
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
  static async getCitizenAppointments(citizenId: string): Promise<Appointment[]> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 100));
      return [...MOCK_APPOINTMENTS];
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

  static async login(cpf: string, password: string): Promise<{
    token: string;
    tokenType: string;
    expiresIn: number;
    citizen: {
      id: string;
      fullName: string;
      cpf: string;
      email: string;
      role: string;
    };
  }> {
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
        },
      };
    }
    return this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ cpf, password }),
    });
  }

  static async recoverPassword(cpf: string): Promise<{ message: string; codeSimulated?: string }> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 200));
      return { message: "Código enviado para o e-mail cadastrado.", codeSimulated: "123456" };
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
}

// Named exports for ease of consumption
export const getServices = ApiClient.getServices.bind(ApiClient);
export const getServiceById = ApiClient.getServiceById.bind(ApiClient);
export const getAgencies = ApiClient.getAgencies.bind(ApiClient);
export const getUnits = ApiClient.getUnits.bind(ApiClient);
export const getAppointmentSlots = ApiClient.getSlots.bind(ApiClient);
export const createAppointment = ApiClient.createAppointment.bind(ApiClient);
export const getCitizenAppointments = ApiClient.getCitizenAppointments.bind(ApiClient);
export const getAppointmentByProtocol = ApiClient.getAppointmentByProtocol.bind(ApiClient);
export const cancelAppointment = ApiClient.cancelAppointment.bind(ApiClient);
export const registerCitizen = ApiClient.registerCitizen.bind(ApiClient);
export const loginCitizen = ApiClient.login.bind(ApiClient);
export const recoverPassword = ApiClient.recoverPassword.bind(ApiClient);
export const resetPassword = ApiClient.resetPassword.bind(ApiClient);
export const getCitizenMe = ApiClient.getCitizenMe.bind(ApiClient);
export const getFaqs = ApiClient.getFaqs.bind(ApiClient);
export const openQuestion = ApiClient.openQuestion.bind(ApiClient);
