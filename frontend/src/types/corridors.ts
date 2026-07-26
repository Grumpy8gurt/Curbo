export interface CorridorSummary {
  corridorId: string;
  roadId: string;
  name: string;
  knownCurbRamps: number;
  possibleMissingCurbCuts: number;
  hydrantsNearby: number;
  bikeLanesNearby: number;
  userAnnotationsNearby: number;
  busStopsNearby: number;
  parkingConflicts: number;
  bikeLaneFeasibility: "Low" | "Medium" | "High";
  planningNotes: string[];
}
