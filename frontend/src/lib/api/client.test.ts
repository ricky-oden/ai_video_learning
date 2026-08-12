import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiClientError,
  apiRequest,
  clearStoredToken,
  getStoredToken,
  storeToken,
} from "./client";

afterEach(() => {
  vi.restoreAllMocks();
  clearStoredToken();
});

describe("apiRequest", () => {
  it("adds the stored Bearer token", async () => {
    storeToken("opaque-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await apiRequest<{ ok: boolean }>("/auth/me");

    const request = fetchMock.mock.calls[0];
    expect(new Headers(request[1]?.headers).get("Authorization")).toBe(
      "Bearer opaque-token",
    );
  });

  it("clears the token after a 401 response", async () => {
    storeToken("expired-token");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ error: {} }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(apiRequest("/auth/me")).rejects.toBeInstanceOf(ApiClientError);
    expect(getStoredToken()).toBeNull();
  });
});
