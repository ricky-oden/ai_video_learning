# Decision Log

PLAN_VERSION: `AI-LEARNING-V1.0`

## DEC-001: 学習用初期スコープの固定

- 日付: 2026-08-10
- 状態: 承認済み
- 決定者: ユーザー
- 背景: 元経歴と初期調査案には本番規模の機能が含まれていたため、学習用リポジトリの完成範囲を限定する必要があった。
- 決定:
  - PLAN_VERSIONを`AI-LEARNING-V1.0`とする。
  - 通常動画機能をログイン、教材一覧・詳細、プレイヤーUI、指定位置遷移、履歴、回答評価、管理者状態確認に限定する。
  - opaque Bearer tokenをDBとfrontend localStorageに保存し、backendで最終認可する。
  - MEMBER、PREMIUM、ADMINを区別する。
  - AI質問はPREMIUMとADMIN、字幕取込と評価結果確認はADMINだけに許可する。
  - ローカル教材・字幕fixtureだけを使用する。
  - 初期providerは決定論的fakeだけとし、実OpenAI providerを未承認フェーズに分離する。
  - 初期評価指標からMRR、nDCGを必須完成条件から外す。
- 影響: 外部通信と従量課金なしで、通常機能、RAG、根拠、抑止、stream、評価の境界を学習できる。

## DEC-002: PROPOSED_CHANGEの使用範囲

- 日付: 2026-08-10
- 状態: 承認済み
- 決定者: ユーザー
- 決定: `PROPOSED_CHANGE`は`CAREER-SYSTEMS-V1`または承認済み`AI-LEARNING-V1.0`計画を変更する場合だけ使用し、通常の初期設計案には使用しない。

## DEC-003: AI-LEARNING-V1.0初期正本の承認

- 日付: 2026-08-10
- 状態: 承認済み
- 決定者: ユーザー
- 決定:
  - 現在の計画文書を`AI-LEARNING-V1.0`の初期正本とする。
  - GitHub Actionsは`CAREER-SYSTEMS-V1`の将来対象から削除せず、初期フェーズでは作成しない。
  - 実OpenAI providerは未承認の独立フェーズとして残す。
  - 元経歴に実OpenAI APIの記載があっても、このリポジトリで経験済み・実装済み・検証済みとは記録しない。
  - fake providerで保証できない項目を検証済みと記録しない。

## 未承認事項

- 実OpenAI provider、OpenAI SDK、外部embedding API
- 外部動画・字幕サービス
- 課金、本番監視、本番デプロイ
- 初期対象外機能の追加

## DEC-004: Phase 1開発基盤の固定versionと構成

- 日付: 2026-08-12
- 状態: 承認・検証済み
- 決定者: ユーザー（固定値）、Codex（承認範囲内の依存patch version固定）
- 対象要件: `SYS-001`, `SYS-002`, `SYS-003`, `DB-001`
- Docker image:
  - `node:22.23.2-alpine`（resolved digest `sha256:c610fcdfb1d5b4740dd70c284ed3cb16bb857e0f7166196e36a5501df7a3aa32`）
  - `python:3.12.13-slim`（resolved digest `sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36`）
  - `pgvector/pgvector:0.8.1-pg16-trixie`（resolved digest `sha256:1e4956185a7fd9306a41ee759a7b4329c4faf9a2bb91a1d01437310c97002433`）
- frontend runtime依存:
  - Next.js 16.3.0、React/React DOM 19.2.8
- frontend development/test依存:
  - TypeScript 5.9.3、Vitest 4.1.10、Playwright 1.58.2
  - React Testing Library 16.3.2、jest-dom 7.0.1、jsdom 29.1.1
  - ESLint 9.39.5、eslint-config-next 16.3.0、Prettier 3.9.6
  - `@types/node` 22.20.1、`@types/react` 19.2.18、`@types/react-dom` 19.2.4
  - transitive依存は`frontend/package-lock.json`で固定する。
- backend runtime依存:
  - FastAPI 0.141.1、Starlette 1.6.0、Uvicorn 0.52.1
  - Pydantic 2.13.4、pydantic-settings 2.15.0、pydantic-core 2.46.4
  - SQLAlchemy 2.0.52、Alembic 1.19.1
  - psycopg/psycopg-binary 3.3.4、pgvector 0.4.2、numpy 2.5.2
  - その他runtime transitive依存も`backend/requirements.txt`へ完全固定する。
- backend development/test依存:
  - pytest 9.1.1、Ruff 0.16.2、httpx2/httpcore2 2.7.0
  - その他development/test transitive依存も`backend/requirements-dev.txt`へ完全固定する。
- Compose:
  - project `ai-video-learning`
  - frontend `3001:3000`、backend `8003:8000`、DB host port非公開
  - 開発DB `db:5432/ai_video_learning`はnamed volume
  - test DB `test-db:5432/ai_video_learning_test`はprofile + tmpfs
  - frontend/backendは非root user
