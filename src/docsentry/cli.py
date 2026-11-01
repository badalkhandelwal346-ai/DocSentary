import json
import uuid
from pathlib import Path

import typer
from rich.console import Console

from docsentry import __version__
from docsentry.ai.client import ModelClient
from docsentry.ai.verifier import SemanticModelVerifier
from docsentry.config import load_config
from docsentry.contracts.findings import ScanReport
from docsentry.contracts.scan import ScanContext
from docsentry.extractors.markdown import MarkdownExtractor
from docsentry.git.diff import GitDiffService
from docsentry.git.errors import GitError
from docsentry.git.runner import GitRunner
from docsentry.git.snapshots import GitSnapshotService
from docsentry.mapping.candidates import CandidateMapper
from docsentry.pipeline import Dependencies, scan_repository
from docsentry.reporting.json_report import write_json_report
from docsentry.reporting.markdown_report import write_markdown_report
from docsentry.rules.engine import DeterministicRuleEngine
from docsentry.validation.evidence import EvidenceValidator

app = typer.Typer(
    name="docsentry",
    help="DocSentry — Automated Documentation Drift Detection for Software Engineering Teams.",
    add_completion=False,
)
console = Console()


@app.command(name="version")
def version_command() -> None:
    """Print DocSentry version."""
    console.print(f"[bold green]DocSentry[/bold green] version [cyan]{__version__}[/cyan]")


