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
        <label
          key={layer.id}
          className={`layer-item ${layerCounts[layer.id] === 0 ? "is-disabled" : ""}`}
        >
          <span>
            <input
              type="checkbox"
              checked={visibility[layer.id]}
              onChange={() => onToggle(layer.id)}
            />
            {layer.label}
          </span>
          <small>
            {layerCounts[layer.id] === 0
              ? "unavailable"
              : `${layerCounts[layer.id]} · ${layerStatuses[layer.id] ?? "loaded"}`}
          </small>
        </label>
      ))}
    </div>
  );
}
