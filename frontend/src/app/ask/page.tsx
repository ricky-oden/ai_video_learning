"use client";

import { type FormEvent, useEffect, useState } from "react";

import { AuthGate } from "@/components/auth-gate";
import { QuestionResult } from "@/components/question-result";
import { apiRequest } from "@/lib/api/client";
import type { Material, QuestionRun } from "@/lib/api/types";
import { useAuth } from "@/providers/auth-provider";

export default function AskPage() {
  const { user } = useAuth();
  const [materials, setMaterials] = useState<Material[]>([]);
  const [question, setQuestion] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<QuestionRun | null>(null);

  useEffect(() => {
    if (!user || user.role === "MEMBER") return;
    void apiRequest<Material[]>("/materials").then((items) => {
      setMaterials(items);
      if (items[0]) setSelected([items[0].id]);
    });
  }, [user]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      setResult(
        await apiRequest<QuestionRun>("/question-runs", {
          method: "POST",
          body: JSON.stringify({ question, material_ids: selected }),
        }),
      );
    } catch {
      setError("質問を送信できませんでした。入力内容は保持されています。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="page-shell">
      <AuthGate>
        {user?.role === "MEMBER" ? (
          <p role="alert">PREMIUMまたはADMIN権限が必要です。</p>
        ) : (
          <>
            <h1>教材へ質問</h1>
            <form
              className="form-stack"
              onSubmit={(event) => void submit(event)}
            >
              <label>
                質問
                <textarea
                  required
                  minLength={1}
                  maxLength={500}
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                />
              </label>
              <fieldset>
                <legend>対象教材（1〜5件）</legend>
                {materials.map((material) => (
                  <label key={material.id}>
                    <input
                      type="checkbox"
                      checked={selected.includes(material.id)}
                      onChange={(event) =>
                        setSelected((current) =>
                          event.target.checked
                            ? [...current, material.id].slice(0, 5)
                            : current.filter((id) => id !== material.id),
                        )
                      }
                    />
                    {material.title}
                  </label>
                ))}
              </fieldset>
              <button
                type="submit"
                disabled={submitting || selected.length === 0}
              >
                {submitting ? "送信中…" : "質問する"}
              </button>
            </form>
            {error && <p role="alert">{error}</p>}
            {result && <QuestionResult run={result} />}
          </>
        )}
      </AuthGate>
    </main>
  );
}
