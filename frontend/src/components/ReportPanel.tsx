import type { CorridorSummary } from "../types/corridors";
import type { CorridorReportResult } from "../types/reports";

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
          <strong>{summary.name}</strong>
          <span className="rating-pill">{summary.bikeLaneFeasibility} feasibility</span>
        </div>
        <div className="metrics-grid">
          <div>
            <span>Known curb ramps</span>
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
            <span>Parking conflicts</span>
            <strong>{summary.parkingConflicts}</strong>
          </div>
          <div>
            <span>Bus stops</span>
            <strong>{summary.busStopsNearby}</strong>
          </div>
        </div>
        <div className="notes-list">
          {summary.planningNotes.map((note) => (
            <p key={note}>{note}</p>
          ))}
        </div>
      </article>

      <button className="primary-button" type="button" onClick={onGenerate} disabled={generating}>
        {generating ? "Generating..." : "Generate Report"}
      </button>

      {reportResult ? <p className="success-callout">{reportResult.summary}</p> : null}
    </div>
  );
}
