"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AuthGate } from "@/components/auth-gate";
import { apiRequest } from "@/lib/api/client";
import type { Material } from "@/lib/api/types";

export default function MaterialsPage() {
  const [materials, setMaterials] = useState<Material[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    void apiRequest<Material[]>("/materials")
      .then(setMaterials)
      .catch(() => setError(true));
  }, []);

  return (
    <main className="page-shell">
      <AuthGate>
        <h1>教材一覧</h1>
        {error && <p role="alert">教材を取得できませんでした。</p>}
        {!error && materials === null && <p role="status">読み込み中です。</p>}
        {materials?.length === 0 && <p>表示できる教材はありません。</p>}
        <div className="card-grid">
          {materials?.map((material) => (
            <article className="card" key={material.id}>
              <p className="eyebrow">{material.required_role}</p>
              <h2>{material.title}</h2>
              <p>{material.description}</p>
              <Link href={`/materials/${material.id}`}>教材を見る</Link>
            </article>
          ))}
        </div>
      </AuthGate>
    </main>
  );
}
