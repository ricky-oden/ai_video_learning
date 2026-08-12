# 実装状態

PLAN_VERSION: `AI-LEARNING-V1.0`

最終更新日: 2026-08-12

## 現在フェーズ

`Phase 2: 認証と通常動画導線（実装・検証済み・Phase 3未承認）`

## 全体状態

- 計画文書: `AI-LEARNING-V1.0`初期正本として承認済み
- アプリケーション: Phase 2の認証と通常動画導線まで実装済み
- frontend: login、認証復元、教材一覧・詳細、local動画、指定位置UI、ADMIN状態画面を実装・検証済み
- backend: opaque session、role認可、教材API、ADMIN教材状態APIを実装・検証済み
- database / migration: users、auth_sessions、materialsとpgvector extensionをAlembic管理し検証済み
- Docker Compose: frontend/backend/db/test-dbに加え、profile付きPlaywright runnerを実装・検証済み
- テスト: backend 22件、frontend 9件、Playwright 1件が成功。Phase 3以降は未実装
- GitHub Actions: CAREER-SYSTEMS-V1上の将来対象、初期フェーズでは未作成
- OpenAI API接続: 未承認・未実装
- 外部通信: dependency/Docker image取得のみ実施。外部AI・embedding・動画・字幕API通信は未実施

## 要件状態

受入条件を検証できた要件だけを実装・検証済みとする。一部実装は完成件数へ含めない。

| 分類 | 状態 |
|---|---|
| `SYS-*` | 3件 実装・検証済み |
| `DB-*` | 1件 実装・検証済み |
| `AUTH-*` | 4件 実装・検証済み、2件 未実装 |
| `VID-*` | 5件 実装・検証済み、1件 一部実装 |
| `ADM-*` | 1件 一部実装 |
| `TRN-*` | 未実装 |
| `PRV-*` | 未実装 |
| `RAG-*` | 未実装 |
| `HIS-*` | 未実装 |
| `STR-*` | 未実装 |
| `EVAL-*` | 未実装 |
| `SEC-*` | 未実装 |
| `TST-*` | 未実装 |

## Phase 2で実施したこと

- Argon2id password、SHA-256 hashだけを保存する8時間opaque session、再login/logout revoke、inactive拒否を実装した。
- MEMBER/PREMIUM/ADMINの教材role matrixをbackendで強制した。
- localStorage認証復元、Bearer付加、401削除、login/logout UIを実装した。
- local fixture 3教材、HTML video、指定位置UI、ADMINの`NOT_IMPORTED`状態確認を実装した。
- PostgreSQL migration、seed冪等性、Vitest、pytest、Playwright主要導線を検証した。

## 今回実施していないこと

- 字幕取込、segment、chunk、embedding、RAG、question/answer、SSE、fake provider
- OpenAI SDK導入、API key操作、外部API呼び出し
- GitHub Actions、production deployment
- Phase 2のstage、commit、push、PR

## 要件件数

- 全要件: 62
- 実装・検証済み: 13
- 一部実装: 2（`VID-005`, `ADM-001`）
- 未実装: 47

元経歴には実OpenAI APIを使用した業務経験の記述があるが、このリポジトリでは実OpenAI providerを経験済み、実装済み、検証済みとして記録しない。
