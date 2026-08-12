# 実装状態

PLAN_VERSION: `AI-LEARNING-V1.0`

最終更新日: 2026-08-12

## 現在フェーズ

`Phase 4: 根拠付き質問応答（実装・検証済み・Phase 5未着手）`

## 全体状態

- 計画文書: `AI-LEARNING-V1.0`初期正本として承認済み
- アプリケーション: Phase 4の同期式根拠付き質問応答、回答抑止、citation、履歴、feedbackまで実装済み
- frontend: `/ask`、`/history`、状態別表示、完了回答コピー、citation seek、feedbackを追加・検証済み
- backend: cosine pgvector検索、`evidence-policy-v1`、根拠限定fake回答、生成後citation検証、所有権・教材認可を実装・検証済み
- database / migration: question/retrieval/result/answer/citation/feedbackを追加し、検索条件・provider metadata・回答時snapshotをAlembic管理・検証済み
- Docker Compose: frontend/backend/db/test-dbに加え、profile付きPlaywright runnerを実装・検証済み
- テスト: backend 49件、frontend 16件、Playwright 3件が成功。clean DB migration往復、pgvector 0.8.1/vector(32)、Alembic check、Next.js production buildも成功
- GitHub Actions: CAREER-SYSTEMS-V1上の将来対象、初期フェーズでは未作成
- OpenAI API接続: 未承認・未実装
- 外部通信: dependency/Docker image取得のみ実施。外部AI・embedding・動画・字幕API通信は未実施

## 要件状態

受入条件を検証できた要件だけを実装・検証済みとする。一部実装は完成件数へ含めない。

| 分類 | 状態 |
|---|---|
| `SYS-*` | 3件 実装・検証済み |
| `DB-*` | 1件 実装・検証済み |
| `AUTH-*` | 4件 実装・検証済み、2件 一部実装 |
| `VID-*` | 6件 実装・検証済み |
| `ADM-*` | 1件 実装・検証済み |
| `TRN-*` | 5件 実装・検証済み |
| `PRV-*` | 6件 実装・検証済み、1件 未実装 |
| `RAG-*` | 10件 実装・検証済み |
| `HIS-*` | 3件 実装・検証済み |
| `STR-*` | 未実装 |
| `EVAL-*` | 未実装 |
| `SEC-*` | 未実装 |
| `TST-*` | 未実装 |

## Phase 4で実施したこと

- PREMIUM/ADMIN限定の同期question runと、指定教材すべてのbackend認可を実装した。
- cosine distance top_k=5検索と、検索条件・順位・distance・選択状態の保存を実装した。
- bigram overlap 0.20、best distance 0.55、最大3根拠の`evidence-policy-v1`を固定fixtureで検証した。
- `deterministic-local/grounded-extractive-v1`と許可集合外citation拒否を実装した。
- 回答時snapshot、過去字幕version再現、履歴、コピー、feedback、citation seekをAPI/UI/E2Eで検証した。

## 今回実施していないこと

- SSE、AbortControllerによる受信停止、backend cancel、切断区別、非破壊再生成
- fake providerのstream event、遅延、中断scenario
- Phase 6の固定評価run、評価結果管理
- OpenAI SDK導入、API key操作、外部API呼び出し
- GitHub Actions、production deployment
- Phase 4のstage、commit、push、PR

## 要件件数

- 全要件: 62
- 実装・検証済み: 39
- 一部実装: 2（`AUTH-004`, `AUTH-005`）
- 未実装: 21

元経歴には実OpenAI APIを使用した業務経験の記述があるが、このリポジトリでは実OpenAI providerを経験済み、実装済み、検証済みとして記録しない。
