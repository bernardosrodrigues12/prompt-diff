import csv
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config  
from call_model import call_model  

VALID_VERSIONS = ("v1", "v2", "v3")

CALL_DELAY_SECONDS = 15.0

RESULT_FIELDS = [
    "id",
    "expected_category",
    "raw_response",
    "input_tokens",
    "output_tokens",
    "latency_ms",
]


def load_prompt(version: str) -> str:
    prompt_file = config.PROMPTS_FOLDER / f"{version}.md"
    return prompt_file.read_text(encoding="utf-8")


def load_cases() -> list[dict[str, str]]:
    with open(config.CASES_FILE, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in VALID_VERSIONS:
        raise SystemExit(f"Usage: python src/run_version.py {'|'.join(VALID_VERSIONS)}")

    version = sys.argv[1]
    prompt_text = load_prompt(version)
    cases = load_cases()

    output_file = config.CASES_FILE.parent / f"results_{version}.csv"
    rows = []

    print(f"Running {len(cases)} cases for {version} with {config.MODEL}...")

    for index, case in enumerate(cases, start=1):
        response = call_model(prompt_text, case["message"])

        rows.append({
            "id": case["id"],
            "expected_category": case["expected_category"],
            "raw_response": response.text,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "latency_ms": response.latency_ms,
        })

        preview = response.text.strip().replace("\n", " ")[:40]
        print(f"[{index}/{len(cases)}] {case['id']} -> {preview!r} ({response.latency_ms} ms)")

        if index < len(cases):
            time.sleep(CALL_DELAY_SECONDS)

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} results to {output_file}")


if __name__ == "__main__":
    main()