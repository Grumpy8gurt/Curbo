import { useState } from "react";
import type { AnnotationStatus } from "../types/annotations";
import type { SelectedFeatureDetails } from "../utils/mapHelpers";

interface FeaturePopupProps {
  feature: SelectedFeatureDetails | null;
  onAnnotationStatusChange: (
    annotationId: string,
    status: AnnotationStatus
  ) => Promise<void>;
}

const STATUS_OPTIONS: AnnotationStatus[] = [
  "pending",
  "reviewed",
  "confirmed",
  "rejected"
];

export function FeaturePopup({
  feature,
  onAnnotationStatusChange
}: FeaturePopupProps) {
  const [savingStatus, setSavingStatus] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);

  if (!feature) {
    return (
      <div className="feature-popup is-empty">
        <p>Click a road, asset, or annotation to inspect it.</p>
      </div>
    );
  }

  async function handleStatusChange(status: AnnotationStatus) {
    if (!feature) {
      return;
    }
    setSavingStatus(true);
    setStatusError(null);
    try {
      await onAnnotationStatusChange(feature.id, status);
    } catch {
      setStatusError("Status could not be saved. Try again.");
    } finally {
      setSavingStatus(false);
    }
  }

  return (
    <div className="feature-popup">
      <div className="card-topline">
        <strong>{feature.title}</strong>
        <span className="feature-tag">{feature.layerId}</span>
      </div>
      <p>{feature.subtitle}</p>
      <p>Source: {feature.source}</p>
      {feature.geometryLabel ? <p>Geometry: {feature.geometryLabel}</p> : null}
      {feature.layerId === "annotations" && feature.status ? (
        <label className="field-label feature-status-control">
          Review status
          <select
            className="select-input"
            value={feature.status}
            disabled={savingStatus}
            onChange={(event) =>
              void handleStatusChange(event.target.value as AnnotationStatus)
            }
          >
            {STATUS_OPTIONS.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </label>
      ) : feature.status ? (
        <p>Status: {feature.status}</p>
      ) : null}
      {feature.notes ? <p>Notes: {feature.notes}</p> : null}
      {feature.measurements?.length ? (
        <div>
          <strong>Dimensions</strong>
          <ul className="measurement-list">
            {feature.measurements.map((measurement) => (
              <li key={measurement}>{measurement}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {feature.fieldReviewPrompts?.length ? (
        <div className="field-review-callout">
          <strong>Field-review prompts</strong>
          <ul>
            {feature.fieldReviewPrompts.map((prompt) => (
              <li key={prompt}>{prompt}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {feature.screeningDisclaimer ? (
        <p className="screening-disclaimer">{feature.screeningDisclaimer}</p>
      ) : null}
      {statusError ? <p className="error-callout">{statusError}</p> : null}
      <p>
        Location: {feature.coordinates[1].toFixed(4)}, {feature.coordinates[0].toFixed(4)}
      </p>
    </div>
  );
}
