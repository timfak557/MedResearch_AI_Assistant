import { useCallback } from "react";
import { deleteConversation } from "@/api/conversationApi";
import { useApp } from "@/context/AppContext";

export function useConversations() {
  const { conversations, removeConversation, clearAllConversations } = useApp();

  /** Remove locally and clear the backend's conversation context. */
  const deleteOne = useCallback(
    async (id: string) => {
      removeConversation(id);
      try {
        await deleteConversation(id);
      } catch {
        // Backend context may already be expired — local removal is enough.
      }
    },
    [removeConversation],
  );

  return { conversations, deleteOne, clearAllConversations };
}
