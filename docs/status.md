# 実装状態

PLAN_VERSION: `AI-LEARNING-V1.0`

最終更新日: 2026-08-12

## 現在フェーズ

`Phase 1: 開発基盤（実装・検証済み・Phase 2未承認）`

## 全体状態

- 計画文書: `AI-LEARNING-V1.0`初期正本として承認済み
- アプリケーション: Phase 1基盤のみ実装済み
- frontend: Next.js基盤、共通状態、404、同一origin API転送を実装・検証済み
- backend: FastAPI、DB-backed health、共通API errorを実装・検証済み
- database / migration: PostgreSQL 16 + pgvector extension migrationを実装・検証済み
- Docker Compose: frontend/backend/db/test-dbを実装・検証済み
- テスト: Phase 1基盤テストのみ実装・成功。Phase 2以降は未実装
- GitHub Actions: CAREER-SYSTEMS-V1上の将来対象、初期フェーズでは未作成
- OpenAI API接続: 未承認・未実装
- 外部通信: dependency/Docker image取得のみ実施。外部AI・embedding・動画・字幕API通信は未実施

## 要件状態

`docs/requirements.md`に定義された全要件は未実装である。文書が存在することは、機能の実装完了または受入条件の検証完了を意味しない。

| 分類 | 状態 |
|---|---|
| `SYS-*` | 3件 実装・検証済み |
| `DB-*` | 1件 実装・検証済み |
| `AUTH-*` | 未実装 |
| `VID-*` | 未実装 |
| `ADM-*` | 未実装 |
| `TRN-*` | 未実装 |
| `PRV-*` | 未実装 |
| `RAG-*` | 未実装 |
| `HIS-*` | 未実装 |
| `STR-*` | 未実装 |
| `EVAL-*` | 未実装 |
| `SEC-*` | 未実装 |
| `TST-*` | 未実装 |

## 今回実施したこと

- Node.js 22.23.2 / Next.js App Routerのfrontend基盤を構築した。
- Python 3.12.13 / FastAPI / SQLAlchemy / Alembicのbackend基盤を構築した。
- PostgreSQL 16 + pgvector 0.8.1の開発DBとtest DBを分離した。
- pgvector extensionのupgrade、vector型、downgrade、再upgrade、Alembic checkをclean test DBで検証した。
- Vitest、ESLint、Prettier、TypeScript、Next.js build、pytest、Ruffを実行した。
- frontend/backend/DB health、Next.js同一origin health、非root user、runtime依存分離を検証した。

## 今回実施していないこと

- User/Token/認証、動画、字幕、chunk、embedding、RAG、question/answer、SSE、fake provider
- OpenAI SDK導入、API key操作、外部API呼び出し
- GitHub Actions、production deployment
- stage、commit、push、PR

## 要件件数

- 全要件: 62
- 実装・検証済み: 4（`SYS-001`〜`SYS-003`, `DB-001`）
- 未実装: 58

元経歴には実OpenAI APIを使用した業務経験の記述があるが、このリポジトリでは実OpenAI providerを経験済み、実装済み、検証済みとして記録しない。
