import { describe, it, expect, vi, afterEach } from "vitest";
import { ApiClient } from "../apiClient";

describe("ApiClient Services & Mocks (Contratos, RN-05, RN-18, RN-20)", () => {
  it("deve listar serviços com paginação de 10 itens por página (RN-05)", async () => {
    const result = await ApiClient.getServices({ page: 1 });
    expect(result).toHaveProperty("items");
    expect(result.pageSize).toBe(10);
    expect(result.items.length).toBeLessThanOrEqual(10);
    expect(result.totalPages).toBeGreaterThanOrEqual(1);
  });

  it("deve filtrar serviços por termo de busca", async () => {
    const result = await ApiClient.getServices({ query: "identidade" });
    expect(result.items.length).toBeGreaterThan(0);
    const hasMatch = result.items.some(
      (s) =>
        s.name.toLowerCase().includes("identidade") ||
        s.summary.toLowerCase().includes("identidade")
    );
    expect(hasMatch).toBe(true);
  });

  it("deve carregar slots de 30 minutos dentro do expediente (RN-18)", async () => {
    const slots = await ApiClient.getSlots("unidade-centro", "2026-11-10");
    expect(slots.length).toBeGreaterThan(0);

    // Valida que cada slot tem 30 minutos de duração (ex: 08:00 às 08:30)
    slots.forEach((slot) => {
      const [startHour, startMin] = slot.startsAt.split(":").map(Number);
      const [endHour, endMin] = slot.endsAt.split(":").map(Number);
      const diffMinutes = endHour * 60 + endMin - (startHour * 60 + startMin);
      expect(diffMinutes).toBe(30);
      expect(slot.capacity).toBeGreaterThan(0);
    });
  });

  it("deve criar agendamento atômico gerando protocolo no formato AAAAMMDD-XXXX (RN-20)", async () => {
    const appt = await ApiClient.createAppointment({
      serviceId: "servico-emitir-rg",
      unitId: "unidade-centro",
      scheduledDate: "2026-11-12",
      scheduledTime: "10:00",
    });

    expect(appt).toBeDefined();
    expect(appt.id).toBeTruthy();
    // Protocolo AAAAMMDD-XXXX
    expect(appt.protocolNumber).toMatch(/^\d{8}-\d{4}$/);
    expect(appt.status).toBe("scheduled");
  });

  it("deve cancelar agendamento com sucesso", async () => {
    const appointments = await ApiClient.getCitizenAppointments("citizen-001");
    expect(appointments.length).toBeGreaterThan(0);

    const targetId = appointments[0].id;
    await ApiClient.cancelAppointment(targetId, "Imprevisto pessoal");

    const updated = await ApiClient.getCitizenAppointments("citizen-001");
    const cancelledAppt = updated.find((a) => a.id === targetId);
    expect(cancelledAppt?.status).toBe("cancelled");
  });

  it("deve iniciar sem agendamentos fakes preexistentes para cidadão sem agendamentos", async () => {
    const list = await ApiClient.getCitizenAppointments("citizen-fresh-zero");
    expect(list).toEqual([]);
  });

  it("deve atualizar dados do órgão via updateAgency", async () => {
    const updated = await ApiClient.updateAgency("agency-detran", {
      name: "Departamento Estadual de Trânsito Atualizado",
      acronym: "DETRAN-AL",
      sphere: "state",
      description: "Nova descrição atualizada",
    });
    expect(updated.name).toBe("Departamento Estadual de Trânsito Atualizado");
    expect(updated.acronym).toBe("DETRAN-AL");
  });

  describe("Limpeza de sessão em erro 401 (RN-28)", () => {
    const originalLocation = window.location;

    afterEach(() => {
      vi.unstubAllEnvs();
      vi.unstubAllGlobals();
      vi.resetModules();
      localStorage.clear();
      Object.defineProperty(window, "location", {
        configurable: true,
        value: originalLocation,
      });
    });

    it("deve remover sosp_auth_token e sosp_user e redirecionar conta institucional para /sessao-expirada?tipo=institucional", async () => {
      vi.resetModules();
      vi.stubEnv("NEXT_PUBLIC_API_MOCK", "false");
      vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.sosp.test/api/v1");

      localStorage.setItem("sosp_auth_token", "expired-jwt");
      localStorage.setItem(
        "sosp_user",
        JSON.stringify({ id: "admin-1", fullName: "Admin SOSP", role: "superadmin" })
      );

      let assignedHref = "";
      Object.defineProperty(window, "location", {
        configurable: true,
        value: {
          pathname: "/admin/orgaos",
          get href() {
            return assignedHref;
          },
          set href(val: string) {
            assignedHref = val;
          },
        },
      });

      const fetchMock = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({
          type: "https://sosp.al.gov.br/errors/401",
          title: "Não autenticado",
          status: 401,
          detail: "Sessão expirada por inatividade.",
        }),
      });
      vi.stubGlobal("fetch", fetchMock);

      const { ApiClient: LiveApiClient } = await import("../apiClient");

      await expect(LiveApiClient.getAgencies()).rejects.toMatchObject({ status: 401 });
      expect(localStorage.getItem("sosp_auth_token")).toBeNull();
      expect(localStorage.getItem("sosp_user")).toBeNull();
      expect(assignedHref).toBe("/sessao-expirada?tipo=institucional");
    });
  });
});

