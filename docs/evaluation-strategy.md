# 評価戦略

PLAN_VERSION: `AI-LEARNING-V1.0`

## 原則

- 評価ケースと期待値は人が定義し、版管理する。
- AIまたはfakeが生成した回答を自動的に正解へ採用しない。
- 検索、根拠、抑止、生成、stream性能、操作を分離して記録する。
- 初期評価はローカルfixtureとfake providerだけで完結する。

## 評価ケース

各ケースは次を持つ。

- 質問と対象教材
- 回答可能/回答不可
- 教材内/教材外
- 期待video ID
- 期待segment/chunkまたはstart/end ms
- 必須事実
- 根拠にないため述べてはいけない主張
- cancel/regeneration用scenario

## 必須指標

### 検索Hit@k

期待chunkが検索上位k件に一つ以上含まれるかをケースごとに記録する。初期kは評価fixtureとともに固定する。

### 期待動画・字幕範囲との一致

video IDの完全一致と、期待時間範囲に対する取得・引用範囲の重なりを記録する。

### 引用整合性

citation ID、chunk、字幕version、動画、時刻、text snapshotが同じ検索runと整合するかを検証する。

### 根拠外主張

固定された必須事実・禁止主張と引用テキストを用いて確認する。初期fakeでは決定規則による自動検査を中心とし、人手確認欄も残す。

### 回答可否

期待answerabilityとシステム判定を比較し、TP/FP/TN/FNを記録する。

### 教材外誤回答率

`教材外なのにcompleted answerとなった件数 / 教材外ケース数`を記録する。

### TTFTと総応答時間

- TTFT: question run作成開始から最初の`content_delta`まで
- 総応答時間: 開始からterminal eventまで

fake delay条件と実測値を分けて記録する。

### 中断・再生成

- 中断後にcompleted answerを残さないこと
- provider処理が中断を観測すること
- 再生成で元answer/citationが保持されること

## 必須でない将来候補

MRR、nDCG、citation precision/recall、p50/p95集計は設計候補として残すが、`AI-LEARNING-V1.0`の完成条件にはしない。

## 合否

具体的な数値閾値はfake embedding、chunk規則、評価fixtureを同時に確認して固定する。AIが閾値やpromptを自動変更する処理は実装しない。失敗または未実行の必須評価を成功扱いにしない。

対象要件: `EVAL-*`
