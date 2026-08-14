export class AdminRequestError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "AdminRequestError";
  }
}

function responseMessage(payload: unknown, status: number): string {
  if (status === 401) return "Your session has expired. Please sign in again.";
  if (status === 403) return "You do not have permission to perform this action.";
  if (typeof payload === "object" && payload !== null && "error" in payload) {
    const error = (payload as { error?: unknown }).error;
    if (typeof error === "string") return error;
    if (typeof error === "object" && error !== null && "message" in error && typeof error.message === "string") {
      return error.message;
    }
  }
  if (status === 503) return "The service is unavailable.";
  if (status >= 500) return "The Admin service encountered an error.";
  return "The operation could not be completed.";
}

export async function parseJsonSafely(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text.trim()) return null;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return null;
  }
}

export async function adminRequest<T>(url: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, { cache: "no-store", ...init });
  } catch {
    throw new AdminRequestError("The service is unavailable.", 503);
  }

  const payload = await parseJsonSafely(response);
  if (!response.ok) throw new AdminRequestError(responseMessage(payload, response.status), response.status);
  if (typeof payload !== "object" || payload === null || !("data" in payload)) {
    throw new AdminRequestError("The Admin service returned an invalid response.", 502);
  }
  return (payload as { data: T }).data;
}

export function isAuthenticationError(error: unknown): boolean {
  return error instanceof AdminRequestError && error.status === 401;
}
