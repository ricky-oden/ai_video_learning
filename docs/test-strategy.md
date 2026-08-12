# テスト戦略

PLAN_VERSION: `AI-LEARNING-V1.0`

Phase 4までの認証、教材、字幕、embedding、検索、根拠判定、同期回答、citation、履歴・feedbackテストは実装・実行済み。Phase 5のstream、中断、再生成は未実装である。ローカルfixture、fake provider、test PostgreSQL/pgvectorだけで完結し、外部API通信を行わない。

Phase 4実績: backend pytest 49件、frontend Vitest 16件、Playwright 3件。migration clean upgrade/downgrade/再upgrade、pgvector extension/vector(32)、Alembic check、Next.js production buildも成功した。

## frontend: Vitest + React Testing Library

- login成功・失敗、localStorage保存・削除
- role別の表示制御
- 教材一覧・詳細・player state
- citation選択によるvideoとstart_ms指定
- stream event reducer、sequence、未知event
- refused/cancelled/disconnected/failedの区別
- copy、feedback、regenerate操作
- 字幕・回答をHTMLとして注入しないこと

frontend表示テストはbackend認可テストの代わりにしない。

## backend unit: pytest

- opaque token発行、hash照合、期限、失効
- role/resource認可matrix
- 字幕validation、正規化、segment/chunk決定性
- fake embeddingのprocess間決定性と固定次元
- 根拠十分性の境界値
- refusal時にgeneratorを呼ばないこと
- fake回答の根拠限定、citation検証
- run状態遷移、cancel/completed競合
- 評価指標計算

## provider contract: pytest

- `EmbeddingProvider`と`AnswerGenerationProvider`の契約
- 同一入力の同一出力
- vector次元、有限値、順序
- evidence集合外citationの拒否
- event順序、terminal event一つ
- 遅延、途中失敗、中断scenario

## DB/API integration: pytest + PostgreSQL/pgvector

- Alembicによる新規DB構築
- vector保存・類似検索
- 教材・公開字幕version・role filter
- answer/citation snapshotの参照整合性
- token、履歴、評価の所有権
- terminal状態の条件付き更新
- 全APIの正常、401、403、404、409
- 外部networkを拒否するtest fixture

SQLiteでpgvector結合テストを代替しない。

## E2E: Playwright

1. role別loginとlogout
2. 教材一覧から詳細・ローカル動画再生
3. PREMIUM/ADMINの質問、SSE回答、citation位置への移動
4. MEMBERのAI質問拒否
5. 根拠不足と教材外質問の拒否
6. stream中断とcancelled表示
7. network切断と明示中断の表示差
8. 再生成で元回答が残ること
9. 回答copyとfeedback
10. ADMIN字幕取込・状態確認・評価結果、非ADMIN拒否

## 評価回帰

固定dataset versionを用い、Hit@k、動画・字幕範囲、引用整合性、根拠外主張、回答可否、教材外誤回答率、TTFT、総時間、中断・再生成を記録する。MRR/nDCGは必須にしない。

## 完了判定

- 要件IDとtest caseを対応付ける。
- 未実行、skip理由未記録、失敗中の必須testがあれば対象要件を完了にしない。
- test logへtoken、password、字幕外の秘密情報を出力しない。
- OpenAI SDK、API key、外部APIを必要とするtestを作らない。

対象要件: `TST-*`, `SEC-*`および各機能要件の受入条件
