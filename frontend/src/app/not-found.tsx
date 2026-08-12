import Link from "next/link";

export default function NotFound() {
  return (
    <main className="page-shell">
      <p className="eyebrow">404</p>
      <h1>ページが見つかりません</h1>
      <p>URLを確認するか、トップページへ戻ってください。</p>
      <Link href="/">トップページへ戻る</Link>
    </main>
  );
}
