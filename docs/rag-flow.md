# RAGフロー

PLAN_VERSION: `AI-LEARNING-V1.0`

## 質問処理

Phase 4では同期question run、検索結果保存、十分性判定、根拠限定fake回答、citation検証・保存まで実装済みである。SSE、中断、再生成はPhase 5で追加する。

```text
POST question run
→ token・role検証
→ material access検証
→ 質問保存
→ fake質問embedding
→ 公開字幕version・認可教材に限定したpgvector検索
→ retrieval run/result保存
→ 根拠十分性判定
   ├─ 不足: refused_insufficient_evidence
   ├─ 教材外: refused_out_of_scope
   └─ 十分: 認可済み根拠をfake generatorへ渡す
→ provider citation検証
→ answer・citation・snapshot保存
→ terminal response
```

## 検索

- query vectorとchunk vectorのprovider version・次元を一致させる。
- SQL条件で教材、公開字幕version、ユーザー権限を絞ったうえで類似検索する。
- cosine distance、`top_k=5`、provider metadata、policy versionとthreshold、順位・distance・選択状態をretrieval run/resultへ記録する。
- 認可できないchunkを取得後に隠すだけの実装は不可。provider入力にも含めない。

## 根拠十分性

初期判定`evidence-policy-v1`は正規化済み文字bigram overlapを使う。overlap 0は教材外、overlap ratio 0.20未満またはbest cosine distance 0.55超は根拠不足、両条件を満たす場合は上位最大3chunkを選択する。境界値は人が固定したfixtureで検証し、AIによる自動閾値変更は行わない。

判定結果には次を保存する。

- policy version
- `answerable` boolean
- refusal category
- 使用した検索結果ID
- thresholdや件数などの判定材料

## 回答抑止

- 根拠不足・教材外ではgeneratorを呼ばない。
- 一般知識で補わない。
- 拒否理由を回答本文と混同せずterminal statusとして保存する。
- 閾値をAIが自動変更しない。

## 根拠付き回答

fake generatorへ渡すものは質問、許可済みchunk、citation ID、generation policy versionだけとする。回答は根拠テキストを一定規則で組み立て、各主張に対応するcitationを返す。

生成後にcitation IDがretrieval resultの選択集合へ含まれることを検査する。不整合なら`completed`にせず、`failed`として保存する。

## 再現性

過去のrunから質問、対象教材、query embedding metadata、検索順位、十分性規則、provider version、回答、引用snapshotを再構成できるようにする。

対象要件: `RAG-*`, `PRV-*`, `AUTH-004`, `AUTH-006`
