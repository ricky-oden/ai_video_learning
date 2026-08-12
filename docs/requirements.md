# 要件と受入条件

PLAN_VERSION: `AI-LEARNING-V1.0`

すべての要件の初期状態は`未実装`である。受入条件が実装され、指定テストまたは確認手順が成功した場合だけ状態を変更する。

## システム基盤

### SYS-001 固定技術構成

- 状態: 実装・検証済み（2026-08-12）
- 要件: Node.js 22系、npm、Next.js App Router、React、TypeScript、Python 3.12系、FastAPI、SQLAlchemy、Alembic、PostgreSQL 16系、pgvectorを使用する。
- 受入条件: 実行環境とlockfileから各採用技術・major/minor方針を確認でき、README記載の再現手順が成功する。

### SYS-002 Python依存の分離

- 状態: 実装・検証済み（2026-08-12）
- 要件: runtime依存とdevelopment/test依存を分離する。
- 受入条件: runtime環境にtest専用依存を入れずbackendが起動でき、development/test環境でpytest等を実行できる。

### SYS-003 Docker Compose分離

- 状態: 実装・検証済み（2026-08-12）
- 要件: frontend、backend、dbをCompose serviceとして分離し、project名を`ai-video-learning`、host portを3001/8003、DB内部接続を`db:5432`とする。
- 受入条件: 各serviceのhealthcheckが成功し、frontendからbackend、backendからDBへ接続できる。

### DB-001 pgvector有効化

- 状態: 実装・検証済み（2026-08-12）
- 要件: PostgreSQL 16系でpgvector extensionと必要なschemaをAlembic管理する。
- 受入条件: 新規DBへのmigrationでvector列を作成でき、downgrade/upgrade方針がテストされる。

## 認証・認可

### AUTH-001 opaque Bearer tokenログイン

- 状態: 実装・検証済み（2026-08-12）
- 要件: 学習用ログイン成功時にopaque tokenを発行し、tokenの認証用レコードをDBへ保存する。
- 受入条件: 正常な資格情報でtokenが発行され、不正な資格情報は401となり、token文字列からユーザー情報を復元できない。

### AUTH-002 frontend token保存

- 状態: 実装・検証済み（2026-08-12）
- 要件: frontendはtokenをlocalStorageへ保存し、Bearer headerへ設定する。XSSにより読み取られるリスクをREADMEと認証文書へ明記する。
- 受入条件: 再読込後にtokenを再利用でき、logoutで削除され、XSS上の注意が文書化される。

### AUTH-003 role区分

- 状態: 実装・検証済み（2026-08-12）
- 要件: `MEMBER`、`PREMIUM`、`ADMIN`を区別する。
- 受入条件: backendの認可テストで各roleの許可・拒否結果がrole matrixと一致する。

### AUTH-004 AI質問権限

- 状態: 未実装
- 要件: AI質問、stream、中断、再生成はPREMIUMとADMINだけが利用できる。
- 受入条件: MEMBERは403、PREMIUMとADMINは許可され、frontendの表示に関係なくbackendで拒否できる。

### AUTH-005 管理者権限

- 状態: 一部実装・Phase 6検証待ち（2026-08-12、字幕取込認可のみ）
- 要件: 字幕取込と評価結果確認はADMINだけが利用できる。
- 受入条件: MEMBER/PREMIUMは403、ADMINだけが操作できる。

### AUTH-006 backend最終認可

- 状態: 実装・検証済み（2026-08-12、Phase 2 API）
- 要件: frontendの表示制御を信用せず、すべての保護APIでbackendがtoken、role、教材アクセスを検査する。
- 受入条件: UIを経由しない直接API requestでも不許可操作を拒否できる。

## 通常動画機能

### VID-001 ログイン画面

- 状態: 実装・検証済み（2026-08-12）
- 要件: ログイン、失敗表示、logoutを提供する。
- 受入条件: 正常・不正ログイン、再読込、logoutのE2Eが成功する。

### VID-002 教材一覧

- 状態: 実装・検証済み（2026-08-12）
- 要件: ローカルデモ教材の一覧を、認証ユーザーがアクセス可能な範囲で表示する。
- 受入条件: APIと画面の表示内容がfixtureおよびアクセス権と一致する。

### VID-003 教材詳細

- 状態: 実装・検証済み（2026-08-12）
- 要件: 教材情報、動画情報、字幕処理状態を表示する。
- 受入条件: 存在、未存在、アクセス不可をそれぞれ200、404、403として扱う。

### VID-004 動画プレイヤーUI

