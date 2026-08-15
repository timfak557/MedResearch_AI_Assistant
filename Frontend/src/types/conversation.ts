import type { ChatMessage } from "./chat";

/** Locally stored research conversation (backend keeps its own context by ID). */
export interface Conversation {
  id: string; // backend conversation_id
  title: string;
  createdAt: string; // ISO
  updatedAt: string; // ISO
  lastQuestion: string;
  messages: ChatMessage[];
}
