import { apiUrl, resolveMock, USE_MOCK_API } from "./client";
import { createMockReport } from "./mockData";
import type { CorridorReportResult } from "../types/reports";

export async function generateCorridorReport(
  corridorId: string,
  roadName: string
): Promise<CorridorReportResult> {
  if (USE_MOCK_API) {
    return resolveMock(createMockReport(corridorId, roadName), 260);
  }

  const response = await fetch(apiUrl("/api/reports/corridor"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ corridor_id: corridorId, format: "html" })
  });

  return response.json();
}
