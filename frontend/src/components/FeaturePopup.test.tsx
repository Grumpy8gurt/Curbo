import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { FeaturePopup } from "./FeaturePopup";
import type { SelectedFeatureDetails } from "../utils/mapHelpers";

describe("FeaturePopup", () => {
  it("sends annotation status changes through the review callback", async () => {
    const onStatusChange = vi.fn().mockResolvedValue(undefined);
    const feature: SelectedFeatureDetails = {
      id: "ann_004",
      layerId: "annotations",
      title: "missing curb cut",
      subtitle: "Planner annotation",
      source: "frontend",
      status: "pending",
      notes: "Ramp is absent.",
      coordinates: [-123.08, 44.05]
    };

    render(
      <FeaturePopup
        feature={feature}
        onAnnotationStatusChange={onStatusChange}
      />
    );
    fireEvent.change(screen.getByLabelText("Review status"), {
      target: { value: "reviewed" }
    });

    await waitFor(() =>
      expect(onStatusChange).toHaveBeenCalledWith("ann_004", "reviewed")
    );
  });

  it("shows available curb-ramp dimensions", () => {
    const feature: SelectedFeatureDetails = {
      id: "ramp_42",
      layerId: "sidewalkRamps",
      title: "ramp_42",
      subtitle: "Sidewalk ramp",
      source: "City of Eugene GIS",
      status: "existing",
      measurements: ["Left width: 3.5 ft", "Left grade: 8.6 %"],
      fieldReviewPrompts: [
        "Left width 3.5 ft is below the 4 ft field-review reference.",
        "Left grade 8.6% exceeds the 8.33% field-review reference."
      ],
      screeningDisclaimer:
        "Screening only: published measurements are field-review prompts, not an accessibility-compliance finding.",
      coordinates: [-123.08, 44.05]
    };

    render(
      <FeaturePopup
        feature={feature}
        onAnnotationStatusChange={vi.fn()}
      />
    );

    expect(screen.getByText("Dimensions")).toBeInTheDocument();
    expect(screen.getByText("Left width: 3.5 ft")).toBeInTheDocument();
    expect(screen.getByText("Left grade: 8.6 %")).toBeInTheDocument();
    expect(screen.getByText("Field-review prompts")).toBeInTheDocument();
    expect(screen.getByText(/not an accessibility-compliance finding/)).toBeInTheDocument();
  });
});
