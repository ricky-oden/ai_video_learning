# AI Provider境界

PLAN_VERSION: `AI-LEARNING-V1.0`

## 初期方針

実装対象は決定論的fake providerだけである。OpenAI SDKを依存へ追加せず、API keyを要求・保存・表示せず、実OpenAI APIや外部embedding APIを呼び出さない。

## EmbeddingProvider

責務:

- 正規化済みテキスト列を固定次元vector列へ変換する。
- provider名、version、dimensionsを返す。
- 同一入力とversionに対して別processでも同一結果を返す。

概念契約:

```text
embed(texts, context)
→ vectors
→ provider_name
→ provider_version
→ dimensions
```

入力順と出力順を一致させ、空入力、過大入力、version不一致をtyped errorとして扱う。

## AnswerGenerationProvider

責務:

- Phase 4では質問と認可済み根拠から同期回答を生成する。
- 使用したcitation IDを明示する。
- provider名、versionを返す。
- Phase 5でstream eventと中断signalの境界を拡張する。

概念契約:

```text
generate(question, evidence)
→ body
→ citation_ids
→ provider metadata
```

providerは検索、認可、十分性判定、DB保存を担当しない。

## fake provider

- Phase 3 embeddingは`deterministic-local/hash-char-ngram-v1`、32次元とする。
- 正規化済み文字unigram/bigramをSHA-256で固定bucketへ割り当て、有限vectorへL2正規化する。
- Python組込み`hash()`のようにprocessごとに変わり得るものは使用しない。
- Phase 4回答は`deterministic-local/grounded-extractive-v1`とし、選択済み根拠textを順番どおり決定論的に連結する。
- citationは渡されたIDだけを返せる。
- event分割、遅延、中断点を持つscenario providerはPhase 5で実装する。

## contract test

- 同一入力の決定性
- vector次元と有限値
- 入出力順序
- 根拠集合外citationの禁止
- event sequenceとterminal event
- cancel後にcontentを出さない
- provider errorのアプリ独自errorへの変換

## fake providerで保証できる範囲

- 固定次元と同一入力・versionに対する決定性
- provider interfaceとuse-caseの分離
- pgvector保存・検索までのアプリケーション配線
- 認可済み根拠だけを入力にすること
- 根拠集合外citationの拒否
- 根拠不足・教材外質問でgeneratorを呼ばないこと
- stream event順序、遅延、途中失敗、中断scenario
- 回答、引用、履歴、再生成関係の保存

## fake providerでは保証できない範囲

- 実embeddingの意味的類似度と検索品質
- 実LLMの回答品質、自然さ、推論能力
- 実providerのtokenizer、context制限、finish reason
- rate limit、timeout、provider障害、SDK固有error
- 実APIのstream形式、TTFT、総応答時間
- token使用量、料金、provider側のデータ保持条件

これらをfakeによる検証済み項目として記録しない。

## 実OpenAI provider

未承認の独立フェーズであり、interface名だけを理由にplaceholder SDK、環境変数、API key欄を追加しない。実接続には費用、検証方法、送信データ、支出上限、停止方法の提示と明示承認が必要である。元経歴の記載と、このリポジトリにおける実装・検証実績を混同しない。

対象要件: `PRV-*`, `SEC-001`
