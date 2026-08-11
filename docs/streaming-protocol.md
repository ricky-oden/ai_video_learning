# Streaming Protocol

PLAN_VERSION: `AI-LEARNING-V1.0`

## transport

1. `POST /api/v1/question-runs`でrunを作成する。
2. responseのrun IDを使用し、`GET /api/v1/question-runs/{run_id}/events`をSSEで購読する。
3. frontendはAbortControllerで受信を停止する。
4. 明示中断時は`POST /api/v1/question-runs/{run_id}/cancel`も呼ぶ。

SSE requestでもBearer tokenを送信できるclient方式を選ぶ。標準`EventSource`が任意headerを設定できない制約を踏まえ、fetchによるSSE parsingを初期候補とする。

## event envelope

```json
{
  "run_id": "run_opaque_id",
  "sequence": 4,
  "event_type": "content_delta",
  "data": {}
}
```

- `run_id`: POSTで返したID
- `sequence`: run内で1から単調増加
- `event_type`: 定義済みevent種別
- `data`: event固有payload

## event type

- `run_state`: `retrieving`, `evidence_checking`, `generating`
- `content_delta`: 回答文字列の追加分
- `citation`: citation ID、video ID、start/end ms、snapshot表示情報
- `refused`: `insufficient_evidence`または`out_of_scope`
- `completed`: answer IDとterminal metadata
- `cancelled`: 明示中断完了
- `failed`: 公開可能なerror code
- `heartbeat`: 任意。contentとして扱わない

terminal eventは`completed`, `refused`, `cancelled`, `failed`のいずれか一つだけとする。

## 状態遷移

```text
submitted → retrieving → evidence_checking
evidence_checking → refused
evidence_checking → generating → completed
非terminal状態 → cancelling → cancelled
非terminal状態 → failed
```

## 中断と切断

- AbortControllerはfrontendの受信停止であり、それだけでbackend cancel完了とはみなさない。
- cancel APIが成功した場合を明示中断として記録する。
- network切断は`disconnected_at`を記録できるが、即座にcancelledへしない。
- cancelとcompletedが競合した場合のterminal状態決定はDBの条件付き更新で一度だけ行う。
- cancel後のcontent eventを画面へ反映しない。

## 再接続

初期案では最新run状態をGETし、terminalなら保存済み結果を表示する。非terminal streamのevent replayを必須範囲に含めるかは未確定である。少なくともsequenceにより重複・欠落を検知する。

## 再生成

元answer IDを指定して新question runを作る。元answer、citation、評価を上書きせず、生成後answerの`parent_answer_id`で関係を保持する。

対象要件: `STR-*`, `HIS-001`
