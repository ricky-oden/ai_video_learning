import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AdminMaterialsPage from "./page";

vi.mock("@/providers/auth-provider", () => ({
  useAuth: () => ({
    user: { id: "admin", email: "admin@example.com", role: "ADMIN" },
    loading: false,
  }),
}));

describe("AdminMaterialsPage", () => {
  beforeEach(() => {
    const base = {
      id: "20000000-0000-4000-8000-000000000001",
      title: "教材",
      description: "説明",
      required_role: "MEMBER",
      video_path: "/media/demo-hair-technique.mp4",
      duration_ms: 6000,
      is_active: true,
      created_at: "2026-08-12T00:00:00Z",
      updated_at: "2026-08-12T00:00:00Z",
    };
    let imported = false;
    vi.spyOn(globalThis, "fetch").mockImplementation(async (_input, init) => {
      if (init?.method === "POST") {
        imported = true;
        return Response.json({ id: "version-1", status: "READY" });
      }
      return Response.json([
        {
          ...base,
          transcript_status: imported ? "READY" : "NOT_IMPORTED",
          current_version: imported ? 1 : null,
          latest_version: imported ? 1 : null,
          segment_count: imported ? 5 : 0,
          chunk_count: imported ? 2 : 0,
          embedding_count: imported ? 2 : 0,
          provider_name: imported ? "deterministic-local" : null,
          provider_version: imported ? "hash-char-ngram-v1" : null,
          dimensions: imported ? 32 : null,
        },
      ]);
    });
  });

  it("imports a fixture and shows READY counts and provider metadata", async () => {
    render(<AdminMaterialsPage />);
    expect(await screen.findByText("NOT_IMPORTED")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "字幕を取り込む" }));
    await waitFor(() => expect(screen.getByText("READY")).toBeInTheDocument());
    expect(
      screen.getByText(/segment 5 \/ chunk 2 \/ embedding 2/),
    ).toBeInTheDocument();
    expect(screen.getByText(/deterministic-local/)).toBeInTheDocument();
  });
});
