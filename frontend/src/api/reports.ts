import { apiUrl, resolveMock, USE_MOCK_API } from "./client";
import { createMockReport } from "./mockData";
import type { CorridorReportResult } from "../types/reports";

export async function generateCorridorReport(
  roadId: string,
  roadName: string
): Promise<CorridorReportResult> {
  if (USE_MOCK_API) {
    return resolveMock(createMockReport(roadId, roadName), 260);
  }

  const response = await fetch(apiUrl("/api/reports/corridor"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ roadId, format: "html" })
  });

  const payload = await response.json();

  if ("reportId" in payload) {
    return payload;
  }

  return {
    reportId: payload.report_id,
    roadId,
    downloadUrl: payload.download_url,
    summary: `${roadName} corridor report generated. Download at ${payload.download_url}.`
  };
}
