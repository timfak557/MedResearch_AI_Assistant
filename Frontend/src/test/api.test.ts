import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, request } from "@/api/apiClient";

function mockFetch(status: number, body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      json: () => Promise.resolve(body),
    }),
  );
}

afterEach(() => vi.unstubAllGlobals());

describe("apiClient error mapping", () => {
  it("returns parsed JSON on success", async () => {
    mockFetch(200, { status: "healthy" });
    await expect(request("/health")).resolves.toEqual({ status: "healthy" });
  });

  it("maps 422 to a validation error", async () => {
    mockFetch(422, { error: "Query must not be empty." });
    const error = await request("/api/v1/search", { method: "POST", body: {} }).catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).kind).toBe("validation");
  });

  it("maps 502 to a friendly LLM failure message", async () => {
    mockFetch(502, { error: "The language model is currently unavailable." });
    const error = await request("/api/v1/chat", { method: "POST", body: {} }).catch((e) => e);
    expect((error as ApiError).kind).toBe("llm");
    expect((error as ApiError).message).toMatch(/could not be generated/i);
  });

  it("maps 503 to a retrieval-unavailable message", async () => {
    mockFetch(503, {});
    const error = await request("/api/v1/search", { method: "POST", body: {} }).catch((e) => e);
    expect((error as ApiError).kind).toBe("retrieval");
    expect((error as ApiError).message).toMatch(/temporarily unavailable/i);
  });

  it("maps network failure to a friendly connection message", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    const error = await request("/health").catch((e) => e);
    expect((error as ApiError).kind).toBe("network");
    expect((error as ApiError).message).toMatch(/unable to connect/i);
  });

  it("never leaks stack traces or internals into messages", async () => {
    mockFetch(500, { detail: 'Traceback (most recent call last): File "/app/main.py"' });
    const error = await request("/api/v1/chat", { method: "POST", body: {} }).catch((e) => e);
    expect((error as ApiError).message).not.toMatch(/traceback|\.py/i);
  });
});