- migration: Alembicでpgvector extensionを作成・削除し、業務tableは作成しない。
- 理由: Phase 1を再現可能にし、Phase 2以降の業務機能や外部providerを混入させないため。

## DEC-005: Phase 2認証・local教材実装

- 日付: 2026-08-12
- 状態: 承認・検証済み
- 決定者: ユーザー（要件）、Codex（承認範囲内の実装詳細）
- 認証:
  - email unique、Argon2id password hash
  - 32-byte相当のopaque tokenを発行し、DBにはSHA-256 hashだけを保存
  - 有効期限8時間、同一userの未revoke sessionは1件、再login/logoutでrevoke
  - frontend localStorage保存、Bearer自動付加、401時削除
- 教材: `materials` tableにlocal fixture pathを保持し、MEMBER/PREMIUM/ADMINのaccessをbackendで判定する。
- fixture: active MEMBER、active PREMIUM、inactiveの3教材と、4つのlocal demo userを冪等seedする。
- Docker image: Playwright runner `mcr.microsoft.com/playwright:v1.58.2-noble`（digest `sha256:6446946a1d9fd62d9ae501312a2d76a43ee688542b21622056a372959b65d63d`）。
- 追加runtime依存: argon2-cffi 25.1.0、argon2-cffi-bindings 25.1.0、cffi 2.0.0、pycparser 3.0、email-validator 2.3.0、dnspython 2.8.0。すべて`backend/requirements.txt`へ固定する。
- 境界: `VID-005`のcitation起点E2Eと`ADM-001`の字幕version/segment/chunk/embedding状態は後続Phaseまで完成扱いにしない。
- 外部性: dependency/image取得以外の外部通信はなく、AI・embedding・動画・字幕APIおよび従量課金は使用しない。

## DEC-006: Phase 3字幕versionと決定論的fake embedding

- 日付: 2026-08-12
- 状態: 承認・検証済み
- 決定者: ユーザー（固定仕様）、Codex（承認範囲内の実装詳細）
- 字幕fixture: JSON形式、backend許可済みID mapping、MEMBER/PREMIUM正常fixtureと不正fixture。
- 正規化: `nfkc-whitespace-v1`。NFKC、空白統一、trimだけを行いoriginal textを保持する。
- chunk: `segment-window-3-overlap-1-v1`。最大3segment、1segment overlap、segment境界非分割。
- embedding: `deterministic-local/hash-char-ngram-v1`、32次元。文字unigram/bigramとSHA-256固定bucketを使用し、組込み`hash()`を使用しない。
- transaction: PROCESSING versionを先に作成し、segment/chunk/embeddingを一つのtransactionで保存する。失敗内容をrollback後、安全な別transactionでFAILEDを記録する。
- version: 再取込は新versionとし、成功時だけcurrentを切り替える。失敗時は旧currentを維持する。
- 検索境界: 質問を同じfake空間へ変換し、READY/current、active教材、role、指定教材をSQL条件で絞ってpgvector検索する。
- Phase境界: AnswerGenerationProviderはinterfaceのみ。回答、十分性判定、citation、run保存、SSEは作成しない。
- 外部性: OpenAI SDK/API keyおよび外部AI・embedding・字幕API通信はない。

## DEC-007: Phase 4同期式根拠付き質問応答

- 日付: 2026-08-12
- 状態: 承認・検証済み
- 決定者: ユーザー（固定仕様）、Codex（承認範囲内の実装詳細）
- API: `POST /api/v1/question-runs`はPhase 4では同期完了後のterminal状態を返し、SSE endpoint、`events_url`、cancel、再生成を追加しない。
- 検索: Phase 3と同じ`deterministic-local/hash-char-ngram-v1` 32次元、cosine distance、`top_k=5`。READY/currentかつ指定・認可済み教材だけをSQLで検索する。
- 十分性: `evidence-policy-v1`。正規化済み文字bigram overlap 0は教材外、overlap ratio 0.20未満またはbest cosine distance 0.55超は根拠不足、選択根拠は最大3chunkとする。人が固定したfixtureが境界値を満たしたため初期目安から閾値を変更していない。
- 回答: `deterministic-local/grounded-extractive-v1`。選択済みchunk textだけを決定論的に連結しcitation IDを返す。許可集合外citationはrunをFAILEDにし、completed answerを保存しない。
- 保持: 検索条件、provider metadata、順位・distance・選択、字幕version、chunk、material、local video path、時刻、text snapshotを保存し、新字幕公開後も旧citationを再現する。
- frontend: `/ask`と`/history`、terminal状態別表示、完了回答コピー、citation seek、所有者feedbackを実装する。MEMBERはUIと直接APIの双方で質問不可。
- 外部性: OpenAI SDK/API key、外部AI・embedding・動画・字幕API通信、SSEは追加しない。依存versionの追加変更はない。
