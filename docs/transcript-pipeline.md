# 字幕処理パイプライン

PLAN_VERSION: `AI-LEARNING-V1.0`

## 入力

リポジトリ内の字幕fixtureだけを入力とする。外部動画・字幕API、upload service、background queue製品は使用しない。fixture形式とschemaは実装フェーズで一つに固定する。

## 処理順

```text
ADMIN取込要求
→ fixture IDと動画の検証
→ transcript version作成（processing）
→ syntax・時刻・sequence検証
→ original text保持
→ version付き正規化
→ segment保存
→ version付きchunk作成
→ fake embedding生成
→ pgvector保存
→ 件数・制約・次元を検証
→ transcript version公開（ready）
```

途中で失敗したversionは`failed`とし、検索対象にしない。再実行で公開済みversionを上書きせず、新versionまたは明示された安全な再試行単位を使用する。

## 正規化

初期候補:

- 改行・連続空白を一つの空白へ正規化
- Unicode normalization規則を固定
- 空segmentの除外
- 元テキストは変更せず別列に保存

句読点の追加、誤字訂正、複数言語変換など意味を変更し得る処理は初期範囲に含めない。正規化規則には`normalization_version`を付ける。

## segment

- `sequence`で原順序を保持する。
- `start_ms`と`end_ms`を整数で保存する。
- `0 <= start_ms < end_ms`を必須とする。
- 重複・隣接を許すかはfixture schema確定時に決め、テストで固定する。

## chunk

- segment境界を追跡できるよう`first_segment_id`と`last_segment_id`を持つ。
- `start_ms`は最初のsegment、`end_ms`は最後のsegmentから導出する。
- 同一入力・設定で同じchunkになる決定論的規則を使用する。
- chunk長、overlap、区切り規則を`chunking_version`へ対応付ける。
- 初期値は評価fixtureを作成してから固定する。AIによる自動変更は行わない。

## embedding

- 固定次元のfake embeddingだけを使用する。
- `provider_name`, `provider_version`, `dimensions`を保存する。
- Python process依存のランダムhashは使用せず、安定したalgorithmからvectorを作る。
- chunkと質問は同じnormalization/provider versionを使用する。

## 管理者が確認する状態

- `pending`, `processing`, `ready`, `failed`
- segment/chunk/embedding件数
- normalization/chunking/provider version
- failure codeと秘密情報を含まない概要

対象要件: `TRN-*`, `RAG-001`, `ADM-001`, `PRV-003`, `PRV-004`
