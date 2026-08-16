// API base URL: defaults to the local backend but can be overridden via
// VITE_API_BASE_URL in .env for staging or production deployments.
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// When VITE_USE_MOCK_API=true, all API calls bypass the network and return
// fallback data immediately.  Useful for frontend-only development without
// running the Python backend.
export const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API === "true";
const API_KEY = import.meta.env.VITE_CURBO_API_KEY;
const REQUEST_TIMEOUT_MS = 15_000;

// Normalized error class for HTTP errors, timeouts, network failures, and
// malformed responses. Real requests never switch into mock mode after an
// error; mock behavior is selected only by VITE_USE_MOCK_API.
export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly status?: number
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}

export async function resolveFallback<T>(value: T, delayMs = 180): Promise<T> {
  // Simulate a small network delay in mock/fallback mode so the UI loading
  // states are visible during development.
  await new Promise((resolve) => window.setTimeout(resolve, delayMs));
  return deepClone(value);
}

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

export async function fetchJson<T>(
  path: string,
  init?: RequestInit,
  validate?: (value: unknown) => value is T
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  if (API_KEY) {
    headers.set("X-API-Key", API_KEY);
  }

  const abortFromCaller = () => controller.abort();
  init?.signal?.addEventListener("abort", abortFromCaller, { once: true });

  try {
    const response = await fetch(apiUrl(path), {
      ...init,
      headers,
      signal: controller.signal
    });
    if (!response.ok) {
      let detail = `${response.status} ${response.statusText}`;
      try {
        const errorBody = (await response.json()) as { detail?: string };
        detail = errorBody.detail ?? detail;
      } catch {
        // A non-JSON error page still becomes a normal ApiRequestError.
      }
      throw new ApiRequestError(detail, response.status);
    }
    const contentType = response.headers.get("content-type") ?? "";
    if (!contentType.includes("application/json")) {
      throw new ApiRequestError("The API returned an unexpected response format");
    }
    const payload: unknown = await response.json();
    if (validate && !validate(payload)) {
      throw new ApiRequestError("The API response did not match the expected contract");
    }
    return payload as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiRequestError("The API request timed out");
    }
    if (error instanceof TypeError) {
      throw new ApiRequestError("The CURBO API is unreachable");
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
    init?.signal?.removeEventListener("abort", abortFromCaller);
  }
}

export async function fetchJsonWithFallback<T>(
  path: string,
  fallback: T | (() => T),
  init?: RequestInit,
  validate?: (value: unknown) => value is T
): Promise<T> {
  const fallbackValue = () =>
    typeof fallback === "function" ? (fallback as () => T)() : fallback;

  if (USE_MOCK_API) {
    return resolveFallback(fallbackValue());
  }

  return fetchJson<T>(path, init, validate);
}

function deepClone<T>(value: T): T {
  // Cheap structural clone via JSON round-trip.  Sufficient for plain GeoJSON
  // objects; would lose Date/undefined/function values if they appeared.
  return JSON.parse(JSON.stringify(value)) as T;
}
