import argparse
import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config
from call_model import call_model

SETS = {
    "dev": {
        "cases": config.CASES_FILE,
        "results_dir": config.CASES_FILE.parent,
        "reps": 1,
    },
    "validation": {
        "cases": config.CASES_FILE.parent / "validation_cases.csv",
        "results_dir": config.CASES_FILE.parent / "validation",
        "reps": 5,
    },
}

RESULTS_PREFIX = "results_"
CALL_DELAY_SECONDS = 15.0  # free tier spacing, see changelog
RESULT_FIELDS = [
    "id", "rep", "expected_category", "raw_response",
    "input_tokens", "output_tokens", "latency_ms",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one prompt version over a case set.")
    parser.add_argument("version", help="prompt version, e.g. v1 (reads prompts/v1.md)")
    parser.add_argument("--set", dest="case_set", choices=SETS, default="dev")
    parser.add_argument("--force", action="store_true",
                        help="allow overwriting an existing validation result")
    return parser.parse_args()


def load_cases(path: Path) -> list[dict[str, str]]:
    with open(path, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def main() -> None:
    args = parse_args()
    settings = SETS[args.case_set]

    prompt_text = (ROOT / "prompts" / f"{args.version}.md").read_text(encoding="utf-8")
    cases = load_cases(settings["cases"])
    reps = settings["reps"]

    results_dir = settings["results_dir"]
    results_dir.mkdir(parents=True, exist_ok=True)
    output = results_dir / f"{RESULTS_PREFIX}{args.version}.csv"

    if args.case_set == "validation" and output.exists() and not args.force:
        raise SystemExit(
            f"{output} already exists. Validation runs are one-shot. "
            "Use --force only to discard a broken run before evaluating it."
        )

    total = len(cases) * reps
    print(f"Running {len(cases)} cases x {reps} rep(s) for {args.version} "
        f"({args.case_set}) with {config.MODEL}...")

    done = 0
    with open(output, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=RESULT_FIELDS)
        writer.writeheader()

        for rep in range(1, reps + 1):
            for case in cases:
                if done > 0:
                    time.sleep(CALL_DELAY_SECONDS)
                done += 1

                response = call_model(prompt_text, case["message"])
                writer.writerow({
                    "id": case["id"],
                    "rep": rep,
                    "expected_category": case["expected_category"],
                    "raw_response": response.text.strip(),
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "latency_ms": response.latency_ms,
                })
                file.flush()
                print(f"[{done}/{total}] {case['id']} r{rep} -> "
                    f"{response.text.strip()!r} ({response.latency_ms} ms)")

    print(f"Saved: {output}")


if __name__ == "__main__":
    main()