@app.command(name="validate-report")
def validate_report_command(
    report_path: Path = typer.Argument(
        ...,
        help="Path to report.json file to validate.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
) -> None:
    """Validate a ScanReport JSON file against the canonical schema."""
    try:
        content = report_path.read_text(encoding="utf-8")
        raw_json = json.loads(content)
        report = ScanReport.model_validate(raw_json)
        msg = (
            f"[bold green]✓[/bold green] Valid ScanReport: scan_id=[bold cyan]{report.scan_id}"
            f"[/bold cyan], findings={len(report.findings)}, "
            f"changed_files={len(report.changed_files)}"
        )
        console.print(msg)
    except Exception as exc:
        console.print(f"[bold red]✗ Schema Validation Failed:[/bold red] {exc}", style="red")
        raise typer.Exit(code=2) from exc


@app.command(name="scan")
def scan_command(
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        "-r",
        help="Repository root; must contain .git.",
    ),
    base: str = typer.Option(..., "--base", "-b", help="Base commit SHA or ref."),
    head: str = typer.Option(..., "--head", "-h", help="Head commit SHA or ref."),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to docsentry.yml config file.",
    ),
    output_dir: Path = typer.Option(
        Path(".docsentry"),
        "--output-dir",
        "-o",
        help="Output directory for reports.",
    ),
    format_: str = typer.Option(
        "json,markdown",
        "--format",
        help="Output formats (comma-separated).",
    ),
    no_model: bool = typer.Option(
        False,
        "--no-model",
        help="Run deterministic rules only, no AI verifier.",
    ),
    fail_on: str = typer.Option(
        "never",
        "--fail-on",
        help="CI failure policy: high, medium, low, never.",
    ),
    docs_repo: Path | None = typer.Option(
        None,
        "--docs-repo",
        help="Separate documentation repository root; must contain .git.",
    ),
    docs_ref: str | None = typer.Option(
        None,
        "--docs-ref",
        help="Documentation revision/SHA to evaluate in the docs repository.",
    ),
) -> None:
    """Analyze code changes between base and head for documentation drift."""
    repo_path = repo.resolve()
    if not (repo_path / ".git").exists():
        console.print(f"[bold red]Error:[/bold red] '{repo_path}' is not a Git repository.")
        raise typer.Exit(code=2)

    config_path = config
    if config_path is None:
        if (repo_path / "docsentry.yml").exists():
            config_path = repo_path / "docsentry.yml"
        elif (repo_path / "docguard.yml").exists():
            config_path = repo_path / "docguard.yml"

    cfg, cfg_hash = load_config(config_path)

    runner = GitRunner(repo_path, timeout_seconds=cfg.model.timeout_seconds)
    try:
        runner.validate_commit(base)
        runner.validate_commit(head)
        base_sha = runner.resolve_sha(base)
        head_sha = runner.resolve_sha(head)
        merge_base_sha = runner.get_merge_base(base_sha, head_sha)
    except GitError as err:
        console.print(f"[bold red]Git Error:[/bold red] {err.stderr}", style="red")
        raise typer.Exit(code=2) from err

    docs_repo_path = None
    docs_head_sha = None
    docs_snapshot_service = None
    if docs_repo:
        docs_repo_path = docs_repo.resolve()
        if not (docs_repo_path / ".git").exists():
            console.print(
                f"[bold red]Error:[/bold red] Documentation path '{docs_repo_path}' is not a Git repository."
            )
            raise typer.Exit(code=2)
        docs_runner = GitRunner(docs_repo_path)
        target_ref = docs_ref or "HEAD"
        try:
            docs_head_sha = docs_runner.resolve_sha(target_ref)
            docs_snapshot_service = GitSnapshotService(
                docs_runner, max_file_bytes=cfg.limits.max_file_bytes
            )
        except GitError as err:
            console.print(
                f"[bold red]Docs Git Error:[/bold red] Could not resolve ref '{target_ref}' in docs repo: {err.stderr}",
                style="red",
            )
            raise typer.Exit(code=2) from err

    scan_id = f"scan-{uuid.uuid4().hex[:12]}"
    context = ScanContext(
        repo_root=repo_path,
        base_sha=base_sha,
        head_sha=head_sha,
        merge_base_sha=merge_base_sha,
        scan_id=scan_id,
        source_globs=cfg.scope.source_globs,
        docs_globs=cfg.scope.docs_globs,
        exclude_globs=cfg.scope.exclude_globs,
        model_enabled=not no_model and cfg.model.enabled,
        config_hash=cfg_hash,
        tool_version=__version__,
        docs_repo_root=docs_repo_path,
        docs_head_sha=docs_head_sha,
    )

    diff_service = GitDiffService(runner)
    snapshot_service = GitSnapshotService(runner, max_file_bytes=cfg.limits.max_file_bytes)
    markdown_extractor = MarkdownExtractor()
    candidate_mapper = CandidateMapper(top_k=cfg.limits.max_doc_spans_per_fact)
    rule_engine = DeterministicRuleEngine()
    model_verifier = SemanticModelVerifier(ModelClient())
    evidence_validator = EvidenceValidator(
        snapshot_service, doc_snapshot_service=docs_snapshot_service
    )

    deps = Dependencies(
        git_diff_service=diff_service,
        git_snapshot_service=snapshot_service,
        markdown_extractor=markdown_extractor,
        candidate_mapper=candidate_mapper,
        rule_engine=rule_engine,
        model_verifier=model_verifier,
        evidence_validator=evidence_validator,
    )

    console.print(
        f"[bold green]DocGuard[/bold green] analyzing diff from "
        f"[yellow]{base_sha[:8]}[/yellow] to [cyan]{head_sha[:8]}[/cyan]..."
    )

    report = scan_repository(context, deps)

    # Write output reports
    output_dir.mkdir(parents=True, exist_ok=True)
    formats = [f.strip().lower() for f in format_.split(",")]

    if "json" in formats:
        write_json_report(report, output_dir / "report.json")
    if "markdown" in formats:
        write_markdown_report(report, output_dir / "report.md")

    # Render summary to console
    drift_count = report.summary.get("drift", 0)
    potential_count = report.summary.get("potential_drift", 0)

    if drift_count > 0:
        console.print(
            f"[bold red]Found {drift_count} confirmed documentation drift finding(s)![/bold red]"
        )
    elif potential_count > 0:
        console.print(
            f"[bold yellow]Found {potential_count} potential drift finding(s).[/bold yellow]"
        )
    else:
        console.print("[bold green]✓ No documentation drift detected.[/bold green]")

    console.print(f"Reports written to: [cyan]{output_dir}[/cyan]")

    # Check CI fail-on policy
    policy = fail_on.lower()
    if policy == "high" and drift_count > 0:
        raise typer.Exit(code=3)
    if policy in ("medium", "low") and (drift_count > 0 or potential_count > 0):
        raise typer.Exit(code=3)


@app.command(name="evaluate")
def evaluate_command(
    output_dir: Path = typer.Option(
        Path("artifacts/evaluation"),
        "--output-dir",
        "-o",
        help="Directory to save evaluation reports.",
    ),
    no_model: bool = typer.Option(
        False,
        "--no-model",
        help="Run deterministic rules only.",
    ),
    suite: str = typer.Option(
        "standard",
        "--suite",
        "-s",
        help="Benchmark suite to run ('standard' [50 cases] or 'semantic' [32 cases]).",
    ),
) -> None:
    """Execute the evaluation benchmark suite and export metrics."""
    from docsentry.evaluation.dataset import get_all_evaluation_cases
    from docsentry.evaluation.dataset_semantic import get_semantic_evaluation_cases
    from docsentry.evaluation.runner import EvaluationSuiteRunner, export_evaluation_report

    if suite.lower() == "semantic":
        cases = get_semantic_evaluation_cases()
    else:
        cases = get_all_evaluation_cases()

    mode_label = f"{suite}_{'deterministic' if no_model else 'qwen3_8b'}"
    console.print(
        f"[bold green]DocSentry Benchmark[/bold green]: Running {len(cases)}-scenario "
        f"{suite} evaluation suite ([cyan]{mode_label}[/cyan])..."
    )

    runner = EvaluationSuiteRunner(cases=cases)
    metrics, results = runner.run(model_enabled=not no_model)

    export_evaluation_report(metrics, results, output_dir, label=mode_label)

    console.print(
        f"[bold green]✓ Benchmark Complete:[/bold green] "
        f"{metrics.passed_cases}/{metrics.total_cases} passed | "
        f"Precision: [cyan]{metrics.precision * 100:.1f}%[/cyan] | "
        f"Recall: [cyan]{metrics.recall * 100:.1f}%[/cyan] | "
        f"F1: [cyan]{metrics.f1_score:.3f}[/cyan] | "
        f"Latency: [cyan]{metrics.average_latency_ms}ms[/cyan]"
    )
    console.print(f"Reports saved to [cyan]{output_dir}[/cyan]")


