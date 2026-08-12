# AI-LEARNING-V1

美容師向け動画教育・AI学習支援サービスを題材に、通常の動画学習機能と、根拠付きRAGの処理境界を学ぶためのリポジトリです。

現在の計画バージョンは `AI-LEARNING-V1.0` です。Phase 3の字幕取込、決定論的fake embedding、pgvector検索境界まで実装・検証済みです。質問回答、根拠判定、citation、streamは未実装です。

## 固定runtime

- Node.js `22.23.2`、npm `10.9.8`
- Python `3.12.13`
- PostgreSQL 16 + pgvector `0.8.1`
- frontend `http://localhost:3001`
- backend `http://localhost:8003`
- ブラウザのAPI入口 `/api/v1`（Next.jsからCompose内`backend:8000`へ転送）

## 初期スコープ

- ログイン、教材一覧・詳細、動画プレイヤーUI、指定再生位置への移動
- 質問・回答履歴、回答評価、管理者向け教材・字幕状態確認
- ローカルデモ教材と字幕fixture
- 決定論的fake embeddingとfake回答生成
- PostgreSQL 16系とpgvectorを利用する根拠付きRAG
- 根拠不足・教材外質問の回答抑止
- run IDとSSEによる回答stream、中断、再生成
- 検索、根拠、抑止、応答時間、操作成功の評価

OpenAI API、外部embedding API、外部動画・字幕APIは初期スコープに含みません。OpenAI SDKやAPI keyも使用しません。

## 起動

```bash
docker compose config
docker compose build frontend backend
docker compose up -d --wait db
docker compose run --rm backend alembic upgrade head
docker compose up -d --wait backend frontend
docker compose ps
```

DB portはhostへ公開しません。開発DB `ai_video_learning`はnamed volumeへ保存されます。

## Phase 2 demo

```bash
docker compose run --rm backend python -m app.seed
```

共通passwordは学習用fixtureの`Learning123!`です。emailは`member@example.com`、`premium@example.com`、`admin@example.com`、inactive確認用`inactive@example.com`です。教材と動画はリポジトリ内fixtureだけを使用します。

ADMINは`/admin/materials`から許可済みJSON字幕fixtureを取り込めます。入力されたfixture IDはbackendの固定mappingで解決され、任意ファイルパスとして扱いません。embeddingは外部APIを使わない32次元の`deterministic-local/hash-char-ngram-v1`です。

tokenは8時間有効なopaque値で、DBにはSHA-256 hashだけを保存します。frontendは学習目的でtokenをlocalStorageへ保存するため、XSSがあるとtokenを読み取られるリスクがあります。本番用認証方式ではありません。

## test DBとbackend検証

test DBはprofile付きtmpfsで、`test-db:5432/ai_video_learning_test`以外をpytestに許可しません。pytest開始時に`TEST_DATABASE_URL`を検証し、その値をアプリ本体の`DATABASE_URL`へ強制設定します。開発DBへのfallbackはありません。

```bash
docker compose --profile test up -d --wait test-db
docker compose run --rm \
  -e TEST_DATABASE_URL=postgresql+psycopg://ai_learning_test:test-only@test-db:5432/ai_video_learning_test \
  backend pytest
docker compose run --rm backend ruff check .
docker compose run --rm backend ruff format --check .
```

test DBへmigrationを適用する場合も、接続先を明示します。

```bash
docker compose run --rm \
  -e DATABASE_URL=postgresql+psycopg://ai_learning_test:test-only@test-db:5432/ai_video_learning_test \
  backend alembic upgrade head
```

## frontend検証

```bash
docker compose exec -T frontend npm test
docker compose exec -T frontend npm run lint
docker compose exec -T frontend npm run format:check
docker compose exec -T frontend npm run typecheck
docker build --target build --tag ai-video-learning-frontend-build-audit ./frontend
docker compose --profile e2e run --rm e2e
```

稼働中のNext.js dev serverと同じ`.next`へproduction buildを同時出力しないため、buildは隔離したDocker build stageで検証します。

## healthcheck

- direct backend: `http://localhost:8003/api/v1/health`
- Next.js同一origin: `http://localhost:3001/api/v1/health`

成功時はDBへの`SELECT 1`を含めて次を返します。

```json
{"status":"ok","database":"ok"}
```

## 停止

```bash
docker compose --profile test down
```

開発DBのnamed volumeを削除する`down -v`は、明示的に初期化したい場合だけ使用してください。

## 計画文書

- [実装計画](docs/implementation-plan.md)
- [要件と受入条件](docs/requirements.md)
- [状態](docs/status.md)
- [決定記録](docs/decision-log.md)
- [システム概要](docs/system-overview.md)
- [画面一覧](docs/screen-list.md)
- [API仕様](docs/api-specification.md)
- [データモデル](docs/data-model.md)
- [認証・認可](docs/authentication-authorization.md)
- [字幕処理](docs/transcript-pipeline.md)
- [RAGフロー](docs/rag-flow.md)
- [provider境界](docs/provider-boundary.md)
- [streaming protocol](docs/streaming-protocol.md)
- [評価戦略](docs/evaluation-strategy.md)
- [テスト戦略](docs/test-strategy.md)
