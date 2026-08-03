/** Result returned by POST /api/reports/corridor. */
export interface CorridorReportResult {
  reportId: string;
  roadId: string;
  // Relative URL — the frontend prepends API_BASE_URL before opening.
  // Empty string in fallback mode; the backend is required for a real download.
  downloadUrl: string;
  summary: string;
}
