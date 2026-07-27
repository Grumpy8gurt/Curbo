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
  return (
    <div className="field-stack">
      <label className="field-label" htmlFor="corridor-selector">
        Corridor prototype
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
        {roads.map((road) => (
          <option key={road.properties.road_id} value={road.properties.road_id}>
            {getRoadOptionLabel(road)}
          </option>
        ))}
      </select>
      <p className="helper-text">
        {loading
          ? "Analyzing selected corridor..."
          : "You can also click a road directly on the map."}
      </p>
    </div>
  );
}
