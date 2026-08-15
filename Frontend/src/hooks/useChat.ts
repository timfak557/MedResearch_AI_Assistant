import { useCallback, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { sendChatMessage } from "@/api/chatApi";
import { ApiError } from "@/api/apiClient";
import { useApp } from "@/context/AppContext";
import { generateId, truncate } from "@/lib/utils";
import { chatMessageSchema } from "@/lib/validation";
import type { ChatMessage } from "@/types/chat";
import type { Conversation } from "@/types/conversation";

interface UseChatResult {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (text: string) => void;
  regenerate: () => void;
  newConversation: () => void;
  openConversation: (conversation: Conversation) => void;
  setFeedback: (messageId: string, feedback: "helpful" | "not_helpful") => void;
  conversationId: string | null;
  lastAssistantMessage: ChatMessage | null;
}

export function useChat(): UseChatResult {
  const {
    activeConversationId,
    setActiveConversationId,
    conversations,
    upsertConversation,
  } = useApp();

  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const active = conversations.find((c) => c.id === activeConversationId);
    return active?.messages ?? [];
  });
  const [error, setError] = useState<string | null>(null);
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: ({ text, conversationId }: { text: string; conversationId: string | null }) =>
      sendChatMessage({ message: text, conversation_id: conversationId }),
  });

  const persist = useCallback(
    (conversationId: string, nextMessages: ChatMessage[]) => {
      const firstUser = nextMessages.find((m) => m.role === "user");
      const lastUser = [...nextMessages].reverse().find((m) => m.role === "user");
      const existing = conversations.find((c) => c.id === conversationId);
      upsertConversation({
        id: conversationId,
        title: existing?.title ?? truncate(firstUser?.content ?? "Research session", 60),
        createdAt: existing?.createdAt ?? new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        lastQuestion: lastUser?.content ?? "",
        messages: nextMessages,
      });
    },
    [conversations, upsertConversation],
  );

  const sendMessage = useCallback(
    (text: string) => {
      const parsed = chatMessageSchema.safeParse(text);
      if (!parsed.success) {
        setError(parsed.error.issues[0]?.message ?? "Please enter a valid research question.");
        return;
      }
      setError(null);
      setLastQuestion(parsed.data);

      const userMessage: ChatMessage = {
        id: generateId(),
        role: "user",
        content: parsed.data,
        createdAt: new Date().toISOString(),
      };
      setMessages((previous) => [...previous, userMessage]);

      mutation.mutate(
        { text: parsed.data, conversationId: activeConversationId },
        {
          onSuccess: (response) => {
            const assistantMessage: ChatMessage = {
              id: generateId(),
              role: "assistant",
              content: response.answer,
              createdAt: new Date().toISOString(),
              response,
            };
            setActiveConversationId(response.conversation_id);
            setMessages((previous) => {
              const next = [...previous, assistantMessage];
              persist(response.conversation_id, next);
              return next;
            });
          },
          onError: (mutationError) => {
            setError(
              mutationError instanceof ApiError
                ? mutationError.message
                : "Something went wrong. Please try again.",
            );
          },
        },
      );
    },
    [activeConversationId, mutation, persist, setActiveConversationId],
  );

  const regenerate = useCallback(() => {
    if (lastQuestion && !mutation.isPending) sendMessage(lastQuestion);
  }, [lastQuestion, mutation.isPending, sendMessage]);

  const newConversation = useCallback(() => {
    setMessages([]);
    setError(null);
    setLastQuestion(null);
    setActiveConversationId(null);
  }, [setActiveConversationId]);

  const openConversation = useCallback(
    (conversation: Conversation) => {
      setMessages(conversation.messages);
      setActiveConversationId(conversation.id);
      setError(null);
    },
    [setActiveConversationId],
  );

  const setFeedback = useCallback((messageId: string, feedback: "helpful" | "not_helpful") => {
    // Local-only UI state: the backend has no feedback endpoint.
    setMessages((previous) =>
      previous.map((m) => (m.id === messageId ? { ...m, feedback } : m)),
    );
  }, []);

  const lastAssistantMessage =
    [...messages].reverse().find((m) => m.role === "assistant") ?? null;

  return {
    messages,
    isLoading: mutation.isPending,
    error,
    sendMessage,
    regenerate,
    newConversation,
    openConversation,
    setFeedback,
    conversationId: activeConversationId,
    lastAssistantMessage,
  };
}
