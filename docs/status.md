# 実装状態

PLAN_VERSION: `AI-LEARNING-V1.0`

最終更新日: 2026-08-12

## 現在フェーズ

`Phase 3: 字幕取込とfake embedding（実装・検証済み・Phase 4未承認）`

## 全体状態

- 計画文書: `AI-LEARNING-V1.0`初期正本として承認済み
- アプリケーション: Phase 3の字幕取込とfake embedding、検索service境界まで実装済み
- frontend: ADMIN字幕取込、READY/FAILED/current version、件数、provider metadata表示を追加・検証済み
- backend: JSON fixture validation、NFKC/空白正規化、chunk、決定論的32次元embedding、認可済みpgvector検索を実装・検証済み
- database / migration: version/segment/chunk/vector(32)を追加し、旧version保持とcurrent一意制約をAlembic管理・検証済み
- Docker Compose: frontend/backend/db/test-dbに加え、profile付きPlaywright runnerを実装・検証済み
- テスト: backend 38件、frontend 9件、Playwright 2件が成功。Phase 4以降は未実装
- GitHub Actions: CAREER-SYSTEMS-V1上の将来対象、初期フェーズでは未作成
- OpenAI API接続: 未承認・未実装
- 外部通信: dependency/Docker image取得のみ実施。外部AI・embedding・動画・字幕API通信は未実施

## 要件状態

受入条件を検証できた要件だけを実装・検証済みとする。一部実装は完成件数へ含めない。

| 分類 | 状態 |
|---|---|
| `SYS-*` | 3件 実装・検証済み |
| `DB-*` | 1件 実装・検証済み |
| `AUTH-*` | 4件 実装・検証済み、1件 一部実装、1件 未実装 |
| `VID-*` | 5件 実装・検証済み、1件 一部実装 |
| `ADM-*` | 1件 実装・検証済み |
| `TRN-*` | 4件 実装・検証済み、1件 一部実装 |
| `PRV-*` | 2件 実装・検証済み、2件 一部実装、3件 未実装 |
| `RAG-*` | 4件 実装・検証済み、6件 未実装 |
| `HIS-*` | 未実装 |
| `STR-*` | 未実装 |
| `EVAL-*` | 未実装 |
| `SEC-*` | 未実装 |
| `TST-*` | 未実装 |

## Phase 3で実施したこと

- 許可済みmappingから解決するJSON字幕fixture、全件validation、original text保持を実装した。
- `nfkc-whitespace-v1`正規化と`segment-window-3-overlap-1-v1`chunkを実装した。
- `deterministic-local/hash-char-ngram-v1`の32次元fake embeddingをinterface越しに実装した。
- PROCESSING作成、内容transaction、FAILED記録transaction、成功時current切替を実装した。
- READY/current/教材roleで絞るpgvector検索serviceとADMIN API/UIを実装した。

## 今回実施していないこと

- question/answer、十分性判定、citation、SSE、中断、履歴、回答生成provider
- OpenAI SDK導入、API key操作、外部API呼び出し
- GitHub Actions、production deployment
- Phase 3のstage、commit、push、PR

## 要件件数

- 全要件: 62
- 実装・検証済み: 24
- 一部実装: 5（`AUTH-005`, `VID-005`, `TRN-005`, `PRV-002`, `PRV-004`）
- 未実装: 33

元経歴には実OpenAI APIを使用した業務経験の記述があるが、このリポジトリでは実OpenAI providerを経験済み、実装済み、検証済みとして記録しない。
