# API仕様案

PLAN_VERSION: `AI-LEARNING-V1.0`

全APIは未実装。prefixは`/api/v1`とする案で、承認済み要件の範囲内で詳細設計時にschemaを固定する。

## 共通

- 認証: `Authorization: Bearer <opaque-token>`
- error envelope: `code`, `message`, `details`, `request_id`
- 外部APIは呼び出さない。
- 404と403の情報開示方針は、教材・回答所有権を漏らさないようAPI単位で固定する。

## 認証

| method/path | role | 概要 | 要件 |
|---|---|---|---|
| `POST /auth/login` | 未認証 | opaque token発行 | AUTH-001 |
| `POST /auth/logout` | 認証済み | 現token失効 | AUTH-002 |
| `GET /auth/me` | 認証済み | userとrole取得 | AUTH-003 |

`POST /auth/login` responseは`access_token`, `token_type: bearer`, `user`を返す。tokenはJWTではなく推測困難なopaque値とする。

## 教材

| method/path | role | 概要 | 要件 |
|---|---|---|---|
| `GET /materials` | 全role | アクセス可能教材一覧 | VID-002 |
| `GET /materials/{material_id}` | 全role | 教材、動画、字幕状態 | VID-003 |
| `GET /videos/{video_id}/media` | 全role | ローカルdemo media | VID-004, VID-006 |

media endpointはfixtureだけを返し、任意path入力をファイルパスへ直接連結しない。

## question runとstream

| method/path | role | 概要 | 要件 |
|---|---|---|---|
| `POST /question-runs` | PREMIUM, ADMIN | 質問run作成 | STR-001 |
| `GET /question-runs/{run_id}` | 所有者/ADMIN | run状態取得 | HIS-001 |
| `GET /question-runs/{run_id}/events` | 所有者/ADMIN | SSE購読 | STR-002, STR-003 |
| `POST /question-runs/{run_id}/cancel` | 所有者/ADMIN | 明示中断 | STR-005 |
| `POST /answers/{answer_id}/regenerations` | 所有者/ADMIN | 新runとして再生成 | STR-007 |
| `GET /questions/history` | 認証済み | 自分の履歴 | HIS-001 |
| `POST /answers/{answer_id}/feedback` | 閲覧可能者 | 評価登録/更新 | HIS-003 |

question run request案:

```json
{
  "question": "カラー剤を塗布する順番は？",
  "material_ids": ["material-demo-1"]
}
```

response案:

```json
{
  "run_id": "run_opaque_id",
  "status": "submitted",
  "events_url": "/api/v1/question-runs/run_opaque_id/events"
}
```

run terminal statusは`completed`, `refused_insufficient_evidence`, `refused_out_of_scope`, `cancelled`, `failed`とする。

## 管理者

| method/path | role | 概要 | 要件 |
|---|---|---|---|
| `GET /admin/materials/transcript-status` | ADMIN | 字幕処理状態一覧 | ADM-001 |
| `POST /admin/videos/{video_id}/transcript-imports` | ADMIN | fixture字幕取込 | TRN-001 |
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
