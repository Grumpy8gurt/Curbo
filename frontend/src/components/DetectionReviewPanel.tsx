import type {
  DetectionFeature,
  DetectionReviewStatus
} from "../types/detections";

interface DetectionReviewPanelProps {
  detections: DetectionFeature[];
  onReview: (detectionId: string, status: DetectionReviewStatus) => Promise<void>;
}

export function DetectionReviewPanel({
  detections,
  onReview
}: DetectionReviewPanelProps) {
  return (
    <div className="card-list">
      {detections.length === 0 ? (
        <p className="empty-state">No detections yet. Upload an image to create one.</p>
      ) : null}

      {detections.map((feature) => {
        const { detection_id, label, confidence, review_status } = feature.properties;
        const [longitude, latitude] = feature.geometry.coordinates;

        return (
          <article className="info-card" key={detection_id}>
            <div className="card-topline">
              <strong>{label}</strong>
              <span className={`status-pill status-${review_status}`}>{review_status}</span>
            </div>
            <p>Confidence: {(confidence * 100).toFixed(0)}%</p>
            <p>
              Approx. location: {latitude.toFixed(4)}, {longitude.toFixed(4)}
            </p>
            <div className="button-row">
              <button
                className="secondary-button"
                type="button"
                onClick={() => onReview(detection_id, "confirmed")}
              >
                Confirm
              </button>
              <button
                className="ghost-button"
                type="button"
                onClick={() => onReview(detection_id, "rejected")}
              >
                Reject
              </button>
            </div>
          </article>
        );
      })}
    </div>
  );
}
