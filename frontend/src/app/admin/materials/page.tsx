"use client";

import { useEffect, useState } from "react";

import { AuthGate } from "@/components/auth-gate";
import { apiRequest } from "@/lib/api/client";
import type { AdminMaterial, TranscriptVersion } from "@/lib/api/types";
import { useAuth } from "@/providers/auth-provider";

export default function AdminMaterialsPage() {
  const { user } = useAuth();
  const [materials, setMaterials] = useState<AdminMaterial[] | null>(null);
  const [error, setError] = useState(false);
  const [importingId, setImportingId] = useState<string | null>(null);

  async function refresh() {
    setMaterials(await apiRequest<AdminMaterial[]>("/admin/materials"));
  }

  useEffect(() => {
    if (user?.role !== "ADMIN") return;
    void apiRequest<AdminMaterial[]>("/admin/materials")
      .then(setMaterials)
      .catch(() => setError(true));
  }, [user]);

  async function importTranscript(material: AdminMaterial) {
    const fixtureByMaterial: Record<string, string> = {
      "20000000-0000-4000-8000-000000000001": "hair-cut-basic-v1",
      "20000000-0000-4000-8000-000000000002": "hair-consultation-premium-v1",
    };
    const fixtureId = fixtureByMaterial[material.id];
    if (!fixtureId) return;
    setImportingId(material.id);
    setError(false);
    try {
      await apiRequest<TranscriptVersion>(
        `/admin/materials/${material.id}/transcript-imports`,
        { method: "POST", body: JSON.stringify({ fixture_id: fixtureId }) },
      );
      await refresh();
    } catch {
      setError(true);
      await refresh();
    } finally {
      setImportingId(null);
    }
  }

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
                  <th>current version</th>
                  <th>件数</th>
                  <th>provider</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {materials?.map((material) => (
                  <tr key={material.id}>
                    <td>{material.title}</td>
                    <td>{material.is_active ? "有効" : "無効"}</td>
                    <td>{material.transcript_status}</td>
                    <td>{material.current_version ?? "-"}</td>
                    <td>
                      segment {material.segment_count} / chunk{" "}
                      {material.chunk_count} / embedding{" "}
                      {material.embedding_count}
                    </td>
                    <td>
                      {material.provider_name
                        ? `${material.provider_name} / ${material.provider_version} / ${material.dimensions}`
                        : "-"}
                    </td>
                    <td>
                      {material.id !==
                        "20000000-0000-4000-8000-000000000003" && (
                        <button
                          type="button"
                          disabled={importingId === material.id}
                          onClick={() => void importTranscript(material)}
                        >
                          {importingId === material.id
                            ? "取込中…"
                            : "字幕を取り込む"}
                        </button>
                      )}
                    </td>
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