- 状態: 実装・検証済み（2026-08-12）
- 要件: リポジトリ内のローカルデモ動画を再生するUIを提供する。
- 受入条件: 外部URLを使わずfixture動画を読込み、標準的な再生操作を行える。

### VID-005 指定再生位置への移動

- 状態: 一部実装・Phase 4検証待ち（2026-08-12、指定位置UIと純粋関数のみ）
- 要件: 回答引用の`start_ms`から対象動画の再生位置へ移動する。
- 受入条件: 引用選択後、正しい動画と許容誤差内の再生位置が選択されるE2Eが成功する。

### VID-006 ローカル教材限定

- 状態: 実装・検証済み（2026-08-12）
- 要件: 教材、動画、字幕はリポジトリ内fixtureだけを使用し、外部動画・字幕APIを呼ばない。
- 受入条件: fixture以外の取得処理・外部URL・外部API依存がなく、networkテストで外部通信が発生しない。

### ADM-001 教材・字幕状態確認

- 状態: 実装・検証済み（2026-08-12）
- 要件: ADMINが教材、字幕version、segment/chunk/embedding処理状態を確認できる。
- 受入条件: ADMIN画面/APIで成功・失敗・未処理状態を確認でき、非ADMINは403となる。

## 字幕処理

### TRN-001 字幕fixture取込

- 状態: 実装・検証済み（2026-08-12）
- 要件: ADMIN操作でローカル字幕fixtureを取込み、取込結果を記録する。
- 受入条件: 正常fixtureを再現可能に取込み、不正形式を永続化前に拒否し、処理状態を確認できる。

### TRN-002 正規化

- 状態: 実装・検証済み（2026-08-12）
- 要件: 元字幕を変更せず保持し、正規化規則と版を記録して正規化テキストを作成する。
- 受入条件: 同一入力と同一規則から同一結果が得られ、元テキストを参照できる。

### TRN-003 segment保存

- 状態: 実装・検証済み（2026-08-12）
- 要件: 字幕をversion、sequence、text、start_ms、end_ms付きsegmentとして保存する。
- 受入条件: sequenceと時刻が単調で、`0 <= start_ms < end_ms`をDB/APIで保証する。

### TRN-004 chunk作成

- 状態: 実装・検証済み（2026-08-12）
- 要件: segment境界と時間範囲を追跡可能なchunkを決定論的に作成し、chunking versionを保存する。
- 受入条件: 同一segmentと設定から同一chunkが作られ、各chunkから元segment範囲へ戻れる。

### TRN-005 字幕版の不変参照

- 状態: 一部実装・Phase 4検証待ち（2026-08-12、旧version保持まで）
- 要件: 過去回答が参照した字幕versionを保持し、新version公開後も過去根拠を再現できる。
- 受入条件: 新version追加後も既存answer citationのtext snapshot、chunk、時刻を取得できる。

## provider境界

### PRV-001 EmbeddingProvider分離

- 状態: 実装・検証済み（2026-08-12）
- 要件: embedding生成をアプリケーションuse-caseからinterfaceで分離する。
- 受入条件: use-caseが具体provider SDK型に依存せず、contract testを実行できる。

### PRV-002 AnswerGenerationProvider分離

- 状態: 一部実装・Phase 4検証待ち（2026-08-12、interfaceのみ）
- 要件: 回答生成とstream event生成をinterfaceで分離する。
- 受入条件: use-caseが具体provider SDK型に依存せず、contract testを実行できる。

### PRV-003 決定論的fake embedding

- 状態: 実装・検証済み（2026-08-12）
- 要件: fake embeddingは固定次元で、同一の正規化入力とprovider versionから同一vectorを生成する。
- 受入条件: 複数実行、別process、テスト環境で完全一致し、次元数がDB定義と一致する。

### PRV-004 provider metadata

- 状態: 一部実装・Phase 4検証待ち（2026-08-12、chunk embedding metadataのみ）
- 要件: provider名、version、embedding次元、生成設定版を処理結果へ記録する。
- 受入条件: 検索runと回答runから使用provider設定を追跡できる。

### PRV-005 根拠限定fake回答

- 状態: 未実装
- 要件: fake回答は検索済みかつ認可済みの根拠だけから決定論的に組み立てる。
- 受入条件: 根拠にないfixture事実を出力せず、回答中のcitation IDが許可済みchunk集合の部分集合となる。

### PRV-006 実provider禁止

- 状態: 未実装
- 要件: 初期実装にOpenAI SDK、API key、実OpenAI/外部embedding呼出しを含めない。
- 受入条件: dependency、環境変数、コード、network testに実provider接続が存在しない。

### PRV-007 fake障害制御

