"""
Reporting module for generating analysis reports.

Supports multiple output formats:
- Console/Terminal (pretty tables)
- JSON (machine-readable)
- CSV (spreadsheet compatible)
- HTML (web-friendly)
"""

import csv
import json
from datetime import datetime, timezone
from typing import Any

from ..core.logging import get_logger
from ..core.models import AnalysisResult

logger = get_logger(__name__)


class ReportGenerator:
    """Generate reports from analysis results"""

    def __init__(self):
        self.timestamp = datetime.now(timezone.utc)

    def generate_summary(self, analysis: AnalysisResult) -> dict[str, Any]:
        """
        Generate summary statistics

        Args:
            analysis: Analysis result

        Returns:
            Dictionary with summary statistics
        """
        anomalies = analysis.anomalies

        # Count by severity
        severity_counts = {
            "critical": len([a for a in anomalies if a.severity == "critical"]),
            "high": len([a for a in anomalies if a.severity == "high"]),
            "medium": len([a for a in anomalies if a.severity == "medium"]),
            "low": len([a for a in anomalies if a.severity == "low"]),
        }

        # Count by type
        type_counts = {}
        for anomaly in anomalies:
            type_counts[anomaly.anomaly_type] = type_counts.get(anomaly.anomaly_type, 0) + 1

        # Top anomalies
        top_anomalies = sorted(anomalies, key=lambda x: x.confidence, reverse=True)[:10]

        return {
            "timestamp": self.timestamp.isoformat(),
            "total_entries": analysis.total_entries,
            "total_anomalies": len(anomalies),
            "severity_breakdown": severity_counts,
            "type_breakdown": type_counts,
            "critical_count": severity_counts["critical"],
            "high_risk_count": severity_counts["critical"] + severity_counts["high"],
            "top_anomalies": [
                {
                    "type": a.anomaly_type,
                    "severity": a.severity,
                    "confidence": a.confidence,
                    "description": a.description[:100],
                }
                for a in top_anomalies
            ],
            "patterns_detected": len(analysis.patterns),
        }

    def export_json(self, analysis: AnalysisResult, output_path: str) -> None:
        """
        Export analysis results to JSON

        Args:
            analysis: Analysis result
            output_path: Path to output file
        """
        data = {
            "metadata": {
                "generated_at": self.timestamp.isoformat(),
                "loggem_version": "0.1.0",
            },
            "summary": self.generate_summary(analysis),
            "anomalies": [
                {
                    "type": a.anomaly_type,
                    "severity": a.severity,
                    "confidence": a.confidence,
                    "description": a.description,
                    "recommendation": a.recommendation,
                    "timestamp": a.log_entry.timestamp.isoformat() if a.log_entry else None,
                    "source": a.log_entry.source if a.log_entry else None,
                }
                for a in analysis.anomalies
            ],
            "patterns": analysis.patterns,
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info("json_report_exported", path=output_path, anomalies=len(analysis.anomalies))

    def export_csv(self, analysis: AnalysisResult, output_path: str) -> None:
        """
        Export anomalies to CSV

        Args:
            analysis: Analysis result
            output_path: Path to output file
        """
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(
                [
                    "Timestamp",
                    "Severity",
                    "Type",
                    "Confidence",
                    "Description",
                    "Source",
                    "Recommendation",
                ]
            )

            # Data
            for anomaly in analysis.anomalies:
                writer.writerow(
                    [
                        anomaly.log_entry.timestamp.isoformat() if anomaly.log_entry else "",
                        anomaly.severity,
                        anomaly.anomaly_type,
                        f"{anomaly.confidence:.2f}",
                        anomaly.description,
                        anomaly.log_entry.source if anomaly.log_entry else "",
                        anomaly.recommendation,
                    ]
                )

        logger.info("csv_report_exported", path=output_path, anomalies=len(analysis.anomalies))

    def export_html(self, analysis: AnalysisResult, output_path: str) -> None:
        """
        Export analysis results to HTML

        Args:
            analysis: Analysis result
            output_path: Path to output file
        """
        summary = self.generate_summary(analysis)

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>LogGem Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .card h3 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }}
        .anomaly {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }}
        .anomaly.critical {{ border-left-color: #dc3545; }}
        .anomaly.high {{ border-left-color: #fd7e14; }}
        .anomaly.medium {{ border-left-color: #ffc107; }}
        .anomaly.low {{ border-left-color: #28a745; }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .badge.critical {{ background: #dc3545; color: white; }}
        .badge.high {{ background: #fd7e14; color: white; }}
        .badge.medium {{ background: #ffc107; color: #000; }}
        .badge.low {{ background: #28a745; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>💎 LogGem Analysis Report</h1>
        <p>Generated: {self.timestamp.strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>

    <div class="summary">
        <div class="card">
            <h3>Total Entries</h3>
            <div class="value">{summary["total_entries"]:,}</div>
        </div>
        <div class="card">
            <h3>Total Anomalies</h3>
            <div class="value">{summary["total_anomalies"]:,}</div>
        </div>
        <div class="card">
            <h3>Critical Issues</h3>
            <div class="value" style="color: #dc3545;">{summary["severity_breakdown"]["critical"]}</div>
        </div>
        <div class="card">
            <h3>High Risk</h3>
            <div class="value" style="color: #fd7e14;">{summary["severity_breakdown"]["high"]}</div>
        </div>
    </div>

    <div class="card" style="margin-bottom: 30px;">
        <h2>Top Anomalies</h2>
"""

        for _i, anomaly in enumerate(analysis.anomalies[:20], 1):
            html += f"""
        <div class="anomaly {anomaly.severity}">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <span class="badge {anomaly.severity}">{anomaly.severity}</span>
                    <strong style="margin-left: 10px;">{anomaly.anomaly_type}</strong>
                    <p style="margin: 10px 0;">{anomaly.description}</p>
                    <p style="margin: 5px 0; color: #666; font-size: 14px;">
                        💡 {anomaly.recommendation}
                    </p>
                </div>
                <div style="text-align: right; margin-left: 20px;">
                    <div style="font-size: 24px; font-weight: bold; color: #667eea;">
                        {anomaly.confidence:.0f}%
                    </div>
                    <div style="font-size: 12px; color: #999;">confidence</div>
                </div>
            </div>
        </div>
"""

        html += """
    </div>

    <div class="card">
        <p style="text-align: center; color: #999;">
            Generated by LogGem v0.1.0 - AI-Powered Log Anomaly Detection
        </p>
    </div>
</body>
</html>
"""

        with open(output_path, "w") as f:
            f.write(html)

        logger.info("html_report_exported", path=output_path, anomalies=len(analysis.anomalies))

    def print_summary(self, analysis: AnalysisResult) -> None:
        """
        Print summary statistics to console

        Args:
            analysis: Analysis result
        """
        summary = self.generate_summary(analysis)

        print("\n" + "=" * 70)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 70)
        print(f"\nTotal Entries:     {summary['total_entries']:,}")
        print(f"Total Anomalies:   {summary['total_anomalies']:,}")
        print(f"Patterns Found:    {summary['patterns_detected']}")

        print("\n" + "-" * 70)
        print("Severity Breakdown:")
        print("-" * 70)
        for severity, count in summary["severity_breakdown"].items():
            print(f"  {severity.upper():12} {count:>5}")

        print("\n" + "-" * 70)
        print("Anomaly Types:")
        print("-" * 70)
        for atype, count in summary["type_breakdown"].items():
            print(f"  {atype:30} {count:>5}")

        print("\n" + "=" * 70)
