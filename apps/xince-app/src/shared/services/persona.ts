import type { PersonaCardPayload } from "@/shared/models/persona";
import { request } from "@/shared/services/http";

export function fetchPersonaCard() {
  return request<PersonaCardPayload>("/profile/persona-card");
}
