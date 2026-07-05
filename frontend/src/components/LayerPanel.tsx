import { LAYER_OPTIONS, type LayerId, type LayerVisibility } from "../types/layers";

interface LayerPanelProps {
  visibility: LayerVisibility;
  onToggle: (layerId: LayerId) => void;
}

export function LayerPanel({ visibility, onToggle }: LayerPanelProps) {
  return (
    <div className="layer-list">
      {LAYER_OPTIONS.map((layer) => (
        <label
          key={layer.id}
          className={`layer-item ${layer.disabled ? "is-disabled" : ""}`}
        >
          <span>
            <input
              type="checkbox"
              checked={visibility[layer.id]}
              onChange={() => onToggle(layer.id)}
              disabled={layer.disabled}
            />
            {layer.label}
          </span>
          {layer.disabled ? <small>placeholder</small> : <small>live mock</small>}
        </label>
      ))}
    </div>
  );
}
