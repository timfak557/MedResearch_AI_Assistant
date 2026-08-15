import type { Source } from "./source";

export interface ChatRequest {
  message: string;
  conversation_id: string | null;
}

export type SafetyCategory =
  | "general_medical_information"
  | "medical_research"
  | "diagnosis_request"
  | "treatment_request"
  | "medication_request"
  | "emergency"
  | "self_harm"
  | "unrelated"
  | "prompt_injection"
  | (string & {}); // tolerate future categories

export interface ChatResponse {
  conversation_id: string;
  answer: string;
  sources?: Source[];
  retrieval_count?: number;
  confidence?: number;
  insufficient_context?: boolean;
  safety_category?: SafetyCategory;
  disclaimer?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string; // ISO
  /** Present only on assistant messages. */
  response?: ChatResponse;
  /** Local-only feedback state (no backend endpoint exists for feedback). */
  feedback?: "helpful" | "not_helpful";
}
