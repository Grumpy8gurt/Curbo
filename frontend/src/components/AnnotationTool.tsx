import { useState } from "react";
import type {
  AnnotationDraft,
  AnnotationDrawMode,
  AnnotationGeometry,
  AnnotationKind
} from "../types/annotations";
import type { Position } from "../types/geojson";

interface AnnotationToolProps {
  geometry: AnnotationGeometry | null;
  drawingMode: AnnotationDrawMode | null;
  drawingPointCount: number;
  onStartDrawing: (mode: AnnotationDrawMode) => void;
  onFinishDrawing: () => void;
  onCancelDrawing: () => void;
  onUseManualPoint: (position: Position) => void;
  onCreate: (annotation: AnnotationDraft) => Promise<void>;
}

export function AnnotationTool({
  geometry,
  drawingMode,
  drawingPointCount,
  onStartDrawing,
  onFinishDrawing,
  onCancelDrawing,
  onUseManualPoint,
  onCreate
}: AnnotationToolProps) {
  const [annotationType, setAnnotationType] = useState<AnnotationKind>("curb cut");
  const [description, setDescription] = useState("");
  const [latitude, setLatitude] = useState(44.0521);
  const [longitude, setLongitude] = useState(-123.0868);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!geometry || drawingMode) {
      setErrorMessage("Place and finish a point or line before saving.");
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);
    try {
      await onCreate({ annotationType, description, geometry });
      setDescription("");
    } catch {
      setErrorMessage("The annotation could not be saved. Check the values and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="field-stack" onSubmit={handleSubmit}>
      <label className="field-label">
        Type
        <select
          className="select-input"
          value={annotationType}
          onChange={(event) => setAnnotationType(event.target.value as AnnotationKind)}
        >
          <option value="curb cut">Curb cut location</option>
          <option value="missing curb cut">Missing curb cut</option>
          <option value="fire hydrant">Fire hydrant location</option>
          <option value="bike lane gap">Bike-lane gap</option>
          <option value="proposed bike lane">Proposed bike lane</option>
          <option value="parking/loading conflict">Parking or loading conflict</option>
          <option value="intersection safety">Intersection safety</option>
          <option value="drainage/utility conflict">Drainage or utility conflict</option>
          <option value="bad data">Bad data</option>
          <option value="obstruction">Obstruction</option>
          <option value="other">Other</option>
        </select>
      </label>

      <fieldset className="placement-fieldset">
        <legend>Map placement</legend>
        <div className="button-row placement-buttons">
          <button
            className="secondary-button"
            type="button"
            onClick={() => onStartDrawing("point")}
          >
            Place point
          </button>
          <button
            className="secondary-button"
            type="button"
            onClick={() => onStartDrawing("line")}
          >
            Draw line
          </button>
        </div>
        {drawingMode ? (
          <div className="drawing-callout" role="status">
            <p>
              {drawingMode === "point"
                ? "Click once on the map."
                : `Click along the route (${drawingPointCount} point${
                    drawingPointCount === 1 ? "" : "s"
                  }).`}
            </p>
            <div className="button-row">
              {drawingMode === "line" ? (
                <button
                  className="primary-button"
                  type="button"
                  disabled={drawingPointCount < 2}
                  onClick={onFinishDrawing}
                >
                  Finish line
                </button>
              ) : null}
              <button className="ghost-button" type="button" onClick={onCancelDrawing}>
                Cancel
              </button>
            </div>
          </div>
        ) : geometry ? (
          <p className="success-callout">
            {geometry.type === "Point"
              ? "Point ready to save."
              : `Line ready with ${geometry.coordinates.length} points.`}
          </p>
        ) : (
          <p className="helper-text">Choose a placement tool, then click the map.</p>
        )}
      </fieldset>

      <label className="field-label">
        Description
        <textarea
          className="text-input textarea-input"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Describe what is present, missing, or likely to affect a bike lane."
          required
        />
      </label>

      <details className="coordinate-fallback">
        <summary>Enter point coordinates instead</summary>
        <div className="form-row">
          <label className="field-label">
            Latitude
            <input
              className="text-input"
              type="number"
              step="0.0001"
              min="-90"
              max="90"
              value={latitude}
              onChange={(event) => setLatitude(Number(event.target.value))}
              required
            />
          </label>
          <label className="field-label">
            Longitude
            <input
              className="text-input"
              type="number"
              step="0.0001"
              min="-180"
              max="180"
              value={longitude}
              onChange={(event) => setLongitude(Number(event.target.value))}
              required
            />
          </label>
        </div>
        <button
          className="ghost-button coordinate-button"
          type="button"
          onClick={() => onUseManualPoint([longitude, latitude])}
        >
          Use these coordinates
        </button>
      </details>

      <button
        className="primary-button"
        type="submit"
        disabled={submitting || !geometry || drawingMode !== null}
      >
        {submitting ? "Saving..." : "Add annotation"}
      </button>
      {errorMessage ? <p className="error-callout">{errorMessage}</p> : null}
    </form>
  );
}
