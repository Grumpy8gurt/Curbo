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
    <h1>Curbo Corridor Report</h1>
    <p><strong>Road:</strong> {escape(str(summary.get("road_name", summary.get("road_id", ""))))}</p>
    <p><strong>Feasibility:</strong> {escape(str(summary.get("bike_lane_feasibility", "unknown")))}</p>
    <h2>Layers Included</h2>
    <p>{escape(", ".join(include_layers) if include_layers else "None requested")}</p>
    <h2>Summary</h2>
    <pre>{escape(str(summary))}</pre>
  </body>
</html>
"""
    report_path.write_text(html, encoding="utf-8")
    return report_path
