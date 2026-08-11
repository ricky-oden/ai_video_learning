# システム概要

PLAN_VERSION: `AI-LEARNING-V1.0`

## 学習上の中心導線

```text
Next.js画面
→ FastAPI API
→ 認証・認可
→ use-case/service
→ SQLAlchemy
→ PostgreSQL / pgvector
→ fake provider境界
→ 根拠検証
→ SSE
→ 回答・引用・履歴・評価
```

frontendは画面状態、入力、stream eventの表示、動画位置移動を担当する。backendは入力検証、認証・認可、字幕処理、検索、回答可否、provider呼出し、永続化を担当する。DBはユーザー、token、教材、字幕版、segment、chunk、vector、run、回答、引用、評価を保持する。

## component境界

- `frontend`: Next.js App Router。localStorage tokenをBearer headerへ設定する。
- `backend/api`: FastAPI routerとPydantic schema。
- `backend/application`: 認証、字幕取込、RAG、stream、評価use-case。
- `backend/domain`: 状態遷移、十分性判定、role matrix、provider interface。
- `backend/infrastructure`: SQLAlchemy repository、pgvector検索、fake provider。
- `db`: PostgreSQL 16系、pgvector extension。
- `fixtures`: ローカルデモ動画、字幕、ユーザー、評価ケース。

## roleと主要機能

| 機能 | MEMBER | PREMIUM | ADMIN |
|---|---:|---:|---:|
| ログイン・教材閲覧 | 可 | 可 | 可 |
| AI質問・stream・中断・再生成 | 不可 | 可 | 可 |
| 自分の履歴・回答評価 | 閲覧可能な回答のみ | 可 | 可 |
| 字幕取込 | 不可 | 不可 | 可 |
| 教材・字幕状態確認 | 不可 | 不可 | 可 |
| 評価結果確認 | 不可 | 不可 | 可 |

最終認可は常にbackendで行う。

## data flow上の不変条件

- 検索対象は認可済み教材と公開字幕versionに限定する。
- providerへ渡したchunkだけをcitationとして採用できる。
- 拒否時は生成providerを呼ばない。
- terminal状態後に同じrunを別terminal状態へ変更しない。
- 再生成で元回答を更新しない。
- 過去回答が参照した字幕versionとsnapshotを削除・置換しない。

## 外部境界

初期版に外部サービス境界の実接続はない。ブラウザ、frontend、backend、DB、fixtureのローカル通信だけで完結する。実OpenAI providerは未承認である。
