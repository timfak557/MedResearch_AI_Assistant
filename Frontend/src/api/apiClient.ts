/** Centralized API client.
 *
 * All requests go through `request()`, which applies the base URL, a
 * timeout, JSON handling, and converts every failure into an `ApiError`
 * with a user-friendly message. Raw backend errors, stack traces, and
 * internals are never surfaced to the UI.
 */

export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8080";

const DEFAULT_TIMEOUT_MS = 90_000;

export type ApiErrorKind =
  | "network"
  | "timeout"
  | "validation"
  | "llm"
  | "retrieval"
  | "not_found"
  | "server";

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status?: number;

  constructor(kind: ApiErrorKind, message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
  }
}

function friendlyMessage(status: number, backendError?: string): { kind: ApiErrorKind; message: string } {
  if (status === 422 || status === 400) {
    return { kind: "validation", message: backendError ?? "Please enter a valid research question." };
  }
  if (status === 404) {
    return { kind: "not_found", message: "The requested item was not found." };
  }
  if (status === 502) {
    return { kind: "llm", message: "The AI response could not be generated. Please try again." };
  }
  if (status === 503) {
    return { kind: "retrieval", message: "Medical knowledge search is temporarily unavailable." };
  }
  return { kind: "server", message: "Something went wrong. Please try again." };
}

interface RequestOptions {
  method?: "GET" | "POST" | "DELETE";
  body?: unknown;
  timeoutMs?: number;
  signal?: AbortSignal;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, timeoutMs = DEFAULT_TIMEOUT_MS, signal } = options;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  if (signal) signal.addEventListener("abort", () => controller.abort(), { once: true });

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (error) {
    clearTimeout(timer);
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("timeout", "The request took too long. Please try again.");
    }
    throw new ApiError("network", "Unable to connect to the MedResearch AI service.");
  }
  clearTimeout(timer);

  if (!response.ok) {
    // Backend errors arrive as {"error": "..."} or FastAPI {"detail": "..."} —
    // both are sanitized server-side, but we still map to friendly text.
    let backendError: string | undefined;
    try {
      const data: unknown = await response.json();
      if (data && typeof data === "object") {
        const record = data as Record<string, unknown>;
        if (typeof record.error === "string") backendError = record.error;
        else if (typeof record.detail === "string") backendError = record.detail;
      }
    } catch {
      /* non-JSON error body — ignore */
    }
    const { kind, message } = friendlyMessage(response.status, backendError);
    throw new ApiError(kind, message, response.status);
  }

  return (await response.json()) as T;
}
