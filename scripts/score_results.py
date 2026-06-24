from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_FIELDS = [
    "date",
    "match_id",
    "competition",
    "stage",
    "home_team",
    "away_team",
    "kickoff_bjt",
    "prediction",
    "confidence",
    "result",
    "correct",
    "error_reason",
    "lesson",
    "report_path",
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_results(path: Path) -> dict[str, str]:
    data = load_json(path)
    items = data.get("results", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError("results file must contain a list or an object with a 'results' list")

    results: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        match_id = str(item.get("match_id", ""))
        if not match_id:
            continue
        if item.get("result"):
            outcome = str(item["result"])
        else:
            home_score = int(item["home_score"])
            away_score = int(item["away_score"])
            if home_score > away_score:
                outcome = "home_win"
            elif home_score < away_score:
                outcome = "away_win"
            else:
                outcome = "draw"
        results[match_id] = outcome
    return results


def read_ledger(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def write_ledger(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=LEDGER_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in LEDGER_FIELDS})


def write_review(day: str, scored_rows: list[dict[str, str]]) -> Path:
    review_path = ROOT / "memory" / f"review-{day}.md"
    lines = [
        f"# {day} Prediction Review",
        "",
        "| Match | Prediction | Result | Correct | Error Reason | Lesson |",
        "|---|---|---|---|---|---|",
    ]
    for row in scored_rows:
        match = f"{row.get('home_team', '')} vs {row.get('away_team', '')}"
        lines.append(
            f"| {match} | {row.get('prediction', '') or 'TBD'} | {row.get('result', '')} | {row.get('correct', '') or 'UNSCORED'} | {row.get('error_reason', '')} | {row.get('lesson', '')} |"
        )
    lines.extend(
        [
            "",
            "## Follow-up",
            "",
            "Fill `error_reason` and `lesson` in `memory/ledger.csv`, then copy durable lessons into `memory/lessons.md`.",
        ]
    )
    review_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return review_path


def score(day: str, results_path: Path, ledger_path: Path) -> Path:
    outcomes = load_results(results_path)
    rows = read_ledger(ledger_path)
    scored_rows: list[dict[str, str]] = []

    for row in rows:
        if day and row.get("date") != day:
            continue
        outcome = outcomes.get(row.get("match_id", ""))
        if not outcome:
            continue
        row["result"] = outcome
        prediction = row.get("prediction", "").strip()
        row["correct"] = "TRUE" if prediction and prediction == outcome else ("FALSE" if prediction else "")
        scored_rows.append(row)

    write_ledger(ledger_path, rows)
    return write_review(day, scored_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Score World Cup prediction ledger rows against real results.")
    parser.add_argument("--results", required=True, help="Path to results JSON.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Target date in YYYY-MM-DD.")
    parser.add_argument("--ledger", default=str(ROOT / "memory/ledger.csv"), help="Path to ledger CSV.")
    args = parser.parse_args()

    review_path = score(args.date, Path(args.results).resolve(), Path(args.ledger).resolve())
    print(f"Updated ledger and wrote review: {review_path}")


if __name__ == "__main__":
    main()

