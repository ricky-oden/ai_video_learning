# 字幕処理パイプライン

PLAN_VERSION: `AI-LEARNING-V1.0`

## 入力

リポジトリ内のJSON字幕fixtureだけを入力とする。外部動画・字幕API、upload service、background queue製品は使用しない。fixture IDはbackendの許可済みmappingから解決し、任意pathとして扱わない。

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

- `normalization_version = nfkc-whitespace-v1`
- Unicode NFKC
- 改行、tab、連続空白を半角空白一つへ統一
- 前後空白を除去
- 元テキストは変更せず別列に保存

句読点の追加、誤字訂正、複数言語変換など意味を変更し得る処理は初期範囲に含めない。正規化規則には`normalization_version`を付ける。

## segment

- `sequence`で原順序を保持する。
- `start_ms`と`end_ms`を整数で保存する。
- `0 <= start_ms < end_ms`を必須とする。
- sequenceは1から連続し、次segmentの開始は前segmentの終了以上とする。
- 空白だけのtext、重複時間、不正時刻は全件検証後に拒否する。

## chunk

- `chunking_version = segment-window-3-overlap-1-v1`
- 最大3segment、次chunkと1segment重複とし、segment境界を分割しない。
- `first_segment_sequence`と`last_segment_sequence`を持つ。
- `start_ms`は最初のsegment、`end_ms`は最後のsegmentから導出する。
- 同一入力・設定で同じchunkになる決定論的規則を使用する。
- chunk長、overlap、区切り規則を`chunking_version`へ対応付ける。
- 空の末尾chunkを作らず、AIによる自動変更は行わない。

## embedding

- 固定次元のfake embeddingだけを使用する。
- `provider_name`, `provider_version`, `dimensions`を保存する。
- Python process依存のランダムhashは使用せず、安定したalgorithmからvectorを作る。
- chunkと質問は同じnormalization/provider versionを使用する。

## 管理者が確認する状態

- `NOT_IMPORTED`, `PROCESSING`, `READY`, `FAILED`
- segment/chunk/embedding件数
- normalization/chunking/provider version
- failure codeと秘密情報を含まない概要

対象要件: `TRN-*`, `RAG-001`, `ADM-001`, `PRV-003`, `PRV-004`
