# AI-LEARNING-V1 実装計画

PLAN_VERSION: `AI-LEARNING-V1.0`

## 目的

美容師向け動画教育サービスを題材として、画面からFastAPI、PostgreSQL、pgvector、交換可能なAI provider境界までの一往復を学ぶ。AI生成結果を正解として固定せず、根拠、回答抑止、stream、評価を独立した責務として設計する。

## 現在フェーズ

`Phase 0: 計画固定（初期正本承認済み）`

計画文書は初期正本として承認済みである。全要件は未実装であり、Phase 1の開始には別途ユーザー承認を必要とする。

## 固定技術構成

- Node.js 22系、npm
- Next.js App Router、React、TypeScript
- Python 3.12系
- FastAPI、SQLAlchemy、Alembic
- PostgreSQL 16系、pgvector
- Vitest、React Testing Library、Playwright、pytest
- Docker Compose
- Python依存はruntime用とdevelopment/test用に分離する

## アーキテクチャ原則

1. frontend、backend、databaseの責務を分離する。
2. backendが認証・認可の最終判断を行う。
3. ローカルデモ教材と字幕fixtureだけを使用する。
4. 初期AI処理は決定論的fake providerだけを使用する。
5. `EmbeddingProvider`と`AnswerGenerationProvider`を分離する。
6. 生成前に根拠十分性と教材範囲を判定する。
7. 回答と引用は字幕版、chunk、動画、再生位置、回答時スナップショットまで追跡可能にする。
8. streamの受信停止とbackendの生成中断を分け、切断と明示中断も区別する。
9. 評価ケースは人が定義し、生成回答を正解データとして循環利用しない。

## 実装フェーズ

### Phase 0: 計画固定

- 本文書、要件、設計、状態、決定記録を確定する。
- 完了条件: 文書間の要件対応が確認され、ユーザーが実装開始を承認する。

### Phase 1: 開発基盤

- Next.js/FastAPIの最小構成、依存分離、Docker Compose、PostgreSQL/pgvector、Alembicを構築する。
- 対象: `SYS-*`, `DB-*`
- 完了条件: healthcheck、migration、空のfrontend/backend testが再現可能に実行できる。

### Phase 2: 認証と通常動画導線

- opaque Bearer token、教材一覧・詳細、プレイヤーUI、指定位置遷移、管理者状態確認を実装する。
- 対象: `AUTH-*`, `VID-*`, `ADM-001`
- 完了条件: MEMBER/PREMIUM/ADMINの許可・拒否をbackendテストとE2Eで確認する。

### Phase 3: 字幕取込とfake embedding

- fixture取込、正規化、segment、chunk、固定次元fake embedding、pgvector保存を実装する。
- 対象: `TRN-*`, `PRV-001`〜`PRV-004`, `RAG-001`〜`RAG-004`
- 完了条件: 同一入力が同一vectorになり、字幕版と時間範囲を失わず検索できる。

### Phase 4: 根拠付き質問応答

- 類似検索、十分性判定、回答抑止、fake回答、回答・引用・履歴保存を実装する。
- 対象: `RAG-005`〜`RAG-010`, `HIS-*`, `PRV-005`〜`PRV-007`
- 完了条件: 回答可能、根拠不足、教材外の各fixtureが期待状態になる。

### Phase 5: streaming、中断、再生成

- question run作成、SSE、AbortController、cancel API、切断区別、非破壊再生成を実装する。
- 対象: `STR-*`
- 完了条件: event順序、中断、切断、再生成履歴をAPI/E2Eテストで確認する。

### Phase 6: 初期評価と総合検証

- 固定評価セット、初期指標、権限・RAG・streamの総合テストを実装する。
- 対象: `EVAL-*`, `TST-*`, `SEC-*`
- 完了条件: 必須指標が記録され、未実行または失敗した検証を完了扱いにしない。

### 未承認フェーズ: 実OpenAI provider

初期計画には含めない。費用、支出上限、データ送信範囲、秘密情報管理、停止方法、fakeとの差分検証を提示し、ユーザーの明示承認を得た場合にだけ計画変更として扱う。

## 対象外

- 学習進捗率、視聴完了、ブックマーク、教材クイズ
- 動画アップロード、CDN、外部動画配信、外部字幕API
- 課金・契約処理
- 実OpenAI API、外部embedding API、OpenAI SDK
- background queue製品、複数言語
- 本番監視、本番デプロイ
- 自動改善、AIによるprompt・閾値の自動書換え

## 初期フェーズでは作成しない将来対象

GitHub Actionsは`CAREER-SYSTEMS-V1`上の将来対象として維持する。現時点ではworkflowを作成せず、実装・ローカル検証の安定後に独立して計画する。作成する場合も当初は`workflow_dispatch`だけとし、無料枠、支出上限、実行内容を確認するまでpushやpull requestを契機とする自動トリガーを有効化しない。

## 変更管理

`CAREER-SYSTEMS-V1`または本文書の承認済み計画を変更する場合だけ`PROPOSED_CHANGE`を使用する。通常の詳細設計や、承認済み要件を満たす実装判断には使用しない。変更は差分、理由、影響、代替案を示し、承認後に`decision-log.md`とPLAN_VERSIONを更新する。
