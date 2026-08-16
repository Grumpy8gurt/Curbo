import { useDeferredValue, useMemo, useState } from "react";
import { getRoadOptionLabel } from "../utils/mapHelpers";
import type { RoadFeature } from "../types/layers";

interface CorridorSelectorProps {
  roads: RoadFeature[];
  selectedRoadId: string | null;
  loading?: boolean;
  onSelect: (roadId: string) => void;
}

export function CorridorSelector({
  roads,
  selectedRoadId,
  loading,
  onSelect
}: CorridorSelectorProps) {
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query.trim().toLocaleLowerCase());
  const visibleRoads = useMemo(() => {
    const matches = deferredQuery
      ? roads.filter((road) =>
          getRoadOptionLabel(road).toLocaleLowerCase().includes(deferredQuery)
        )
      : roads;
    const firstMatches = matches.slice(0, 50);
    const selected = roads.find(
      (road) => road.properties.road_id === selectedRoadId
    );
    if (
      selected &&
      !firstMatches.some(
        (road) => road.properties.road_id === selected.properties.road_id
      )
    ) {
      return [selected, ...firstMatches.slice(0, 49)];
    }
    return firstMatches;
  }, [deferredQuery, roads, selectedRoadId]);

  return (
    <div className="field-stack">
      <label className="field-label" htmlFor="corridor-search">
        Search roads
      </label>
      <input
        id="corridor-search"
        className="text-input"
        type="search"
        value={query}
        placeholder="Start typing a road name"
        onChange={(event) => setQuery(event.target.value)}
      />
      <label className="field-label" htmlFor="corridor-selector">
        Road corridor
      </label>
      {/* Empty string value represents "no selection"; onSelect receives an
          empty string which App.tsx treats as clearing the corridor. */}
      <select
        id="corridor-selector"
        className="select-input"
        value={selectedRoadId ?? ""}
        onChange={(event) => onSelect(event.target.value)}
      >
        <option value="">Choose a road corridor</option>
        {visibleRoads.map((road) => (
          <option key={road.properties.road_id} value={road.properties.road_id}>
            {getRoadOptionLabel(road)}
          </option>
        ))}
      </select>
      <p className="helper-text">
        {loading
          ? "Analyzing selected corridor..."
          : `Showing ${visibleRoads.length} of ${roads.length} roads. You can also click a road on the map.`}
      </p>
    </div>
  );
}
