"use client";

import { useEffect, useState } from "react";

import { AuthGate } from "@/components/auth-gate";
import { QuestionResult } from "@/components/question-result";
import { apiRequest } from "@/lib/api/client";
import type { QuestionRun } from "@/lib/api/types";

export default function HistoryPage() {
  const [runs, setRuns] = useState<QuestionRun[] | null>(null);
  const [feedback, setFeedback] = useState<Record<string, string>>({});

  useEffect(() => {
    void apiRequest<QuestionRun[]>("/questions/history").then(setRuns);
  }, []);

  async function rate(answerId: string, rating: "UP" | "DOWN") {
    await apiRequest(`/answers/${answerId}/feedback`, {
      method: "POST",
      body: JSON.stringify({ rating }),
    });
    setFeedback((current) => ({ ...current, [answerId]: rating }));
  }

  return (
    <main className="page-shell">
      <AuthGate>
        <h1>質問・回答履歴</h1>
        {runs === null && <p role="status">読み込み中です。</p>}
        {runs?.length === 0 && <p>履歴はありません。</p>}
        <div className="card-grid">
          {runs?.map((run) => (
            <article key={run.run_id}>
              <h2>{run.question}</h2>
              <QuestionResult run={run} />
              {run.status === "COMPLETED" && run.answer && (
                <div>
                  <button
                    type="button"
                    onClick={() => void rate(run.answer!.id, "UP")}
                  >
                    役に立った
                  </button>
                  <button
                    type="button"
                    onClick={() => void rate(run.answer!.id, "DOWN")}
                  >
                    改善が必要
                  </button>
                  {feedback[run.answer.id] && <span>評価を保存しました。</span>}
                </div>
              )}
            </article>
          ))}
        </div>
      </AuthGate>
    </main>
  );
}
