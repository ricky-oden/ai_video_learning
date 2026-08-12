type AsyncStateProps = {
  kind: "loading" | "error" | "empty";
};

const messages = {
  loading: "読み込み中です。",
  error: "データを取得できませんでした。",
  empty: "表示できるデータはありません。",
} as const;

export function AsyncState({ kind }: AsyncStateProps) {
  if (kind === "loading") {
    return (
      <div className="state-message" role="status" aria-live="polite">
        {messages[kind]}
      </div>
    );
  }
  if (kind === "error") {
    return (
      <div className="state-message state-message--error" role="alert">
        {messages[kind]}
      </div>
    );
  }
  return <div className="state-message">{messages[kind]}</div>;
}
