export type ApiError = { code: string; message: string; error_id?: string };
export type ApiEnvelope<T> = { success: boolean; data?: T; error?: ApiError; request_id: string };
export type AdminModule = { id: string; label: string; destination: string; owner: string };

export const backendUrl = process.env.FAVORITE_API_URL ?? "http://127.0.0.1:8000";

export function safeError(payload: unknown): string {
  if (typeof payload === "object" && payload !== null && "error" in payload) {
    const error = (payload as { error?: unknown }).error;
    if (typeof error === "object" && error !== null && "message" in error && typeof error.message === "string") return error.message;
  }
  return "The operation could not be completed.";
}
