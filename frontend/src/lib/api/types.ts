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
  transcript_status: "NOT_IMPORTED";
  is_active: boolean;
  created_at: string;
  updated_at: string;
};
