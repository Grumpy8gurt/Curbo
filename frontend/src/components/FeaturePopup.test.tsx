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
      measurements: ["Left width: 4.9 ft", "Left cross slope: 1.1 %"],
      coordinates: [-123.08, 44.05]
    };

    render(
      <FeaturePopup
        feature={feature}
        onAnnotationStatusChange={vi.fn()}
      />
    );

    expect(screen.getByText("Dimensions")).toBeInTheDocument();
    expect(screen.getByText("Left width: 4.9 ft")).toBeInTheDocument();
    expect(screen.getByText("Left cross slope: 1.1 %")).toBeInTheDocument();
  });
});
