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
    The summary dict is rendered as a <pre> block for now — a future sprint
    can template individual fields into a formatted table.

    Returns the absolute path to the written file so the caller can register it
    in the store and serve it via the download endpoint.
    """
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{report_id}.html"
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
      code {{
        background: #f1f5f9;
        padding: 0.15rem 0.3rem;
      }}
    </style>
  </head>
  <body>
    <h1>CURBO Corridor Report</h1>
    <p><strong>Road:</strong> {escape(str(summary.get("name", summary.get("roadId", ""))))}</p>
    <p><strong>Feasibility:</strong> {escape(str(summary.get("bikeLaneFeasibility", "unknown")))}</p>
    <h2>Layers Included</h2>
    <p>{escape(", ".join(include_layers) if include_layers else "None requested")}</p>
    <h2>Summary</h2>
    <pre>{escape(str(summary))}</pre>
  </body>
</html>
"""
    report_path.write_text(html, encoding="utf-8")
    return report_path
