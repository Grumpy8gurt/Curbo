import { fetchJsonWithFallback } from "./client";
import { getFallbackCorridorSummary } from "./fallbackData";
import type { CorridorSummary } from "../types/corridors";

export async function analyzeCorridor(roadId: string): Promise<CorridorSummary> {
  return fetchJsonWithFallback("/api/corridors/analyze", () => getFallbackCorridorSummary(roadId), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ roadId })
  });
}
