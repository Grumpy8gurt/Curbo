// API base URL: defaults to the local backend but can be overridden via
// VITE_API_BASE_URL in .env for staging or production deployments.
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// When VITE_USE_MOCK_API=true, all API calls bypass the network and return
// fallback data immediately.  Useful for frontend-only development without
// running the Python backend.
export const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API === "true";

// Sentinel error class so fetchJsonWithFallback can distinguish server errors
// (4xx/5xx) from network failures (TypeError from fetch).
// Server errors are re-thrown — they indicate a backend bug, not an outage.
// Network failures fall through to the offline fallback.
class ApiRequestError extends Error {}

export async function resolveFallback<T>(value: T, delayMs = 180): Promise<T> {
  // Simulate a small network delay in mock/fallback mode so the UI loading
  // states are visible during development.
  await new Promise((resolve) => window.setTimeout(resolve, delayMs));
  return deepClone(value);
}

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

export async function fetchJsonWithFallback<T>(
  path: string,
  fallback: T | (() => T),
  init?: RequestInit
): Promise<T> {
  const fallbackValue = () =>
    typeof fallback === "function" ? (fallback as () => T)() : fallback;

  if (USE_MOCK_API) {
    return resolveFallback(fallbackValue());
  }

  try {
    const response = await fetch(apiUrl(path), init);
    if (!response.ok) {
      throw new ApiRequestError(`${response.status} ${response.statusText}`);
    }
    return (await response.json()) as T;
  } catch (error) {
    // Re-throw ApiRequestError (server errors) and non-TypeError exceptions
    // (unexpected runtime errors) so they surface to the caller.
    // TypeError is thrown by fetch when the network is unreachable — in that
    // case, silently fall back to the local data and log a warning.
    if (error instanceof ApiRequestError || !(error instanceof TypeError)) {
      throw error;
    }
    console.warn(`CURBO API unavailable for ${path}; using local fallback.`, error);
    return resolveFallback(fallbackValue(), 40);
  }
}

function deepClone<T>(value: T): T {
  // Cheap structural clone via JSON round-trip.  Sufficient for plain GeoJSON
  // objects; would lose Date/undefined/function values if they appeared.
  return JSON.parse(JSON.stringify(value)) as T;
}