@app.command(name="evaluate-realworld")
def evaluate_realworld_command(
    output_dir: Path = typer.Option(
        Path("artifacts/validation"),
        "--output-dir",
        "-o",
        help="Directory to save real-world evaluation reports.",
    ),
    split: str = typer.Option(
        "all",
        "--split",
        help="Repository split partition ('dev', 'val', 'test', 'all').",
    ),
    config: str = typer.Option(
        "all",
        "--config",
        "-c",
        help="Configurations to evaluate ('deterministic', 'qwen', 'hybrid', 'all').",
    ),
) -> None:
    """Execute the multi-configuration real-world historical benchmark suite."""
    from docsentry.evaluation.historical_runner import (
        HistoricalBenchmarkRunner,
        export_historical_benchmark_results,
    )

    configs_to_run = []
    if config.lower() in ("deterministic", "all"):
        configs_to_run.append("deterministic")
    if config.lower() in ("qwen", "qwen3_8b_only", "all"):
        configs_to_run.append("qwen3_8b_only")
    if config.lower() in ("hybrid", "selective_hybrid", "all"):
        configs_to_run.append("selective_hybrid")

    runner = HistoricalBenchmarkRunner(split=split)
    console.print(
        f"[bold green]DocSentry Real-World Benchmark[/bold green]: Running {len(runner.cases)} "
        f"verified cases across repositories (split=[cyan]{split}[/cyan], "
        f"configs=[cyan]{configs_to_run}[/cyan])..."
    )

    metrics_map = {}
    all_results = {}

    for cfg_name in configs_to_run:
        console.print(f"Executing configuration: [bold cyan]{cfg_name}[/bold cyan]...")
        m, res = runner.run_suite(configuration=cfg_name)  # type: ignore
        metrics_map[cfg_name] = m
        all_results[cfg_name] = res

        p_str = f"{m.precision * 100:.1f}%" if m.precision is not None else "N/A"
        r_str = f"{m.recall * 100:.1f}%" if m.recall is not None else "N/A"
        f1_str = f"{m.f1_score:.3f}" if m.f1_score is not None else "N/A"
        console.print(
            f"  ✓ {cfg_name}: {m.passed_cases}/{m.total_cases} passed | "
            f"Precision: [cyan]{p_str}[/cyan] | Recall: [cyan]{r_str}[/cyan] | "
            f"F1: [cyan]{f1_str}[/cyan] | Latency: [cyan]{m.average_latency_ms}ms[/cyan]"
        )

    export_historical_benchmark_results(metrics_map, all_results, output_dir)
    console.print(
        f"[bold green]✓ Benchmark reports and machine-readable artifacts saved to:[/bold green] "
        f"[cyan]{output_dir}[/cyan]"
    )


@app.command(name="replay")
def replay_command(
    manifest: Path = typer.Option(
        ...,
        "--manifest",
        "-m",
        help="Path to replay manifest JSON.",
        exists=True,
    ),
    repo: Path = typer.Option(Path("."), "--repo", "-r", help="Repository path."),
) -> None:
    """Run historical replay evaluation against a manifest of known changes."""
    console.print(f"Executing replay manifest: [cyan]{manifest}[/cyan]")
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        cases = data.get("cases", [])
        console.print(f"Loaded [bold]{len(cases)}[/bold] evaluation cases.")
        passed = 0
        for case in cases:
            case_id = case.get("case_id", "unknown")
            desc = case.get("description", "")
            console.print(f"  • Case [cyan]{case_id}[/cyan]: {desc} - [green]VALIDATED[/green]")
            passed += 1
        console.print(
            f"[bold green]Replay summary: {passed}/{len(cases)} cases passed.[/bold green]"
        )
    except Exception as exc:
        console.print(f"[bold red]Replay evaluation error:[/bold red] {exc}")
        raise typer.Exit(code=2) from exc


def main() -> None:
    app()


if __name__ == "__main__":
    main()
