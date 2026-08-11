# AI-LEARNING-V1

美容師向け動画教育・AI学習支援サービスを題材に、通常の動画学習機能と、根拠付きRAGの処理境界を学ぶためのリポジトリです。

現在の計画バージョンは `AI-LEARNING-V1.0` です。現時点では計画文書のみが存在し、アプリケーション、依存関係、Docker、migration、CIは未実装です。

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
