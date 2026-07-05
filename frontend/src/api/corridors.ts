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

  const payload = await response.json();

  if ("corridorId" in payload) {
    return payload;
  }

  return {
    corridorId: payload.road_id,
    roadId: payload.road_id,
    name: payload.road_name,
    knownCurbRamps: payload.known_curb_ramps,
    possibleMissingCurbCuts: payload.possible_missing_curb_cuts,
    hydrantsNearby: payload.hydrants,
    busStopsNearby: payload.bus_stops,
    parkingConflicts: payload.parking_conflicts,
    bikeLaneFeasibility:
      payload.bike_lane_feasibility.charAt(0).toUpperCase() +
      payload.bike_lane_feasibility.slice(1),
    planningNotes: payload.notes
  };
}
