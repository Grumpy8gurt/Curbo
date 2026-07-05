export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API !== "false";

export async function resolveMock<T>(value: T, delayMs = 180): Promise<T> {
  await new Promise((resolve) => window.setTimeout(resolve, delayMs));
  return deepClone(value);
}

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

function deepClone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}
