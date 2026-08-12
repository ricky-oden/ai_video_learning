# API仕様

PLAN_VERSION: `AI-LEARNING-V1.0`

prefixは`/api/v1`とする。Phase 4までに認証、教材、字幕管理、同期question run、履歴、feedback APIを実装済みである。SSE、中断、再生成APIはPhase 5まで追加しない。

## 共通

- 認証: `Authorization: Bearer <opaque-token>`
- error envelope: `{"error":{"code","message","field_errors","conflict"}}`
- 外部APIは呼び出さない。
- 404と403の情報開示方針は、教材・回答所有権を漏らさないようAPI単位で固定する。

## 認証

| method/path | role | 概要 | 要件 |
|---|---|---|---|
| `POST /api/v1/auth/login` | 未認証 | opaque token発行 | AUTH-001 |
| `POST /api/v1/auth/logout` | 認証済み | 現token失効 | AUTH-002 |
| `GET /api/v1/auth/me` | 認証済み | userとrole取得 | AUTH-003 |

`POST /auth/login` responseは`access_token`, `token_type: bearer`, `user`を返す。tokenはJWTではなく推測困難なopaque値とする。

## 教材

| method/path | role | 概要 | 要件 |
|---|---|---|---|
| `GET /api/v1/materials` | 全role | activeかつアクセス可能な教材一覧 | VID-002 |
| `GET /api/v1/materials/{material_id}` | 全role | 教材、local動画path、字幕状態 | VID-003 |

動画はNext.jsの`public/media`配下の固定fixtureを同一originで返す。APIは任意path入力を受け付けない。

## Phase 4同期question run

| method/path | role | 概要 | 要件 |
|---|---|---|---|
| `POST /api/v1/question-runs` | PREMIUM, ADMIN | 同期処理しterminal runを返す | RAG-005〜RAG-010 |
| `GET /api/v1/question-runs/{run_id}` | 所有者/ADMIN | run状態取得 | HIS-001 |
| `GET /api/v1/questions/history` | 認証済み | 自分の履歴 | HIS-001 |
| `POST /api/v1/answers/{answer_id}/feedback` | 回答所有者 | 評価登録/更新 | HIS-003 |

question run request案:

```json
{
  "question": "カラー剤を塗布する順番は？",
  "material_ids": ["material-demo-1"]
}
```

Phase 4 response概要:

```json
{
  "run_id": "uuid",
  "question": "カラー剤を塗布する順番は？",
  "material_ids": ["uuid"],
  "status": "COMPLETED",
  "failure_code": null,
  "answer": {
    "id": "uuid",
    "body": "選択済み根拠だけから構成した回答",
    "provider_name": "deterministic-local",
    "provider_version": "grounded-extractive-v1",
    "citations": []
  }
}
```

Phase 4 terminal statusは`COMPLETED`, `REFUSED_INSUFFICIENT_EVIDENCE`, `REFUSED_OUT_OF_SCOPE`, `FAILED`とする。requestはquestion 1〜500文字、material ID 1〜5件、重複不可で、指定教材すべてをbackendが認可する。

## Phase 5予定API

`GET /api/v1/question-runs/{run_id}/events`、cancel、regenerationは未実装である。Phase 4 responseに`events_url`は含めない。

## 管理者

| method/path | role | 概要 | 要件 |
|---|---|---|---|
| `GET /api/v1/admin/materials` | ADMIN | 教材、current版、状態、件数、provider一覧 | ADM-001 |
| `POST /api/v1/admin/materials/{material_id}/transcript-imports` | ADMIN | 許可済みfixture字幕取込 | TRN-001 |
| `GET /api/v1/admin/materials/{material_id}/transcript-versions` | ADMIN | 教材の字幕version一覧 | TRN-005 |
| `GET /api/v1/admin/transcript-versions/{version_id}` | ADMIN | version状態・件数・provider詳細 | ADM-001 |
| `GET /admin/evaluation-runs` | ADMIN | 評価run一覧 | EVAL-* |
| `GET /admin/evaluation-runs/{id}` | ADMIN | ケース別評価結果 | EVAL-* |

字幕取込は同期処理またはアプリ内jobとして実装し、外部background queue製品を使わない。

## 代表エラー

- `400 validation_error`
- `401 unauthenticated` / `invalid_token`
- `403 forbidden_role` / `material_forbidden`
- `404 not_found`
- `409 invalid_run_state` / `transcript_version_conflict`
- `422 insufficient_evidence`はHTTP errorではなくterminal run状態として扱う
- `500 provider_contract_error` / `internal_error`
