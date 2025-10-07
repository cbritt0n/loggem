"""
Command-line interface for LogGem.

Provides commands for analyzing logs, watching files, and managing the system.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from loggem import __version__
from loggem.analyzer import LogAnalyzer
from loggem.analyzer.pattern_detector import PatternDetector
from loggem.core.config import get_settings
from loggem.core.logging import get_logger, setup_logging
from loggem.core.models import AnalysisResult, Severity
from loggem.detector import AnomalyDetector
from loggem.parsers import LogParserFactory

app = typer.Typer(
    name="loggem",
    help="LogGem: AI-Assisted Log Anomaly Detector",
    add_completion=False,
)
console = Console()


@app.command()
def analyze(
    files: list[Path] = typer.Argument(..., help="Log files to analyze"),
    format: Optional[str] = typer.Option(
        None, "--format", "-f", help="Log format (syslog, json, nginx, auth)"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file for results (JSON)"
    ),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use for detection"),
    sensitivity: Optional[float] = typer.Option(
        None, "--sensitivity", "-s", min=0.0, max=1.0, help="Detection sensitivity (0.0-1.0)"
    ),
    no_ai: bool = typer.Option(False, "--no-ai", help="Disable AI detection (use only rule-based)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """
    Analyze log files for anomalies.

    Examples:
        loggem analyze /var/log/auth.log
        loggem analyze *.log --format json --output report.json
        loggem analyze auth.log --sensitivity 0.9 --no-ai
    """
    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(level=log_level)
    logger = get_logger(__name__)

    console.print(Panel.fit("🔍 LogGem - Analyzing Logs", style="bold blue"))

    # Validate files
    for file_path in files:
        if not file_path.exists():
            console.print(f"[red]Error: File not found: {file_path}[/red]")
            raise typer.Exit(1)

    # Parse all files
    all_entries = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        parse_task = progress.add_task(f"Parsing {len(files)} file(s)...", total=len(files))

        for file_path in files:
            try:
                parser = LogParserFactory.create_parser(format_type=format, file_path=file_path)
                entries = list(parser.parse_file(file_path))
                all_entries.extend(entries)
                logger.info("parsed_file", path=str(file_path), entries=len(entries))
                progress.advance(parse_task)
            except Exception as e:
                console.print(f"[red]Error parsing {file_path}: {e}[/red]")
                logger.error("parse_failed", path=str(file_path), error=str(e))
                raise typer.Exit(1)

    console.print(f"✓ Parsed {len(all_entries)} log entries")

    # Pattern detection (rule-based)
    console.print("\n[cyan]Running pattern detection...[/cyan]")
    pattern_detector = PatternDetector()
    rule_based_anomalies = pattern_detector.detect_all(all_entries)
    console.print(f"✓ Found {len(rule_based_anomalies)} anomalies via rules")

    # AI detection (if enabled)
    ai_anomalies = []
    if not no_ai:
        console.print("\n[cyan]Running AI detection...[/cyan]")
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task("Loading AI model...", total=None)
                detector = AnomalyDetector(model_name=model, sensitivity=sensitivity)

                progress.add_task("Analyzing with AI...", total=None)
                ai_anomalies = detector.detect_batch(all_entries)
                detector.cleanup()

            console.print(f"✓ Found {len(ai_anomalies)} anomalies via AI")
        except Exception as e:
            console.print(f"[yellow]Warning: AI detection failed: {e}[/yellow]")
            logger.error("ai_detection_failed", error=str(e))

    # Combine anomalies (deduplicate by log_entry_id)
    all_anomalies = rule_based_anomalies + ai_anomalies
    seen_ids = set()
    unique_anomalies = []
    for anomaly in all_anomalies:
        if anomaly.log_entry_id not in seen_ids:
            unique_anomalies.append(anomaly)
            seen_ids.add(anomaly.log_entry_id)

    # Analyze results
    console.print("\n[cyan]Generating analysis...[/cyan]")
    analyzer = LogAnalyzer()
    result = analyzer.analyze(all_entries, unique_anomalies)

    # Display results
    _display_results(result)

    # Save to file if requested
    if output:
        _save_results(result, output)
        console.print(f"\n✓ Results saved to {output}")


@app.command()
def watch(
    file: Path = typer.Argument(..., help="Log file to watch"),
    format: Optional[str] = typer.Option(
        None, "--format", "-f", help="Log format (syslog, json, nginx, auth)"
    ),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use for detection"),
    sensitivity: Optional[float] = typer.Option(
        None, "--sensitivity", "-s", min=0.0, max=1.0, help="Detection sensitivity (0.0-1.0)"
    ),
) -> None:
    """
    Watch a log file in real-time for anomalies.

    Example:
        loggem watch /var/log/auth.log --format auth
    """
    setup_logging()
    console.print(Panel.fit(f"👀 Watching {file}", style="bold blue"))
    console.print("[yellow]Real-time monitoring not yet implemented[/yellow]")
    console.print("This feature will be available in a future release.")


@app.command()
def info() -> None:
    """Display system information and model status."""
    setup_logging()

    settings = get_settings()

    # System info
    table = Table(title="LogGem System Information", show_header=False)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Version", __version__)
    table.add_row("Model", settings.model.name)
    table.add_row("Device", settings.model.device)
    table.add_row("Quantization", settings.model.quantization)
    table.add_row("Sensitivity", str(settings.detection.sensitivity))
    table.add_row("Cache Directory", str(settings.model.cache_dir))
    table.add_row("Data Directory", str(settings.data_dir))

    console.print(table)

    # Available parsers
    console.print("\n[bold]Available Log Formats:[/bold]")
    for fmt in LogParserFactory.list_formats():
        console.print(f"  • {fmt}")


@app.command()
def version() -> None:
    """Display version information."""
    console.print(f"LogGem v{__version__}")


def _display_results(result: AnalysisResult) -> None:
    """Display analysis results in a formatted table."""
    console.print("\n" + "=" * 60)
    console.print("[bold]📊 Analysis Results[/bold]")
    console.print("=" * 60)

    # Summary statistics
    console.print(f"\n[cyan]Total Entries:[/cyan] {result.total_entries}")
    console.print(f"[cyan]Anomalies Found:[/cyan] {len(result.anomalies)}")
    console.print(f"[cyan]Analysis Duration:[/cyan] {result.duration:.2f}s")

    if not result.anomalies:
        console.print("\n[green]✓ No anomalies detected[/green]")
        return

    # Anomalies by severity
    console.print("\n[bold]Anomalies by Severity:[/bold]")
    for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
        anomalies = result.get_anomalies_by_severity(severity)
        if anomalies:
            color = _severity_color(severity)
            console.print(f"  [{color}]{severity.value.upper()}:[/{color}] {len(anomalies)}")

    # Top anomalies
    console.print("\n[bold]Top Anomalies:[/bold]")
    critical_anomalies = result.get_critical_anomalies()
    display_anomalies = critical_anomalies[:10] if critical_anomalies else result.anomalies[:10]

    for i, anomaly in enumerate(display_anomalies, 1):
        color = _severity_color(anomaly.severity)
        console.print(f"\n[{color}]{i}. [{anomaly.severity.value.upper()}][/{color}]")
        console.print(f"   Type: {anomaly.anomaly_type.value}")
        console.print(f"   Confidence: {anomaly.confidence:.2%}")
        console.print(f"   Description: {anomaly.description}")
        if anomaly.recommendation:
            console.print(f"   [yellow]→ {anomaly.recommendation}[/yellow]")


def _save_results(result: AnalysisResult, output_path: Path) -> None:
    """Save results to a JSON file."""
    with open(output_path, "w") as f:
        json.dump(result.to_dict(), f, indent=2)


def _severity_color(severity: Severity) -> str:
    """Get color for severity level."""
    colors = {
        Severity.CRITICAL: "red bold",
        Severity.HIGH: "red",
        Severity.MEDIUM: "yellow",
        Severity.LOW: "white",
    }
    return colors.get(severity, "white")


if __name__ == "__main__":
    app()
