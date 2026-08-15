import { API_BASE_URL } from "./apiClient";
import type { ReadyResponse, SystemStatus } from "@/types/health";

/** /ready returns 503 with a JSON body when not ready — treat both as data. */
export async function fetchSystemStatus(): Promise<SystemStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/ready`, { method: "GET" });
    const data = (await response.json()) as ReadyResponse;
    return {
      api: "connected",
      qdrant: data.qdrant ? "connected" : "unavailable",
      embeddingModel: data.embedding_model ? "connected" : "unavailable",
      llm: data.llm_configured ? "connected" : "unavailable",
    };
  } catch {
    return { api: "unavailable", qdrant: "unavailable", embeddingModel: "unavailable", llm: "unavailable" };
  }
}
