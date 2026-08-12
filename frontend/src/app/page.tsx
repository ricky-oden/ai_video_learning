import { AsyncState } from "@/components/async-state";

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">AI-LEARNING-V1 · Phase 1</p>
        <h1 id="page-title">美容師向け動画教育・AI学習支援</h1>
        <p>
          Next.js、FastAPI、PostgreSQL、pgvectorの接続を学ぶための開発基盤です。
          動画教材やAI機能は後続Phaseで実装します。
        </p>
      </section>

      <section className="panel" aria-labelledby="state-title">
        <h2 id="state-title">共通表示状態</h2>
        <div className="state-grid">
          <AsyncState kind="loading" />
          <AsyncState kind="error" />
          <AsyncState kind="empty" />
        </div>
      </section>
    </main>
  );
}
