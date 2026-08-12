import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { QuestionRun } from "@/lib/api/types";

import { QuestionResult } from "./question-result";

function run(status: QuestionRun["status"]): QuestionRun {
  return {
    run_id: "run-1",
    question: "質問",
    material_ids: ["material-1"],
    status,
    failure_code: null,
    created_at: "2026-08-12T00:00:00Z",
    completed_at: "2026-08-12T00:00:01Z",
    answer:
      status === "COMPLETED"
        ? {
            id: "answer-1",
            body: "根拠だけの回答",
            provider_name: "deterministic-local",
            provider_version: "grounded-extractive-v1",
            citations: [
              {
                id: "citation-1",
                material_id: "material-1",
                transcript_version_id: "version-1",
                chunk_id: "chunk-1",
                video_path: "/media/demo.mp4",
                start_ms: 2400,
                end_ms: 4800,
                text_snapshot: "根拠本文",
                display_order: 1,
              },
            ],
          }
        : null,
  };
}

describe("QuestionResult", () => {
  it.each([
    ["REFUSED_INSUFFICIENT_EVIDENCE", "根拠が不足"],
    ["REFUSED_OUT_OF_SCOPE", "教材外"],
    ["FAILED", "失敗"],
  ] as const)("shows %s explicitly", (status, message) => {
    render(<QuestionResult run={run(status)} />);
    expect(screen.getByText(new RegExp(message))).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "回答をコピー" }),
    ).not.toBeInTheDocument();
  });

  it("copies only a completed answer and links citation to the playback position", () => {
    const writeText = vi.fn();
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    render(<QuestionResult run={run("COMPLETED")} />);
    fireEvent.click(screen.getByRole("button", { name: "回答をコピー" }));
    expect(writeText).toHaveBeenCalledWith("根拠だけの回答");
    expect(
      screen.getByRole("link", { name: "2.4秒から動画を確認" }),
    ).toHaveAttribute("href", "/materials/material-1?start_ms=2400");
  });
});
