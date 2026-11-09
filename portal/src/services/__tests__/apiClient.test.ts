import { describe, it, expect } from "vitest";
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
});

