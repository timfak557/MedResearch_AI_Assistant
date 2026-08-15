export interface HealthResponse {
  status: string;
  service?: string;
}

export interface ReadyResponse {
  status: "ready" | "not_ready" | (string & {});
  qdrant?: boolean;
  embedding_model?: boolean;
  llm_configured?: boolean;
}

export type ServiceState = "connected" | "unavailable" | "checking";

export interface SystemStatus {
  api: ServiceState;
  qdrant: ServiceState;
  embeddingModel: ServiceState;
  llm: ServiceState;
}
