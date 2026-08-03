import { fetchJsonWithFallback } from "./client";
import { getFallbackCorridorSummary } from "./fallbackData";
import type { CorridorSummary } from "../types/corridors";

export async function analyzeCorridor(roadId: string): Promise<CorridorSummary> {
  // POST rather than GET: the request body may grow to include additional
  // options (custom buffer and layer masks) without a URL redesign.
  return fetchJsonWithFallback("/api/corridors/analyze", () => getFallbackCorridorSummary(roadId), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ roadId })
  });
}
