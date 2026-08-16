import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CorridorSelector } from "./CorridorSelector";
import { Header } from "./Header";
import { LayerPanel } from "./LayerPanel";
import { DEFAULT_LAYER_VISIBILITY } from "../types/layers";

describe("product-facing language", () => {
  it("presents CURBO as a civic mobility application", () => {
    render(<Header />);

    expect(screen.getByRole("heading", { name: "CURBO" })).toBeInTheDocument();
    expect(screen.getByText("Eugene, Oregon")).toBeInTheDocument();
    expect(screen.getByText("Civic mobility review")).toBeInTheDocument();
    expect(screen.queryByText(/sprint/i)).not.toBeInTheDocument();
  });

  it("uses operational labels without exposing implementation status", () => {
    render(
      <>
        <CorridorSelector
          roads={[]}
          selectedRoadId={null}
          loading={false}
          onSelect={vi.fn()}
        />
        <LayerPanel
          visibility={DEFAULT_LAYER_VISIBILITY}
          layerCounts={{
            roads: 10,
            sidewalkRamps: 3,
            hydrants: 4,
            bikeLanes: 1,
            annotations: 2
          }}
          onToggle={vi.fn()}
        />
      </>
    );

    expect(screen.getByLabelText("Road corridor")).toBeInTheDocument();
    expect(screen.getByText("On · 10")).toBeInTheDocument();
    expect(screen.queryByText(/prototype|fallback|backend|frontend/i)).not.toBeInTheDocument();
  });
});
