import { fetchJsonWithFallback } from "./client";
import { createFallbackReport } from "./fallbackData";
import type { CorridorReportResult } from "../types/reports";

export async function generateCorridorReport(
  roadId: string,
  roadName: string
): Promise<CorridorReportResult> {
  return fetchJsonWithFallback("/api/reports/corridor", () => createFallbackReport(roadId, roadName), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ roadId, format: "html" })
  });
}
