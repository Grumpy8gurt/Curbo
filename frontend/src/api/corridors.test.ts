import { afterEach, describe, expect, it, vi } from "vitest";
import { analyzeCorridor } from "./corridors";

describe("analyzeCorridor", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("posts the road id and preserves the review evidence contract", async () => {
    const response = {
      corridorId: "cor_road_1",
      roadId: "road_1",
      name: "Test Avenue",
      knownCurbRamps: 0,
      possibleMissingCurbCuts: 0,
      hydrantsNearby: 0,
      bikeLanesNearby: 0,
      userAnnotationsNearby: 0,
      busStopsNearby: 0,
      parkingConflicts: 0,
      bikeLaneGaps: 0,
      intersectionSafetyConcerns: 0,
      annotationsNeedingReview: 0,
      bikeLaneFeasibility: "Low",
      reviewPriority: "Low",
      reviewSignals: ["No mapped bicycle facility."],
      dataLimitation: "Screening only.",
      planningNotes: []
    };
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify(response), { status: 200 }));

    const result = await analyzeCorridor("road_1");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/corridors/analyze",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ roadId: "road_1" })
      })
    );
    expect(result.reviewPriority).toBe("Low");
    expect(result.dataLimitation).toBe("Screening only.");
  });
});
