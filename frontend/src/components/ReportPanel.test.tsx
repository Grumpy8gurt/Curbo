import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ReportPanel } from "./ReportPanel";
import type { CorridorSummary } from "../types/corridors";

const summary: CorridorSummary = {
  corridorId: "cor_road_1",
  roadId: "road_1",
  name: "Test Avenue",
  knownCurbRamps: 2,
  possibleMissingCurbCuts: 1,
  hydrantsNearby: 1,
  bikeLanesNearby: 0,
  userAnnotationsNearby: 4,
  busStopsNearby: 0,
  parkingConflicts: 1,
  bikeLaneGaps: 1,
  intersectionSafetyConcerns: 1,
  annotationsNeedingReview: 2,
  bikeLaneFeasibility: "Medium",
  reviewPriority: "High",
  reviewSignals: ["1 active bike-lane gap observation near the corridor."],
  dataLimitation: "Screening only: current crash, speed, and volume data are unavailable.",
  planningNotes: ["Field-check the intersection."]
};

describe("ReportPanel", () => {
  it("shows review attention, concern categories, signals, and limitations", () => {
    render(
      <ReportPanel
        summary={summary}
        reportResult={null}
        generating={false}
        onGenerate={vi.fn()}
      />
    );

    expect(screen.getByText("High review attention")).toBeInTheDocument();
    expect(screen.getByText("Bike-network gaps")).toBeInTheDocument();
    expect(screen.getByText("Intersection safety")).toBeInTheDocument();
    expect(screen.getByText("1 active bike-lane gap observation near the corridor.")).toBeInTheDocument();
    expect(screen.getByText(/current crash, speed, and volume/)).toBeInTheDocument();
  });
});
