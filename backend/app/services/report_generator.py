from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


def generate_corridor_report(
    report_dir: Path,
    report_id: str,
    summary: dict[str, Any],
    include_layers: list[str],
) -> Path:
    """
    Write a self-contained HTML corridor report to `report_dir/<report_id>.html`.

    All dynamic values are HTML-escaped via `html.escape` to prevent XSS if
    planner-supplied text (e.g. road names) ever contains angle brackets.
    The report uses labeled metrics and lists so it can be read in a review
    meeting without exposing Python's internal dictionary representation.

    Returns the absolute path to the written file so the caller can register it
    in the store and serve it via the download endpoint.
    """
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{report_id}.html"
    metrics = (
        ("Known sidewalk ramps", summary.get("knownCurbRamps", 0)),
        ("Possible missing curb cuts", summary.get("possibleMissingCurbCuts", 0)),
        ("Mapped bicycle facilities", summary.get("bikeLanesNearby", 0)),
        ("Bicycle-network gaps", summary.get("bikeLaneGaps", 0)),
        ("Intersection-safety observations", summary.get("intersectionSafetyConcerns", 0)),
        ("Parking/loading conflicts", summary.get("parkingConflicts", 0)),
        ("Annotations needing review", summary.get("annotationsNeedingReview", 0)),
        ("All nearby annotations", summary.get("userAnnotationsNearby", 0)),
        ("Hydrants nearby", summary.get("hydrantsNearby", 0)),
    )
    metric_rows = "\n".join(
        "        <tr>"
        f"<th scope=\"row\">{escape(label)}</th>"
        f"<td>{escape(str(value))}</td>"
        "</tr>"
        for label, value in metrics
    )
    review_signals = summary.get("reviewSignals") or ["No review signals were generated."]
    signal_items = "\n".join(f"        <li>{escape(str(item))}</li>" for item in review_signals)
    planning_notes = summary.get("planningNotes") or ["No planning notes were generated."]
    note_items = "\n".join(f"        <li>{escape(str(item))}</li>" for item in planning_notes)
    layer_items = "\n".join(
        f"        <li>{escape(str(layer))}</li>" for layer in include_layers
    ) or "        <li>None requested</li>"
    html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{escape(report_id)}</title>
    <style>
      body {{
        font-family: Helvetica, Arial, sans-serif;
        margin: 2rem auto;
        max-width: 760px;
        line-height: 1.5;
        color: #1f2933;
      }}
      h1, h2 {{
        color: #0f5f53;
      }}
      table {{
        width: 100%;
        border-collapse: collapse;
      }}
      th, td {{
        border-bottom: 1px solid #d7e0e5;
        padding: 0.65rem 0;
        text-align: left;
      }}
      td {{
        text-align: right;
        font-weight: 700;
      }}
      .limitation {{
        border-left: 4px solid #b7791f;
        background: #fffbeb;
        padding: 0.75rem 1rem;
      }}
    </style>
  </head>
  <body>
    <h1>CURBO Corridor Report</h1>
    <p><strong>Road:</strong> {escape(str(summary.get("name", summary.get("roadId", ""))))}</p>
    <p><strong>Review attention:</strong> {escape(str(summary.get("reviewPriority", "unknown")))}</p>
    <p><strong>Preliminary bicycle feasibility:</strong> {escape(str(summary.get("bikeLaneFeasibility", "unknown")))}</p>
    <h2>Screening Metrics</h2>
    <table>
      <tbody>
{metric_rows}
      </tbody>
    </table>
    <h2>Review Signals</h2>
    <ul>
{signal_items}
    </ul>
    <h2>Planning Notes</h2>
    <ul>
{note_items}
    </ul>
    <h2>Data Limitations</h2>
    <p class="limitation">{escape(str(summary.get("dataLimitation", "No limitation statement was provided.")))}</p>
    <h2>Layers Included</h2>
    <ul>
{layer_items}
    </ul>
  </body>
</html>
"""
    report_path.write_text(html, encoding="utf-8")
    return report_path
