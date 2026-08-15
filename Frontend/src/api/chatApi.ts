import { request } from "./apiClient";
import type { ChatRequest, ChatResponse } from "@/types/chat";

export function sendChatMessage(body: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
  return request<ChatResponse>("/api/v1/chat", { method: "POST", body, signal });
}
