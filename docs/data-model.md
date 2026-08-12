# データモデル

PLAN_VERSION: `AI-LEARNING-V1.0`

Phase 4までの認証、教材、字幕、embedding、質問、検索、回答、citation、feedback tableを実装済みである。IDはUUID、時刻はUTC、動画位置は整数millisecondで保持する。

## 認証

- `users`: id, email(unique), password_hash(Argon2id), role, is_active, created_at, updated_at
- `auth_sessions`: id, user_id, token_hash(SHA-256, unique), expires_at, revoked_at, created_at

DBには原則としてtokenの照合用hashを保存し、平文tokenの永続化やログ出力を避ける。この方針は「tokenをDBへ保存する」要件を満たしつつ漏えい影響を抑える。

## 教材と動画

- `materials`: id, title, description, required_role, video_path, duration_ms, transcript_status, is_active, created_at, updated_at

`video_path`は`/media/demo-hair-technique.mp4`という管理済みfixture pathであり、利用者入力の任意ファイルパスを許可しない。Phase 2では動画を独立tableへ分けない。

## 字幕

- `transcript_versions`: id, material_id, version, source_fixture, normalization_version, chunking_version, status, failure_code, failure_message, created_by, created_at, published_at, is_current
- `transcript_segments`: id, transcript_version_id, sequence, original_text, normalized_text, start_ms, end_ms
- `transcript_chunks`: id, transcript_version_id, sequence, text, first_segment_sequence, last_segment_sequence, start_ms, end_ms
- `chunk_embeddings`: id, chunk_id, provider_name, provider_version, dimensions, embedding vector(32), created_at

制約案:

- `(material_id, version)` unique
- `(transcript_version_id, sequence)` unique
- `start_ms >= 0`, `end_ms > start_ms`
- vector次元はfake provider固定32次元と一致
- current versionは教材ごとに一つ

## 質問、検索、回答

- `question_runs`: id, user_id, question, status, failure_code, failure_message, created_at, completed_at
- `question_run_materials`: question_run_id, material_id
- `retrieval_runs`: id, question_run_id, embedding provider metadata, dimensions, top_k, policy_version, lexical_overlap_threshold, cosine_distance_threshold, created_at
- `retrieval_results`: id, retrieval_run_id, chunk_id, rank, distance, lexical_overlap_ratio, is_selected
- `answers`: id, question_run_id, body, provider_name, provider_version, created_at
- `answer_citations`: id, answer_id, retrieval_result_id, transcript_version_id, chunk_id, material_id, video_path, start_ms, end_ms, text_snapshot, display_order
- `answer_feedback`: id, answer_id, user_id, rating, comment, created_at, updated_at

不変条件:

- answerは一つのquestion runに属する。
- citationは同じrunの認可済みretrieval resultだけを参照する。
- citationは回答時snapshotを保持する。
- refused/cancelled/failed runに正式なcompleted answerを作らない。
- Phase 5の再生成では親関係を追加し、元answerを変更しない。Phase 4では再生成を実装しない。

## 評価

- `evaluation_cases`: id, version, question, expected_answerability, expected_video_id, expected_start_ms, expected_end_ms, required_facts, forbidden_claims
- `evaluation_runs`: id, dataset_version, provider_versions, policy_versions, started_at, completed_at
- `evaluation_results`: id, evaluation_run_id, case_id, hit_at_k, video_match, range_overlap, citation_valid, unsupported_claim, answerability_match, out_of_scope_false_answer, ttft_ms, total_ms, cancel_success, regeneration_success, details

評価ケースは人が作成・版管理し、fake回答を正解ラベルとして自動登録しない。

## 削除と保持

学習用初期版の保持期間・物理削除要件は未確定。少なくとも引用済み字幕versionを更新で上書きせず、過去回答の再現性を壊さない。
