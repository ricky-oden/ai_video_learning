const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1";
const tokenStorageKey = "ai-learning-access-token";

export class ApiClientError extends Error {
  constructor(
    readonly status: number,
    readonly payload: unknown,
  ) {
    super(`API request failed with status ${status}`);
  }
}

export function getStoredToken(): string | null {
  return globalThis.localStorage?.getItem(tokenStorageKey) ?? null;
}

export function storeToken(token: string): void {
  globalThis.localStorage?.setItem(tokenStorageKey, token);
}

export function clearStoredToken(): void {
  globalThis.localStorage?.removeItem(tokenStorageKey);
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${apiBaseUrl}${path}`, { ...init, headers });
  if (!response.ok) {
    if (response.status === 401) clearStoredToken();
    let payload: unknown = null;
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }
    throw new ApiClientError(response.status, payload);
  }
  return (await response.json()) as T;
}
