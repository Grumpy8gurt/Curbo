export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API === "true";

class ApiRequestError extends Error {}

export async function resolveFallback<T>(value: T, delayMs = 180): Promise<T> {
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
    if (error instanceof ApiRequestError || !(error instanceof TypeError)) {
      throw error;
    }
    console.warn(`CURBO API unavailable for ${path}; using local fallback.`, error);
    return resolveFallback(fallbackValue(), 40);
  }
}

function deepClone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}
