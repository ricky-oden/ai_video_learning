"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { ApiClientError } from "@/lib/api/client";
import { useAuth } from "@/providers/auth-provider";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSubmitting(true);
    setError("");
    try {
      await login(String(form.get("email")), String(form.get("password")));
      router.push("/materials");
    } catch (exception) {
      setError(
        exception instanceof ApiClientError && exception.status === 401
          ? "メールアドレスまたはパスワードが違います。"
          : "ログインできませんでした。",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="page-shell narrow">
      <h1>ログイン</h1>
      {error && <p role="alert">{error}</p>}
      <form className="form-stack" onSubmit={handleSubmit}>
        <label>
          メールアドレス
          <input name="email" type="email" autoComplete="email" required />
        </label>
        <label>
          パスワード
          <input
            name="password"
            type="password"
            autoComplete="current-password"
            required
          />
        </label>
        <button type="submit" disabled={submitting}>
          {submitting ? "ログイン中…" : "ログイン"}
        </button>
      </form>
    </main>
  );
}
