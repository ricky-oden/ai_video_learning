import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { storeToken } from "@/lib/api/client";

import { AuthProvider, useAuth } from "./auth-provider";

function Probe() {
  const { user, loading } = useAuth();
  return <p>{loading ? "loading" : (user?.email ?? "anonymous")}</p>;
}

afterEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

describe("AuthProvider", () => {
  it("restores authentication from localStorage", async () => {
    storeToken("restored-token");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "user-1",
          email: "member@example.com",
          role: "MEMBER",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("member@example.com")).toBeInTheDocument();
    });
  });
});
