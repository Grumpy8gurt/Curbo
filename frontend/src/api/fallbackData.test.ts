import { describe, expect, it } from "vitest";
import {
  addFallbackAnnotation,
  createFallbackReport,
  getFallbackCorridorSummary,
  updateFallbackAnnotation
} from "./fallbackData";

describe("fallback corridor analysis", () => {
  it("keeps rejected concerns in history without treating them as active", () => {
    const roadId = "road_rd_001";
    const baseline = getFallbackCorridorSummary(roadId);
    const created = addFallbackAnnotation({
      annotationType: "bike lane gap",
      description: "Offline status-aware review",
      geometry: { type: "Point", coordinates: [-123.0912, 44.0516] }
    });

    const pending = getFallbackCorridorSummary(roadId);
    expect(pending.bikeLaneGaps).toBe(baseline.bikeLaneGaps + 1);
    expect(pending.annotationsNeedingReview).toBe(
      baseline.annotationsNeedingReview + 1
    );

    updateFallbackAnnotation(created.properties.annotation_id, "rejected");
    const rejected = getFallbackCorridorSummary(roadId);
    expect(rejected.bikeLaneGaps).toBe(baseline.bikeLaneGaps);
    expect(rejected.userAnnotationsNearby).toBe(baseline.userAnnotationsNearby + 1);
  });

  it("returns a product-facing report preview message", () => {
    const report = createFallbackReport("road_rd_001", "Willamette Street");

    expect(report.summary).toBe("Willamette Street report preview is ready.");
    expect(report.summary).not.toMatch(/backend|local|fallback/i);
  });
});
