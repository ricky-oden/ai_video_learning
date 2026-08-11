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
