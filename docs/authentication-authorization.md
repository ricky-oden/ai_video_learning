# 認証・認可

PLAN_VERSION: `AI-LEARNING-V1.0`

## 認証方式

- 学習用のopaque Bearer tokenを使用する。
- ログイン時に推測困難なtokenを一度返し、DBに認証用レコードを保存する。
- DBにはSHA-256 token hashだけを保存し、request tokenをhash化して照合する。
- tokenの有効期限は発行から8時間とする。
- 同一userの未失効sessionは1件とし、再ログイン時に旧sessionをrevokeする。
- logoutで現在tokenを失効させる。
- API keyや外部identity providerは使用しない。

## frontend保存とXSS

frontendはtokenをlocalStorageへ保存する。これは学習用の明示的選択であり、JavaScriptから読み取れるため、XSSが起きるとtokenを窃取され得る。

対策範囲:

- 字幕やAI回答を未検証HTMLとして描画しない。
- `dangerouslySetInnerHTML`を認証済みデータの表示に使用しない。
- tokenをURL、error message、application logへ含めない。
- logoutでlocalStorageから削除する。
- APIが401を返した場合もlocalStorageから削除する。
- frontend role表示を認可の根拠にしない。

本番向けCookie方式への変更は初期範囲外であり、必要なら計画変更として扱う。

## role matrix

| 操作 | MEMBER | PREMIUM | ADMIN |
|---|---:|---:|---:|
| MEMBER教材一覧・詳細・動画 | 許可 | 許可 | 許可 |
| PREMIUM教材一覧・詳細・動画 | 拒否 | 許可 | 許可 |
| ADMIN教材・字幕状態一覧 | 拒否 | 拒否 | 許可 |
| AI question run作成 | 拒否 | 許可 | 許可 |
| 自分のrunをstream/cancel | 拒否 | 許可 | 許可 |
| 自分の回答を再生成 | 拒否 | 許可 | 許可 |
| 自分が閲覧可能な履歴・評価 | 許可 | 許可 | 許可 |
| 字幕fixture取込 | 拒否 | 拒否 | 許可 |
| 字幕処理状態・評価結果 | 拒否 | 拒否 | 許可 |

教材ごとの`required_role`も検索・表示前に検査する。ADMINの包括アクセス範囲は学習用fixture内に限る。

## 認可順序

1. Bearer headerの形式を検証する。
2. token hashで有効・未失効tokenを取得する。
3. userがactiveであることを確認する。
4. endpointに必要なroleを検査する。
5. resource所有者または教材アクセスを検査する。
6. RAG検索条件にも同じ教材制約を適用する。

frontendでボタンを隠しても、backendは直接requestを必ず再検査する。
