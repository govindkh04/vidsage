import json
import logging
from pathlib import Path
from typing import Any, Optional
from rich.console import Console
from rich.table import Table

from ytrag.answer import answer
from ytrag.index import search as qdrant_search

logger = logging.getLogger("ytrag.evaluate")
console = Console(legacy_windows=False)


def run_evaluation(golden_path: Optional[Path] = None, top_k: int = 5) -> dict[str, Any]:
    """Execute automated evaluation against golden dataset."""
    default_path = Path("eval/golden.json")
    target_path = golden_path or default_path

    if not target_path.is_file():
        raise FileNotFoundError(f"Golden evaluation dataset not found at: {target_path}")

    with open(target_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    total_cases = len(cases)
    retrieval_cases = 0
    retrieval_hits = 0
    refusal_cases = 0
    refusal_hits = 0
    timestamp_errors: list[float] = []
    results_detail: list[dict[str, Any]] = []

    console.print(f"[bold cyan]Running VidSage Evaluation ({total_cases} test cases)...[/bold cyan]\n")

    for idx, case in enumerate(cases, start=1):
        q = case["q"]
        expect_refusal = case.get("expect_refusal", False)
        expect_vid = case.get("expect_video_id")
        expect_sec = case.get("expect_around_sec")
        tolerance = case.get("tolerance_sec", 120)

        if expect_refusal:
            refusal_cases += 1
            ans_res = answer(q, top_k=top_k)
            # Refusal is successful if grounded is False or contains refusal text
            is_refused = (not ans_res["grounded"]) or ("cover nahi hua" in ans_res["answer"].lower())
            if is_refused:
                refusal_hits += 1
            results_detail.append(
                {
                    "case": idx,
                    "query": q,
                    "type": "Refusal Test",
                    "status": "[green]PASSED[/green]" if is_refused else "[red]FAILED[/red]",
                    "details": "Correctly refused" if is_refused else "Falsely grounded",
                }
            )
        else:
            retrieval_cases += 1
            # Test vector retrieval
            retrieved = qdrant_search(query=q, top_k=top_k)
            hit = False
            best_error = float("inf")

            for r in retrieved:
                if r.get("video_id") == expect_vid:
                    start_s = r.get("start_sec", 0)
                    end_s = r.get("end_sec", 0)
                    if expect_sec is not None:
                        err = abs(start_s - expect_sec)
                        if err < best_error:
                            best_error = err
                        if (start_s - tolerance) <= expect_sec <= (end_s + tolerance):
                            hit = True
                            break
                    else:
                        hit = True
                        break

            if hit:
                retrieval_hits += 1
                if best_error != float("inf"):
                    timestamp_errors.append(best_error)

            results_detail.append(
                {
                    "case": idx,
                    "query": q,
                    "type": "Retrieval Test",
                    "status": "[green]PASSED[/green]" if hit else "[red]FAILED[/red]",
                    "details": f"Hit in top-{top_k} (error: {best_error:.0f}s)" if hit else f"Missed {expect_vid}",
                }
            )

    # Calculate metrics
    hit_rate = (retrieval_hits / retrieval_cases * 100) if retrieval_cases > 0 else 100.0
    refusal_acc = (refusal_hits / refusal_cases * 100) if refusal_cases > 0 else 100.0
    avg_ts_error = (sum(timestamp_errors) / len(timestamp_errors)) if timestamp_errors else 0.0

    # Display results
    table = Table(title="Evaluation Test Cases", show_lines=True)
    table.add_column("#", width=4)
    table.add_column("Type", width=16)
    table.add_column("Query", width=36)
    table.add_column("Status", width=12)
    table.add_column("Details")

    for r in results_detail:
        table.add_row(
            str(r["case"]),
            r["type"],
            r["query"],
            r["status"],
            r["details"],
        )

    console.print(table)

    summary_table = Table(title="Evaluation Summary Metrics")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Score", style="bold green")

    summary_table.add_row(f"Hit Rate @ {top_k}", f"{hit_rate:.1f}% ({retrieval_hits}/{retrieval_cases})")
    summary_table.add_row("Refusal Accuracy", f"{refusal_acc:.1f}% ({refusal_hits}/{refusal_cases})")
    summary_table.add_row("Avg Timestamp Offset", f"{avg_ts_error:.1f}s")

    console.print(summary_table)

    return {
        "hit_rate_at_k": hit_rate,
        "refusal_accuracy": refusal_acc,
        "avg_timestamp_error": avg_ts_error,
        "total_cases": total_cases,
    }
