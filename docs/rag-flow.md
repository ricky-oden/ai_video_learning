# RAGフロー

PLAN_VERSION: `AI-LEARNING-V1.0`

## 質問処理

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
→ SSE配信
→ answer・citation・snapshot保存
→ completed
```

## 検索

- query vectorとchunk vectorのprovider version・次元を一致させる。
- SQL条件で教材、公開字幕version、ユーザー権限を絞ったうえで類似検索する。
- `top_k`、距離関数、score threshold、policy versionをretrieval runへ記録する。
- 認可できないchunkを取得後に隠すだけの実装は不可。provider入力にも含めない。

## 根拠十分性

初期判定は決定論的規則と固定fixtureで検証する。候補となる入力は、上位score、条件を満たすchunk数、対象教材、質問と教材語彙の対応である。具体的な数値はfake vectorと評価fixtureを実装した際に固定する。

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
