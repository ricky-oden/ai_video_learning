export type Role = "MEMBER" | "PREMIUM" | "ADMIN";

export type User = { id: string; email: string; role: Role };

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
  expires_at: string;
  user: User;
};

export type Material = {
  id: string;
  title: string;
  description: string;
  required_role: "MEMBER" | "PREMIUM";
  video_path: string;
  duration_ms: number;
  transcript_status: "NOT_IMPORTED" | "PROCESSING" | "READY" | "FAILED";
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AdminMaterial = Material & {
  current_version: number | null;
  latest_version: number | null;
  segment_count: number;
  chunk_count: number;
  embedding_count: number;
  provider_name: string | null;
  provider_version: string | null;
  dimensions: number | null;
};

export type TranscriptVersion = {
  id: string;
  material_id: string;
  version: number;
  source_fixture: string;
  normalization_version: string;
  chunking_version: string;
  status: "PROCESSING" | "READY" | "FAILED";
  failure_code: string | null;
  failure_message: string | null;
  is_current: boolean;
  segment_count: number;
  chunk_count: number;
  embedding_count: number;
  provider_name: string | null;
  provider_version: string | null;
  dimensions: number | null;
};

export type Citation = {
  id: string;
  material_id: string;
  transcript_version_id: string;
  chunk_id: string;
  video_path: string;
  start_ms: number;
  end_ms: number;
  text_snapshot: string;
  display_order: number;
};

export type GroundedAnswer = {
  id: string;
  body: string;
  provider_name: string;
  provider_version: string;
  citations: Citation[];
};

export type QuestionRun = {
  run_id: string;
  question: string;
  material_ids: string[];
  status:
    | "PROCESSING"
    | "COMPLETED"
    | "REFUSED_INSUFFICIENT_EVIDENCE"
    | "REFUSED_OUT_OF_SCOPE"
    | "FAILED";
  failure_code: string | null;
  created_at: string;
  completed_at: string | null;
  answer: GroundedAnswer | null;
};
