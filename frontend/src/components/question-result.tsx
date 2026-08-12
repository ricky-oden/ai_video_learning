import Link from "next/link";

import type { QuestionRun } from "@/lib/api/types";

const statusMessage: Record<QuestionRun["status"], string> = {
  PROCESSING: "処理中です。",
  COMPLETED: "回答しました。",
  REFUSED_INSUFFICIENT_EVIDENCE: "根拠が不足しているため回答できません。",
  REFUSED_OUT_OF_SCOPE: "教材外の質問には回答できません。",
  FAILED: "回答処理に失敗しました。",
};

export function QuestionResult({ run }: { run: QuestionRun }) {
  return (
    <section className="card" aria-label="質問結果">
      <p className="eyebrow">{run.status}</p>
      <p>{statusMessage[run.status]}</p>
      {run.answer && (
        <>
          <h2>回答</h2>
          <p className="answer-body">{run.answer.body}</p>
          <button
            type="button"
            onClick={() =>
              void navigator.clipboard.writeText(run.answer?.body ?? "")
            }
          >
            回答をコピー
          </button>
          <h3>根拠</h3>
          <ol>
            {run.answer.citations.map((citation) => (
              <li key={citation.id}>
                <Link
                  href={`/materials/${citation.material_id}?start_ms=${citation.start_ms}`}
                >
                  {citation.start_ms / 1000}秒から動画を確認
                </Link>
                <p>{citation.text_snapshot}</p>
              </li>
            ))}
          </ol>
        </>
      )}
    </section>
  );
}