- 状態: 未実装
- 要件: テスト用に遅延、途中失敗、中断可能点を決定論的に指定できる。
- 受入条件: 指定scenarioごとに同じevent列と最終状態を再現できる。

## RAG

### RAG-001 字幕からembeddingまで

- 状態: 実装・検証済み（2026-08-12）
- 要件: 取込、正規化、segment、chunk、fake embedding、pgvector保存を順番に実行する。
- 受入条件: 各段階の状態と件数を記録し、失敗した段階以降を公開済みにしない。

### RAG-002 質問embedding

- 状態: 実装・検証済み（2026-08-12、検索service境界）
- 要件: 質問を字幕chunkと同じfake embedding空間へ変換する。
- 受入条件: provider versionと次元が一致し、不一致時は検索せず失敗状態になる。

### RAG-003 類似検索

- 状態: 実装・検証済み（2026-08-12、検索service境界）
- 要件: pgvectorにより質問に近いchunkを検索する。
- 受入条件: 固定fixtureに対して期待chunkが設定したk以内に含まれる。

### RAG-004 検索時アクセス制御

- 状態: 実装・検証済み（2026-08-12、検索service境界）
- 要件: 検索対象を公開字幕version、アクセス可能教材、認証ユーザーの権限で絞る。
- 受入条件: アクセス不可教材のchunkが検索結果とprovider入力へ一切含まれない。

### RAG-005 根拠十分性判定

- 状態: 未実装
- 要件: 検索件数、score、期待する教材範囲など、版管理された決定規則で回答可否を判定する。
- 受入条件: 境界値を含む固定fixtureが期待する回答可能/不可状態になる。

### RAG-006 根拠不足の拒否

- 状態: 未実装
- 要件: 十分性条件を満たさない場合は生成providerを呼ばず、`refused_insufficient_evidence`を保存・表示する。
- 受入条件: provider呼出しが0回で、拒否理由と検索runが保存される。

### RAG-007 教材外質問の拒否

- 状態: 未実装
- 要件: 教材内に根拠がない質問は生成providerを呼ばず、`refused_out_of_scope`を保存・表示する。
- 受入条件: 教材外fixtureでprovider呼出しが0回となり、誤った一般知識回答を返さない。

### RAG-008 根拠付き回答

- 状態: 未実装
- 要件: 回答に使用した字幕版、chunk、動画、start_ms、end_msを引用として提示する。
- 受入条件: 全citationが同じrunの認可済み検索結果に存在し、動画位置へ移動できる。

### RAG-009 回答・引用保存

- 状態: 未実装
- 要件: 回答、状態、provider設定、検索run、citation、回答時テキストスナップショットを保存する。
- 受入条件: 後から回答時の入力、検索結果、引用を再構成できる。

### RAG-010 生成後引用検証

- 状態: 未実装
- 要件: provider出力のcitation IDを許可済み検索結果と照合し、不整合なら正式回答として完了させない。
- 受入条件: 不正citation fixtureがfailedまたはrefusedとなり、completed answerとして公開されない。

## 履歴と評価入力

### HIS-001 質問・回答履歴

- 状態: 未実装
- 要件: 認証ユーザーが自分の質問、回答、拒否、失敗、中断履歴を確認できる。
- 受入条件: 他ユーザーの履歴を取得できず、各状態を区別して表示できる。

### HIS-002 回答コピー

- 状態: 未実装
- 要件: 完了した回答本文をfrontendからコピーできる。
- 受入条件: 完了回答だけをコピーでき、失敗・拒否状態で誤った本文をコピーしない。

### HIS-003 回答評価

- 状態: 未実装
- 要件: 利用者が回答へ評価と任意理由を登録できる。
- 受入条件: 自分が閲覧可能な回答だけを評価でき、更新方針がAPI仕様どおりに適用される。

## streaming

### STR-001 question run作成

- 状態: 未実装
- 要件: POST APIでquestion runを作成し、run IDと初期状態を返す。
- 受入条件: 認可・入力検証後に一意なrun IDが返り、DB状態と一致する。

### STR-002 run ID SSE

- 状態: 未実装
- 要件: run ID指定のSSE endpointからstream eventを受信する。
- 受入条件: 異なるユーザーのrunを購読できず、完了時にterminal eventが送られる。

### STR-003 event envelope

- 状態: 未実装
- 要件: 全eventに`run_id`、単調増加`sequence`、`event_type`を持たせる。
- 受入条件: event欠落・重複をfrontendが検知でき、未知eventを安全に無視またはerror表示できる。

### STR-004 frontend受信停止

