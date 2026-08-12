import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AskPage from "./page";

vi.mock("@/providers/auth-provider", () => ({
  useAuth: () => ({
    user: { id: "premium", email: "premium@example.com", role: "PREMIUM" },
    loading: false,
  }),
}));

const material = {
  id: "material-1",
  title: "教材",
  description: "説明",
  required_role: "MEMBER",
  video_path: "/media/demo.mp4",
  duration_ms: 6000,
  transcript_status: "READY",
  is_active: true,
  created_at: "2026-08-12T00:00:00Z",
  updated_at: "2026-08-12T00:00:00Z",
};

describe("AskPage", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("keeps input after an API failure", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (_input, init) => {
      if (init?.method === "POST") return new Response(null, { status: 500 });
      return Response.json([material]);
    });
    render(<AskPage />);
    const input = screen.getByLabelText("質問");
    fireEvent.change(input, { target: { value: "保持する質問" } });
    await screen.findByLabelText("教材");
    fireEvent.click(screen.getByRole("button", { name: "質問する" }));
    await screen.findByRole("alert");
    expect(input).toHaveValue("保持する質問");
  });

  it("disables submission while waiting and renders terminal refusal", async () => {
    let resolvePost: ((response: Response) => void) | undefined;
    vi.spyOn(globalThis, "fetch").mockImplementation(async (_input, init) => {
      if (init?.method !== "POST") return Response.json([material]);
      return new Promise<Response>((resolve) => {
        resolvePost = resolve;
      });
    });
    render(<AskPage />);
    fireEvent.change(screen.getByLabelText("質問"), {
      target: { value: "教材外質問" },
    });
    await screen.findByLabelText("教材");
    fireEvent.click(screen.getByRole("button", { name: "質問する" }));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "送信中…" })).toBeDisabled(),
    );
    resolvePost?.(
      Response.json({
        run_id: "run-1",
        question: "教材外質問",
        material_ids: ["material-1"],
        status: "REFUSED_OUT_OF_SCOPE",
        failure_code: null,
        created_at: "2026-08-12T00:00:00Z",
        completed_at: "2026-08-12T00:00:01Z",
        answer: null,
      }),
    );
    expect(await screen.findByText(/教材外の質問/)).toBeInTheDocument();
  });
});
