import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import HomePage from "./page";

describe("HomePage", () => {
  it("shows the Phase 1 top page", () => {
    render(<HomePage />);
    expect(
      screen.getByRole("heading", { name: "美容師向け動画教育・AI学習支援" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/AI機能は後続Phase/)).toBeInTheDocument();
  });

  it("shows loading, error, and empty foundation states", () => {
    render(<HomePage />);
    expect(screen.getByRole("status")).toHaveTextContent("読み込み中です。");
    expect(screen.getByRole("alert")).toHaveTextContent(
      "データを取得できませんでした。",
    );
    expect(
      screen.getByText("表示できるデータはありません。"),
    ).toBeInTheDocument();
  });
});
