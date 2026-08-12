import { render, screen, waitFor } from "@testing-library/react";
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
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            id: "material-1",
            title: "教材",
            description: "説明",
            required_role: "MEMBER",
            video_path: "/media/demo-hair-technique.mp4",
            duration_ms: 6000,
            transcript_status: "NOT_IMPORTED",
            is_active: true,
            created_at: "2026-08-12T00:00:00Z",
            updated_at: "2026-08-12T00:00:00Z",
          },
        ]),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
  });

  it("shows NOT_IMPORTED transcript state", async () => {
    render(<AdminMaterialsPage />);
    await waitFor(() => {
      expect(screen.getByText("NOT_IMPORTED")).toBeInTheDocument();
    });
  });
});
