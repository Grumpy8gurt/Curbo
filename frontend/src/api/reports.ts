import { fetchJsonWithFallback } from "./client";
import { createFallbackReport } from "./fallbackData";
import type { CorridorReportResult } from "../types/reports";
import { isCorridorReportResult } from "./validation";

export async function generateCorridorReport(
  roadId: string,
  roadName: string
): Promise<CorridorReportResult> {
  // roadName is only used by the fallback factory — the backend derives the
  // name from the road feature, but the fallback needs it as a parameter so
  // the preview summary message is meaningful without a network call.
  return fetchJsonWithFallback(
    "/api/v1/reports/corridor",
    () => createFallbackReport(roadId, roadName),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ roadId, format: "html" })
    },
    isCorridorReportResult
  );
}
