import argparse
import csv
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config

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
ALPHA = 0.05


def discover_versions(results_dir: Path) -> tuple[str, ...]:
    results = sorted(results_dir.glob(f"{RESULTS_PREFIX}*.csv"))
    versions = tuple(path.stem.removeprefix(RESULTS_PREFIX) for path in results)
    if not versions:
        raise SystemExit(f"No {RESULTS_PREFIX}*.csv found in {results_dir}. Run run_version.py first.")
    return versions


def load_cases(path: Path) -> dict[str, dict[str, str]]:
    with open(path, "r", newline="", encoding="utf-8") as file:
        return {row["id"]: row for row in csv.DictReader(file)}


def load_executions(path: Path) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    with open(path, "r", newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            grouped.setdefault(row["id"], []).append(row)
    return grouped


def check_complete(version: str, grouped: dict, cases: dict, reps: int) -> None:
    problems = []
    missing = set(cases) - set(grouped)
    if missing:
        problems.append(f"cases missing: {sorted(missing)}")
    for case_id, rows in grouped.items():
        if len(rows) != reps:
            problems.append(f"case {case_id}: {len(rows)} execution(s), expected {reps}")
    if problems:
        raise SystemExit(
            f"Run {version} is incomplete ({'; '.join(problems)}). Re-run run_version.py."
        )


def score_version(version: str, cases: dict, reps: int, results_dir: Path) -> dict:
    grouped = load_executions(results_dir / f"{RESULTS_PREFIX}{version}.csv")
    check_complete(version, grouped, cases, reps)

    majority = reps // 2 + 1
    passed: dict[str, bool] = {}
    kinds: dict[str, str] = {}
    mistakes: list[tuple[str, str, str]] = []
    format_failures: list[tuple[str, str, str]] = []
    per_case: list[str] = []
    latencies: list[int] = []
    input_tokens: list[int] = []
    output_tokens: list[int] = []
    exec_correct = exec_total = 0

    for case_id, rows in grouped.items():
        expected = cases[case_id]["expected_category"].strip().lower()
        kinds[case_id] = cases[case_id]["kind"]
        answers: Counter = Counter()
        correct_execs = 0

        for row in rows:
            response = row["raw_response"].strip().lower()
            exec_total += 1
            latencies.append(int(row["latency_ms"]))
            input_tokens.append(int(row["input_tokens"]))
            output_tokens.append(int(row["output_tokens"]))
            answers[response] += 1

            if response not in config.CATEGORIES:
                format_failures.append((case_id, row.get("rep", "1"), row["raw_response"]))
            elif response == expected:
                correct_execs += 1

        exec_correct += correct_execs
        passed[case_id] = correct_execs >= majority
        per_case.append(f"{case_id}: {correct_execs}/{len(rows)}")
        if not passed[case_id]:
            most_common = answers.most_common(1)[0][0]
            mistakes.append((case_id, expected, most_common))

    def count(kind: str) -> tuple[int, int]:
        ids = [cid for cid in passed if kinds[cid] == kind]
        return sum(passed[cid] for cid in ids), len(ids)

    clear_ok, clear_total = count("clear")
    amb_ok, amb_total = count("ambiguous")
    total_cases = len(passed)

    return {
        "version": version,
        "passed": passed,
        "cases_ok": sum(passed.values()),
        "cases_total": total_cases,
        "exec_correct": exec_correct,
        "exec_total": exec_total,
        "clear_score": f"{clear_ok}/{clear_total}",
        "ambiguous_score": f"{amb_ok}/{amb_total}",
        "clear_ok": clear_ok,
        "per_case": per_case,
        "mistakes": sorted(mistakes),
        "format_failures": format_failures,
        "median_latency_ms": statistics.median(latencies),
        "median_input_tokens": statistics.median(input_tokens),
        "median_output_tokens": statistics.median(output_tokens),
    }


def mcnemar_exact(favorable: int, contrary: int) -> float:
    n = favorable + contrary
    if n == 0:
        return 1.0
    k = min(favorable, contrary)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


def paired_comparison(target: dict, baseline: dict) -> dict:
    favorable = sum(1 for cid in target["passed"] if target["passed"][cid] and not baseline["passed"][cid])
    contrary = sum(1 for cid in target["passed"] if baseline["passed"][cid] and not target["passed"][cid])
    return {
        "favorable": favorable,
        "contrary": contrary,
        "p_value": mcnemar_exact(favorable, contrary),
    }


def verdict(target: dict, baseline: dict, pair: dict) -> list[tuple[str, bool, str]]:
    return [
        (
            "McNemar p < 0,05 com mais casos favoráveis que contrários",
            pair["p_value"] < ALPHA and pair["favorable"] > pair["contrary"],
            f"p = {pair['p_value']:.4f}, favoráveis {pair['favorable']}, contrários {pair['contrary']}",
        ),
        (
            "Nenhuma regressão nos casos claros",
            target["clear_ok"] >= baseline["clear_ok"],
            f"target {target['clear_score']} vs baseline {baseline['clear_score']}",
        ),
        (
            "Zero falhas de formato",
            len(target["format_failures"]) == 0,
            f"{len(target['format_failures'])} falha(s)",
        ),
    ]


def build_markdown_table(reports: list[dict]) -> str:
    def row(label: str, values: list[str]) -> str:
        return f"| {label} | " + " | ".join(values) + " |"

    lines = [
        row("Métrica", [r["version"] for r in reports]),
        "| " + " | ".join(["---"] * (len(reports) + 1)) + " |",
        row("Casos aprovados", [f"{r['cases_ok']}/{r['cases_total']} ({r['cases_ok'] / r['cases_total']:.0%})" for r in reports]),
        row("Execuções corretas", [f"{r['exec_correct']}/{r['exec_total']} ({r['exec_correct'] / r['exec_total']:.0%})" for r in reports]),
        row("Claros (casos)", [r["clear_score"] for r in reports]),
        row("Ambíguos (casos)", [r["ambiguous_score"] for r in reports]),
        row("Falhas de formato", [str(len(r["format_failures"])) for r in reports]),
        row("Latência mediana (ms)", [f"{r['median_latency_ms']:.0f}" for r in reports]),
        row("Entrada mediana (tokens)", [f"{r['median_input_tokens']:.0f}" for r in reports]),
        row("Saída mediana (tokens)", [f"{r['median_output_tokens']:.0f}" for r in reports]),
    ]
    return "\n".join(lines)


def print_report(report: dict) -> None:
    print(f"\n== {report['version']} ==")
    print(f"Casos aprovados: {report['cases_ok']}/{report['cases_total']}")
    print(f"Execuções corretas: {report['exec_correct']}/{report['exec_total']}")
    print(f"Claros: {report['clear_score']} | Ambíguos: {report['ambiguous_score']}")
    print("Acertos por caso: " + ", ".join(report["per_case"]))
    print(f"Falhas de formato: {len(report['format_failures'])}")
    for case_id, rep, raw in report["format_failures"]:
        print(f"  - caso {case_id} (rep {rep}): resposta fora da lista ({raw!r})")
    if report["mistakes"]:
        print("Casos reprovados (maioria errada):")
        for case_id, expected, got in report["mistakes"]:
            print(f"  - caso {case_id}: esperado {expected}, resposta mais comum {got}")
    else:
        print("Casos reprovados: nenhum")
    print(f"Latência mediana: {report['median_latency_ms']:.0f} ms")


def main() -> None:
    parser = argparse.ArgumentParser(description="Score saved runs.")
    parser.add_argument("--set", dest="case_set", choices=SETS, default="dev")
    parser.add_argument("--baseline", help="version used as the reference, e.g. v3")
    parser.add_argument("--target", help="version under test, e.g. v4")
    args = parser.parse_args()

    if bool(args.baseline) != bool(args.target):
        raise SystemExit("Use --baseline and --target together.")

    settings = SETS[args.case_set]
    cases = load_cases(settings["cases"])
    reports = [
        score_version(version, cases, settings["reps"], settings["results_dir"])
        for version in discover_versions(settings["results_dir"])
    ]
    by_version = {r["version"]: r for r in reports}

    for report in reports:
        print_report(report)

    if args.baseline:
        if args.target not in by_version or args.baseline not in by_version:
            raise SystemExit(f"Both {args.baseline} and {args.target} must have results in this set.")
        target, baseline = by_version[args.target], by_version[args.baseline]
        pair = paired_comparison(target, baseline)

        print(f"\n== {args.target} vs {args.baseline} (pareado, por caso) ==")
        print(f"Favoráveis à {args.target}: {pair['favorable']} | contrários: {pair['contrary']} | "
            f"p (McNemar exato): {pair['p_value']:.4f}")
        print("Critérios declarados no changelog:")
        results = verdict(target, baseline, pair)
        for label, ok, detail in results:
            print(f"  [{'OK' if ok else 'FALHOU'}] {label} ({detail})")
        if all(ok for _, ok, _ in results):
            print(f"Conclusão: {args.target} melhora sobre {args.baseline} neste conjunto.")
        else:
            print(f"Conclusão: não há evidência de melhora de {args.target} sobre {args.baseline} neste conjunto.")

    print("\n-- Tabela pronta para colar no comparison.md --\n")
    print(build_markdown_table(reports))


if __name__ == "__main__":
    main()