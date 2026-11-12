import csv
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config

def discover_versions() -> tuple[str, ...]:
    results = sorted(config.CASES_FILE.parent.glob("results_*.csv"))
    versions = tuple(path.stem.removeprefix("results_") for path in results)
    if not versions:
        raise SystemExit(
            f"No results_*.csv found in {config.CASES_FILE.parent}. "
            "Run run_version.py first."    
        )
    return versions

def load_cases() -> dict[str, dict[str, str]]:
    with open(config.CASES_FILE, "r", newline="", encoding="utf-8") as file:
        return {row["id"]: row for row in csv.DictReader(file)}

def load_results(version: str) -> list[dict[str, str]]:
    results_file = config.CASES_FILE.parent / f"results_{version}.csv"
    with open(results_file, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))

def score_version(version: str, cases: dict[str, dict[str, str]]) -> dict:
    results = load_results(version)

    correct = 0
    clear_total = clear_correct = 0
    ambiguous_total = ambiguous_correct = 0
    format_failures: list[tuple[str, str]] = []
    mistakes: list[tuple[str, str, str]] = []
    latencies: list[int] = []
    input_tokens: list[int] = []
    output_tokens: list[int] = []

    for row in results:
        case = cases[row["id"]]
        is_clear = case["kind"] == "clear"
        if is_clear:
            clear_total += 1
        else:
            ambiguous_total +=1

        response = row["raw_response"].strip().lower()
        expected = row["expected_category"].strip().lower()

        latencies.append(int(row["latency_ms"]))
        input_tokens.append(int(row["input_tokens"]))
        output_tokens.append(int(row["output_tokens"]))

        if response not in config.CATEGORIES:
            format_failures.append((row["id"], row["raw_response"]))
            continue

        if response == expected:
            correct += 1
            if is_clear:
                clear_correct += 1
            else:
                ambiguous_correct += 1
        else:
            mistakes.append((row["id"], expected, response))

    return {
        "version": version,
        "total": len(results),
        "correct": correct,
        "accuracy": correct / len(results),
        "clear_score": f"{clear_correct}/{clear_total}",
        "ambiguous_score": f"{ambiguous_correct}/{ambiguous_total}",
        "format_failures": format_failures,
        "mistakes": mistakes,
        "median_latency_ms": statistics.median(latencies),
        "median_input_tokens": statistics.median(input_tokens),
        "median_output_tokens": statistics.median(output_tokens),
        "total_input_tokens": sum(input_tokens),
        "total_output_tokens": sum(output_tokens),
    }


def build_markdown_table(reports: list[dict]) -> str:

    def row(label: str, values: list[str]) -> str:
        return f"| {label} | " + " | ".join(values) + " |"

    lines = [
        row("Métrica", [report["version"] for report in reports]),
        "| " + " | ".join(["---"] * (len(reports) + 1)) + " |",
        row("Acerto", [f"{r['correct']}/{r['total']} ({r['accuracy']:.0%})" for r in reports]),
        row("Claros", [r["clear_score"] for r in reports]),
        row("Ambíguos", [r["ambiguous_score"] for r in reports]),
        row("Falhas de formato", [str(len(r["format_failures"])) for r in reports]),
        row("Latência mediana (ms)", [f"{r['median_latency_ms']:.0f}" for r in reports]),
        row("Entrada mediana (tokens)", [f"{r['median_input_tokens']:.0f}" for r in reports]),
        row("Saída mediana (tokens)", [f"{r['median_output_tokens']:.0f}" for r in reports]),
    ]
    return "\n".join(lines)


def main() -> None:
    cases = load_cases()
    reports = [score_version(version, cases) for version in discover_versions()]

    for report in reports:
        print(f"\n== {report['version']} ==")
        print(f"Acerto: {report['correct']}/{report['total']} ({report['accuracy']:.0%})")
        print(f"Claros: {report['clear_score']} | Ambíguos: {report['ambiguous_score']}")
        print(f"Falhas de formato: {len(report['format_failures'])}")
        for case_id, raw in report["format_failures"]:
            print(f"  - caso {case_id}: resposta fora da lista ({raw!r})")
        if report["mistakes"]:
            print("Erros de classificação:")
            for case_id, expected, got in report["mistakes"]:
                print(f"  - caso {case_id}: esperado {expected}, obtido {got}")
        else:
            print("Erros de classificação: nenhum")
        print(f"Latência mediana: {report['median_latency_ms']:.0f} ms")
        print(
            f"Tokens por chamada (mediana): entrada {report['median_input_tokens']:.0f}, "
            f"saída {report['median_output_tokens']:.0f}"
        )
        print(f"Tokens totais: entrada {report['total_input_tokens']}, saída {report['total_output_tokens']}")

    print("\n-- Tabela pronta para colar no comparison.md --\n")
    print(build_markdown_table(reports))


if __name__ == "__main__":
    main()

