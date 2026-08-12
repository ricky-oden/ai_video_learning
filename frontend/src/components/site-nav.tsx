"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/providers/auth-provider";

export function SiteNav() {
  const { user, logout } = useAuth();
  const router = useRouter();
  return (
    <nav className="site-nav" aria-label="メインナビゲーション">
      <Link href="/">ホーム</Link>
      {user && <Link href="/materials">教材</Link>}
      {user?.role === "ADMIN" && <Link href="/admin/materials">管理</Link>}
      {user ? (
        <button
          type="button"
          onClick={async () => {
            await logout();
            router.push("/login");
          }}
        >
          ログアウト
        </button>
      ) : (
        <Link href="/login">ログイン</Link>
      )}
    </nav>
  );
}
