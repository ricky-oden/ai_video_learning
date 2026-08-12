"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { useAuth } from "@/providers/auth-provider";

export function AuthGate({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <p role="status">認証状態を確認しています。</p>;
  if (!user) {
    return (
      <p role="alert">
        ログインが必要です。<Link href="/login">ログイン画面へ</Link>
      </p>
    );
  }
  return children;
}
