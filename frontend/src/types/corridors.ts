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
  busStopsNearby: number; // Always 0 until CURBO has a documented transit-stop source.
  parkingConflicts: number;
  bikeLaneGaps: number;
  intersectionSafetyConcerns: number;
  annotationsNeedingReview: number;
  bikeLaneFeasibility: "Low" | "Medium" | "High";
  reviewPriority: "Low" | "Medium" | "High";
  reviewSignals: string[];
  dataLimitation: string;
  planningNotes: string[];
}
