"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { AuthGate } from "@/components/auth-gate";
import { VideoPlayer } from "@/components/video-player";
import { ApiClientError, apiRequest } from "@/lib/api/client";
import type { Material } from "@/lib/api/types";

export default function MaterialDetailPage() {
  const { materialId } = useParams<{ materialId: string }>();
  const [material, setMaterial] = useState<Material | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void apiRequest<Material>(`/materials/${materialId}`)
      .then(setMaterial)
      .catch((exception) => {
        if (exception instanceof ApiClientError && exception.status === 403) {
          setError("この教材を閲覧する権限がありません。");
        } else if (
          exception instanceof ApiClientError &&
          exception.status === 404
        ) {
          setError("教材が見つかりません。");
        } else {
          setError("教材を取得できませんでした。");
        }
      });
  }, [materialId]);

  return (
    <main className="page-shell">
      <AuthGate>
        {error && <p role="alert">{error}</p>}
        {!error && !material && <p role="status">読み込み中です。</p>}
        {material && (
          <>
            <p className="eyebrow">{material.required_role}</p>
            <h1>{material.title}</h1>
            <p>{material.description}</p>
            <VideoPlayer src={material.video_path} title={material.title} />
          </>
        )}
      </AuthGate>
    </main>
  );
}
