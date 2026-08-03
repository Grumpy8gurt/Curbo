import { LAYER_OPTIONS, type LayerId, type LayerVisibility } from "../types/layers";

interface LayerPanelProps {
  visibility: LayerVisibility;
  layerCounts: Record<LayerId, number>;
  layerStatuses: Partial<Record<LayerId, string>>;
  onToggle: (layerId: LayerId) => void;
}

export function LayerPanel({
  visibility,
  layerCounts,
  layerStatuses,
  onToggle
}: LayerPanelProps) {
  return (
    <div className="layer-list">
      {LAYER_OPTIONS.map((layer) => (
        // The "is-disabled" class greys out the row when the layer has no
        // features (e.g. bike_lanes with no cache file).
        <label
          key={layer.id}
          className={`layer-item ${layerCounts[layer.id] === 0 ? "is-disabled" : ""} ${
            visibility[layer.id] ? "is-visible" : "is-hidden"
          }`}
        >
          <span>
            <input
              type="checkbox"
              checked={visibility[layer.id]}
              onChange={() => onToggle(layer.id)}
            />
            {layer.label}
          </span>
          {/* Show feature count and data status ("cached-eugene", "sample-fallback",
              etc.) so planners know whether they are looking at live city data. */}
          <small>
            {layerCounts[layer.id] === 0
              ? "unavailable"
              : `${visibility[layer.id] ? "On" : "Off"} · ${layerCounts[layer.id]} · ${
                  layerStatuses[layer.id] ?? "loaded"
                }`}
          </small>
        </label>
      ))}
    </div>
  );
}
