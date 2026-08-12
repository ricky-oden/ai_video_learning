"use client";

import { useEffect, useState } from "react";

import { AuthGate } from "@/components/auth-gate";
import { apiRequest } from "@/lib/api/client";
import type { Material } from "@/lib/api/types";
import { useAuth } from "@/providers/auth-provider";

export default function AdminMaterialsPage() {
  const { user } = useAuth();
  const [materials, setMaterials] = useState<Material[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (user?.role !== "ADMIN") return;
    void apiRequest<Material[]>("/admin/materials")
      .then(setMaterials)
      .catch(() => setError(true));
  }, [user]);

  return (
    <main className="page-shell">
      <AuthGate>
        {user?.role !== "ADMIN" ? (
          <p role="alert">管理者権限が必要です。</p>
        ) : (
          <>
            <h1>教材・字幕状態</h1>
            {error && <p role="alert">状態を取得できませんでした。</p>}
            {!error && materials === null && (
              <p role="status">読み込み中です。</p>
            )}
            <table>
              <thead>
                <tr>
                  <th>教材</th>
                  <th>公開状態</th>
                  <th>字幕状態</th>
                </tr>
              </thead>
              <tbody>
                {materials?.map((material) => (
                  <tr key={material.id}>
                    <td>{material.title}</td>
                    <td>{material.is_active ? "有効" : "無効"}</td>
                    <td>{material.transcript_status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </AuthGate>
    </main>
  );
}
