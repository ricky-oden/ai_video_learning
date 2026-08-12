# データモデル

PLAN_VERSION: `AI-LEARNING-V1.0`

認証・教材tableはPhase 2で実装済み。Phase 3以降のtableは未実装である。IDはUUID、時刻はUTC、動画位置は整数millisecondで保持する。

## 認証

- `users`: id, email(unique), password_hash(Argon2id), role, is_active, created_at, updated_at
- `auth_sessions`: id, user_id, token_hash(SHA-256, unique), expires_at, revoked_at, created_at

DBには原則としてtokenの照合用hashを保存し、平文tokenの永続化やログ出力を避ける。この方針は「tokenをDBへ保存する」要件を満たしつつ漏えい影響を抑える。

## 教材と動画

- `materials`: id, title, description, required_role, video_path, duration_ms, transcript_status, is_active, created_at, updated_at

`video_path`は`/media/demo-hair-technique.mp4`という管理済みfixture pathであり、利用者入力の任意ファイルパスを許可しない。Phase 2では動画を独立tableへ分けない。

## 字幕

- `transcript_versions`: id, video_id, version, source_fixture, normalization_version, status, created_by, created_at, published_at
- `transcript_segments`: id, transcript_version_id, sequence, original_text, normalized_text, start_ms, end_ms
- `transcript_chunks`: id, transcript_version_id, sequence, text, first_segment_id, last_segment_id, start_ms, end_ms, chunking_version
- `chunk_embeddings`: id, chunk_id, provider_name, provider_version, dimensions, embedding vector, created_at

制約案:

- `(video_id, version)` unique
- `(transcript_version_id, sequence)` unique
- `start_ms >= 0`, `end_ms > start_ms`
- vector次元はfake provider固定次元と一致
- 公開versionはvideoごとに一つ

## 質問、検索、回答

- `questions`: id, user_id, text, created_at
- `question_runs`: id, question_id, user_id, status, explicit_cancel_requested_at, disconnected_at, started_at, completed_at, failure_code
- `retrieval_runs`: id, question_run_id, provider_name, provider_version, dimensions, top_k, policy_version, started_at, completed_at
- `retrieval_results`: id, retrieval_run_id, chunk_id, rank, distance, is_selected
- `answers`: id, question_run_id, parent_answer_id, body, provider_name, provider_version, generation_policy_version, created_at
- `answer_citations`: id, answer_id, retrieval_result_id, transcript_version_id, chunk_id, video_id, start_ms, end_ms, text_snapshot, display_order
- `answer_feedback`: id, answer_id, user_id, rating, reason_code, comment, created_at, updated_at

不変条件:

- answerは一つのquestion runに属する。
- citationは同じrunの認可済みretrieval resultだけを参照する。
- citationは回答時snapshotを保持する。
- refused/cancelled/failed runに正式なcompleted answerを作らない。
- 再生成answerは`parent_answer_id`を持ち、元answerを変更しない。

## 評価

- `evaluation_cases`: id, version, question, expected_answerability, expected_video_id, expected_start_ms, expected_end_ms, required_facts, forbidden_claims
- `evaluation_runs`: id, dataset_version, provider_versions, policy_versions, started_at, completed_at
- `evaluation_results`: id, evaluation_run_id, case_id, hit_at_k, video_match, range_overlap, citation_valid, unsupported_claim, answerability_match, out_of_scope_false_answer, ttft_ms, total_ms, cancel_success, regeneration_success, details

評価ケースは人が作成・版管理し、fake回答を正解ラベルとして自動登録しない。

## 削除と保持

学習用初期版の保持期間・物理削除要件は未確定。少なくとも引用済み字幕versionを更新で上書きせず、過去回答の再現性を壊さない。
