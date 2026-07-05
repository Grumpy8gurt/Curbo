import { apiUrl, resolveMock, USE_MOCK_API } from "./client";
import { getMockCorridorSummary } from "./mockData";
import type { CorridorSummary } from "../types/corridors";

export async function analyzeCorridor(roadId: string): Promise<CorridorSummary> {
  if (USE_MOCK_API) {
    return resolveMock(getMockCorridorSummary(roadId), 240);
  }

  const response = await fetch(apiUrl("/api/corridors/analyze"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ roadId })
  });

  return response.json();
}