- 状態: 未実装
- 要件: frontendはAbortControllerでSSE受信を停止する。
- 受入条件: 中断操作後に追加chunkを画面へ反映しない。

### STR-005 backend cancel

- 状態: 未実装
- 要件: frontend中断時にcancel APIも呼び、backend runを`cancelled`へ遷移させる。
- 受入条件: cancel後にprovider処理が停止し、完了回答を保存しない。

### STR-006 切断と明示中断の区別

- 状態: 未実装
- 要件: network切断を明示cancelと区別し、runの状態を正しく保持する。
- 受入条件: 切断fixtureとcancel fixtureが異なる監査状態になり、再接続方針がprotocol文書と一致する。

### STR-007 非破壊再生成

- 状態: 未実装
- 要件: 再生成は元回答を上書きせず、新run/answerに親回答IDを保存する。
- 受入条件: 元回答と引用が保持され、再生成履歴を辿れる。

## 初期評価

### EVAL-001 検索Hit@k

- 状態: 未実装
- 要件: 期待chunkが上位k件に含まれる割合を記録する。
- 受入条件: 固定評価セットに対するケース別結果と集計値を再現できる。

### EVAL-002 期待動画・字幕範囲一致

- 状態: 未実装
- 要件: 取得・引用した動画IDと時間範囲を期待値と比較する。
- 受入条件: 動画一致と時間範囲の重なりをケース別に確認できる。

### EVAL-003 引用整合性

- 状態: 未実装
- 要件: citationが検索済みchunk、字幕版、回答スナップショットと一致するか検証する。
- 受入条件: 改変citationを検出し、評価失敗として記録できる。

### EVAL-004 根拠外主張

- 状態: 未実装
- 要件: 人が定義した必須事実・禁止主張に基づき、根拠外主張の有無を評価する。
- 受入条件: AI生成結果を正解ラベルにせず、固定評価ケースから判定根拠を追跡できる。

### EVAL-005 回答可否判定

- 状態: 未実装
- 要件: 回答可能/不可の期待値とシステム判定を比較する。
- 受入条件: true/false positive/negativeの件数を出力できる。

### EVAL-006 教材外誤回答率

- 状態: 未実装
- 要件: 教材外ケースに回答してしまった割合を記録する。
- 受入条件: 分母・分子・対象ケースを追跡できる。

### EVAL-007 TTFTと総応答時間

- 状態: 未実装
- 要件: request開始から最初の回答token eventまでとterminal eventまでの時間を記録する。
- 受入条件: fake delayを用いたテストで測定点が期待順序になる。

### EVAL-008 中断・再生成成功

- 状態: 未実装
- 要件: cancelが完了回答を残さないことと、再生成が元回答を保持することを評価する。
- 受入条件: 固定scenarioの成功/失敗と原因を記録できる。

MRRとnDCGは将来候補であり、`AI-LEARNING-V1.0`の必須完成条件ではない。

## セキュリティとテスト

### SEC-001 秘密情報・外部通信禁止

- 状態: 未実装
- 要件: API keyを要求・保存・表示せず、外部AI、embedding、動画、字幕APIへ通信しない。
- 受入条件: dependency、環境変数、ログ、networkテストを確認し、外部通信が0件である。

### SEC-002 XSS注意

- 状態: 未実装
- 要件: localStorage tokenがXSSで窃取され得ることを文書化し、危険なHTML注入を避ける。
- 受入条件: 認証文書に制約があり、回答・字幕を未検証HTMLとして描画しないテストがある。

### TST-001 frontendテスト

- 状態: 未実装
- 要件: VitestとReact Testing Libraryで主要component・state・権限制御を検証する。
- 受入条件: test commandが成功し、重要な拒否・stream状態を含む。

### TST-002 backendテスト

- 状態: 未実装
- 要件: pytestでservice、API、DB、provider contract、認可を検証する。
- 受入条件: PostgreSQL/pgvectorを含むtest commandが再現可能に成功する。

### TST-003 E2Eテスト

- 状態: 未実装
- 要件: Playwrightでログインから質問、引用再生、中断、再生成、評価までを検証する。
- 受入条件: ローカルfixtureとfake providerだけで主要正常系・拒否系が成功する。

## 明示的対象外

- 学習進捗率、視聴完了管理、ブックマーク、教材クイズ
- 動画アップロードサービス、CDN、外部動画配信サービス
- 課金・契約処理
- 実OpenAI API、外部embedding API、OpenAI SDK
- background queue製品、複数言語、本番監視、本番デプロイ
- 自動改善、AIによるpromptまたは閾値の自動書換え
- MRR、nDCGの必須完成条件化
