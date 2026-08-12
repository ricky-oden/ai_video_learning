# 画面一覧

PLAN_VERSION: `AI-LEARNING-V1.0`

Phase 4までの`/login`、教材、字幕管理、同期質問、履歴画面は実装済み。stream・中断・再生成と評価結果管理画面は未実装である。

| ID | route | 画面 | role | 状態 | 主な要件 |
|---|---|---|---|---|---|
| SCR-001 | `/login` | ログイン | 未認証 | 実装済み | AUTH-001, AUTH-002, VID-001 |
| SCR-002 | `/materials` | 教材一覧 | 全role | 実装済み | VID-002 |
| SCR-003 | `/materials/[materialId]` | 教材詳細・動画プレイヤー | 全role | 実装済み（citation seek含む） | VID-003〜VID-005 |
| SCR-004 | `/ask` | AI質問 | PREMIUM, ADMIN | 同期式を実装済み（streamはPhase 5） | AUTH-004, RAG-005〜RAG-010 |
| SCR-005 | `/history` | 質問・回答履歴 | 認証済み | terminal履歴・feedbackを実装済み（再生成はPhase 5） | HIS-001〜HIS-003 |
| SCR-006 | `/admin/materials` | 教材・字幕状態 | ADMIN | 実装済み | AUTH-005, ADM-001, TRN-001 |
| SCR-007 | `/admin/evaluations` | 評価結果 | ADMIN | 未実装 | AUTH-005, EVAL-001〜EVAL-008 |

## 主要状態

### AI質問画面

- `idle`: 質問入力可能
- `submitting`: question run作成中
- `retrieving` / `evidence_checking` / `generating`: Phase 5のstream表示で追加予定
- `completed`: 回答、引用、コピー、評価、再生成を表示
- `refused`: 根拠不足または教材外理由を表示
- `cancelling` / `cancelled`: 中断中・中断済み
- `failed`: 再試行可能なエラー表示
- `disconnected`: 通信切断。明示中断とは別表示

### 教材詳細

- 動画fixtureを再生する。
- citationから遷移した場合、対象videoを選び`start_ms`へseekする。
- AI質問への導線はPREMIUM/ADMINだけ表示するが、backend認可を代替しない。

### 管理者画面

- 教材ごとにcurrent version、取込状態、segment、chunk、embedding件数とprovider metadataを表示する。
- 字幕fixture取込を開始できる。
- 評価ケースとrunの指標を確認できる。

## 対象外画面

進捗、視聴完了、ブックマーク、クイズ、アップロード、契約・課金、本番監視の画面は作成しない。
