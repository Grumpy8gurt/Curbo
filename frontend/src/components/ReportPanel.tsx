import type { CorridorSummary } from "../types/corridors";
import type { CorridorReportResult } from "../types/reports";
import { apiUrl } from "../api/client";

interface ReportPanelProps {
  summary: CorridorSummary | null;
  reportResult: CorridorReportResult | null;
  generating: boolean;
  onGenerate: () => Promise<void>;
}

export function ReportPanel({
  summary,
  reportResult,
  generating,
  onGenerate
}: ReportPanelProps) {
  if (!summary) {
    return <p className="empty-state">Select a road corridor to view a summary report.</p>;
  }

  return (
    <div className="field-stack">
      <article className="summary-card">
        <div className="card-topline">
          <div>
            <span className="card-kicker">Selected corridor</span>
            <strong>{summary.name}</strong>
          </div>
          <span className={`rating-pill priority-${summary.reviewPriority.toLowerCase()}`}>
            {summary.reviewPriority} review attention
          </span>
        </div>
        <p className="feasibility-line">
          Preliminary bicycle feasibility: <strong>{summary.bikeLaneFeasibility}</strong>
        </p>
        <div className="metrics-grid">
          <div>
            <span>Sidewalk ramps</span>
            <strong>{summary.knownCurbRamps}</strong>
          </div>
          <div>
            <span>Missing curb cuts</span>
            <strong>{summary.possibleMissingCurbCuts}</strong>
          </div>
          <div>
            <span>Hydrants nearby</span>
            <strong>{summary.hydrantsNearby}</strong>
          </div>
          <div>
            <span>Mapped bike facilities</span>
            <strong>{summary.bikeLanesNearby}</strong>
          </div>
          <div>
            <span>Bike-network gaps</span>
            <strong>{summary.bikeLaneGaps}</strong>
          </div>
          <div>
            <span>Intersection safety</span>
            <strong>{summary.intersectionSafetyConcerns}</strong>
          </div>
          <div>
            <span>Parking/loading</span>
            <strong>{summary.parkingConflicts}</strong>
          </div>
          <div>
            <span>Needs review</span>
            <strong>{summary.annotationsNeedingReview}</strong>
          </div>
          <div>
            <span>All annotations</span>
            <strong>{summary.userAnnotationsNearby}</strong>
          </div>
        </div>
        <section className="summary-section" aria-labelledby="review-signals-heading">
          <h3 id="review-signals-heading">Review signals</h3>
          <ul className="review-signal-list">
            {summary.reviewSignals.map((signal) => (
              <li key={signal}>{signal}</li>
            ))}
          </ul>
        </section>
        <section className="summary-section notes-list" aria-labelledby="planning-notes-heading">
          <h3 id="planning-notes-heading">Planning notes</h3>
          {summary.planningNotes.map((note) => (
            <p key={note}>{note}</p>
          ))}
        </section>
        <p className="data-limitation">{summary.dataLimitation}</p>
      </article>

      <button className="primary-button" type="button" onClick={onGenerate} disabled={generating}>
        {generating ? "Generating..." : "Generate Report"}
      </button>

      {reportResult ? (
        <div className="success-callout">
          <p>{reportResult.summary}</p>
          {/* downloadUrl is empty in the fallback mode; the backend is needed
              to serve the HTML file via the /api/reports/{id}/download endpoint. */}
          {reportResult.downloadUrl ? (
            <a href={apiUrl(reportResult.downloadUrl)} target="_blank" rel="noreferrer">
              Download HTML report
            </a>
          ) : (
            <small>Report download is unavailable in this session.</small>
          )}
        </div>
      ) : null}
    </div>
  );
}
