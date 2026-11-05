/**
 * Tipos oficiais da API SOSP (OpenAPI 3.0.3 — docs/api/openapi.yaml)
 * Todas as propriedades em camelCase (ADR-002)
 */

export type ServiceChannel = "online" | "inPerson" | "hybrid";

export type ServiceCategory =
  | "Documentos"
  | "Saúde"
  | "Educação"
  | "Transporte"
  | "Assistência Social"
  | "Tributos"
  | "Trabalho";

export type ProtocolStatus =
  | "received"
  | "in_analysis"
  | "awaiting_document"
  | "scheduled"
  | "completed"
  | "cancelled";

export interface ServiceDocument {
  id: string;
  name: string;
  isRequired: boolean;
  description?: string;
  sampleUrl?: string;
}

export interface ServiceStep {
  stepOrder: number;
  title: string;
  description: string;
  estimatedTime?: string;
}

export interface Service {
  id: string;
  name: string;
  category: ServiceCategory;
  channel: ServiceChannel;
  agencyId: string;
  agencyAcronym: string;
  agencyName: string;
  isFree: boolean;
  costAmount: number | null;
  averageDeadlineDays: number;
  summary: string;
  description: string;
  whoCanUse: string;
  prerequisites?: string;
  externalUrl?: string;
  updatedAt: string;
  unitCount: number;
  documents: ServiceDocument[];
  steps: ServiceStep[];
}

export interface Agency {
  id: string;
  name: string;
  acronym: string;
  sphere: "municipal" | "state" | "federal";
  description?: string;
  isActive: boolean;
}

export interface Unit {
  id: string;
  agencyId: string;
  name: string;
  cep: string;
  street: string;
  number: string;
  neighborhood: string;
  city: string;
  state: string;
  phone?: string;
  email?: string;
  openingHours: string;
  dailyLimit: number;
  latitude?: number;
  longitude?: number;
  isPcdAccessible: boolean;
  hasPriorityService: boolean;
  isActive: boolean;
}

export interface AppointmentSlot {
  slotDate: string; // YYYY-MM-DD
  startsAt: string; // HH:MM
  endsAt: string;   // HH:MM
  capacity: number;
  bookedCount: number;
  isAvailable: boolean;
}

export interface Appointment {
  id: string;
  protocolNumber: string; // AAAAMMDD-XXXX
  citizenId: string;
  citizenName: string;
  citizenCpfMasked: string;
  serviceId: string;
  serviceName: string;
  agencyName: string;
  unitId: string;
  unitName: string;
  unitAddress: string;
  scheduledDate: string;
  scheduledTime: string;
  status: "scheduled" | "confirmed" | "completed" | "cancelled" | "no_show";
  createdAt: string;
}

export interface ProtocolTimelineEvent {
  status: ProtocolStatus;
  statusLabel: string;
  occurredAt: string;
  actorName: string;
  observation?: string;
}

export interface ProtocolAttachment {
  id: string;
  fileName: string;
  fileSize: number;
  contentType: string;
  uploadedAt: string;
}

export interface Protocol {
  protocolNumber: string;
  protocolType: "appointment" | "question";
  status: ProtocolStatus;
  statusLabel: string;
  serviceName: string;
  agencyName: string;
  unitName?: string;
  createdAt: string;
  estimatedCompletionDate?: string;
  timeline: ProtocolTimelineEvent[];
  attachments: ProtocolAttachment[];
}

export interface CitizenProfile {
  id: string;
  cpf: string;
  fullName: string;
  birthDate: string;
  email: string;
  phone: string;
  gender: string;
  isPcd: boolean;
  pcdDescription?: string;
  motherName: string;
  fatherName?: string;
  cep: string;
  street: string;
  number: string;
  complement?: string;
  neighborhood: string;
  city: string;
  state: string;
  avatarUrl?: string;
}

/** RFC 7807 — Problem Details */
export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  traceId?: string;
  errors?: Array<{ field: string; message: string }>;
}

