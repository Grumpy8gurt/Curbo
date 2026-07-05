import type { SelectedFeatureDetails } from "../utils/mapHelpers";

interface FeaturePopupProps {
  feature: SelectedFeatureDetails | null;
}

export function FeaturePopup({ feature }: FeaturePopupProps) {
  if (!feature) {
    return (
      <div className="feature-popup is-empty">
        <p>Click a road, asset, annotation, or detection to inspect it.</p>
      </div>
    );
  }

  return (
    <div className="feature-popup">
      <div className="card-topline">
        <strong>{feature.title}</strong>
        <span className="feature-tag">{feature.layerId}</span>
      </div>
      <p>{feature.subtitle}</p>
      <p>Source: {feature.source}</p>
      {feature.status ? <p>Status: {feature.status}</p> : null}
      {feature.confidence !== undefined ? (
        <p>Confidence: {(feature.confidence * 100).toFixed(0)}%</p>
      ) : null}
      {feature.notes ? <p>Notes: {feature.notes}</p> : null}
      <p>
        Location: {feature.coordinates[1].toFixed(4)}, {feature.coordinates[0].toFixed(4)}
      </p>
    </div>
  );
}
