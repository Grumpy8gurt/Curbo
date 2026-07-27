/** Corridor planning summary returned by POST /api/corridors/analyze. */
export interface CorridorSummary {
  corridorId: string;
  roadId: string;
  name: string;
  knownCurbRamps: number;
  possibleMissingCurbCuts: number;
  hydrantsNearby: number;
  bikeLanesNearby: number;
  userAnnotationsNearby: number;
  busStopsNearby: number;         // Always 0 in Sprint 3 — no bus stop data source yet.
  parkingConflicts: number;       // Always 0 in Sprint 3 — reserved for future data.
  bikeLaneFeasibility: "Low" | "Medium" | "High";
  planningNotes: string[];
}
