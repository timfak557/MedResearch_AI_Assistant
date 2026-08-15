import { request } from "./apiClient";

/** Delete a conversation's server-side context. */
export function deleteConversation(conversationId: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/api/v1/conversations/${encodeURIComponent(conversationId)}`, {
    method: "DELETE",
  });
}
