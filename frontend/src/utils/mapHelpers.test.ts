import { describe, expect, it } from "vitest";
import type { Feature } from "../types/geojson";
import {
  getCurbRampFieldReviewPrompts,
  toSelectedFeatureDetails
} from "./mapHelpers";
import type { CurbRampProperties } from "../types/layers";

function rampFeature(properties: Partial<CurbRampProperties>): Feature {
  return {
    type: "Feature",
    properties: {
      ramp_id: "ramp_test",
      status: "existing",
      condition: "not assessed",
      ...properties
    },
    geometry: { type: "Point", coordinates: [-123.08, 44.05] }
  };
}

describe("curb-ramp field-review helpers", () => {
  it("preserves side-specific grades and produces explainable screening prompts", () => {
    const details = toSelectedFeatureDetails(
      "sidewalkRamps",
      rampFeature({
        width_feet: 3.5,
        left_grade_percent: 8.6,
        right_grade_percent: 7.2,
        left_cross_slope_percent: 2.9
      })
    );

    expect(details.measurements).toContain("Left grade: 8.6 %");
    expect(details.measurements).toContain("Right grade: 7.2 %");
    expect(details.fieldReviewPrompts).toEqual([
      "Width 3.5 ft is below the 4 ft field-review reference.",
      "Left grade 8.6% exceeds the 8.33% field-review reference.",
      "Left cross slope 2.9% exceeds the 2.08% field-review reference."
    ]);
    expect(details.screeningDisclaimer).toMatch(/not an accessibility-compliance finding/);
  });

  it("does not flag values exactly on the published dimensional references", () => {
    const prompts = getCurbRampFieldReviewPrompts({
      ramp_id: "ramp_boundary",
      status: "existing",
      condition: "not assessed",
      width_feet: 4,
      grade_percent: 8.33,
      cross_slope_percent: 2.08
    });

    expect(prompts).toEqual([]);
  });

  it("suppresses nonpositive width sentinels while preserving valid zero slopes", () => {
    const details = toSelectedFeatureDetails(
      "sidewalkRamps",
      rampFeature({ width_feet: 0, left_width_feet: -1, grade_percent: 0 })
    );

    expect(details.measurements).toEqual(["Grade: 0 %"]);
    expect(details.fieldReviewPrompts).toEqual([]);
  });
});
