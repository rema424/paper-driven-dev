#!/usr/bin/env python3
"""Run hidden test suites against all implementations and aggregate results.

Usage:
    uv run --with pytest python3 paper/downstream/run_tests.py

Output: paper/downstream/results/test_results.json
"""

import json
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
TESTS_DIR = BASE_DIR / "tests"
IMPL_DIR = BASE_DIR / "implementations"
RESULTS_DIR = BASE_DIR / "results"


def run_tests_for_impl(impl_path: str, test_file: str) -> dict:
    """Run a test file against an implementation and return results."""
    env = os.environ.copy()
    env["DOWNSTREAM_IMPL_PATH"] = str(impl_path)

    result = subprocess.run(
        [
            "uv",
            "run",
            "--with",
            "pytest",
            "python3",
            "-m",
            "pytest",
            str(test_file),
            "-v",
            "--tb=short",
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )

    # Parse pytest verbose output
    lines = result.stdout.strip().split("\n")
    passed = 0
    failed = 0
    errors = 0
    test_details = []

    for line in lines:
        if " PASSED" in line:
            passed += 1
            test_name = line.split(" PASSED")[0].strip().split("::")[-1]
            test_details.append({"name": test_name, "result": "passed"})
        elif " FAILED" in line:
            failed += 1
            test_name = line.split(" FAILED")[0].strip().split("::")[-1]
            test_details.append({"name": test_name, "result": "failed"})
        elif " ERROR" in line:
            errors += 1
            test_name = line.split(" ERROR")[0].strip().split("::")[-1]
            test_details.append({"name": test_name, "result": "error"})

    # Fallback: parse summary line if verbose parsing found nothing
    if passed + failed + errors == 0:
        import re
        for line in lines:
            m = re.search(r'(\d+) passed', line)
            if m:
                passed = int(m.group(1))
            m = re.search(r'(\d+) failed', line)
            if m:
                failed = int(m.group(1))
            m = re.search(r'(\d+) error', line)
            if m:
                errors = int(m.group(1))

    return {
        "impl_file": str(impl_path.name),
        "total": passed + failed + errors,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "pass_rate": passed / max(passed + failed + errors, 1),
        "tests": test_details,
        "compile_success": result.returncode != 2,  # 2 = collection error
        "stdout": result.stdout[-500:] if len(result.stdout) > 500 else result.stdout,
        "stderr": result.stderr[-500:] if len(result.stderr) > 500 else result.stderr,
    }


def parse_filename(filename: str) -> dict:
    """Parse condition and run info from filename.

    Expected format: cs{1,2}-{condition}-run{N}.py
    """
    name = filename.replace(".py", "")
    parts = name.split("-")
    cs = parts[0]  # cs1 or cs2
    condition = "-".join(parts[1:-1])  # conventional, paper-format, pdd-template, checklist
    run = parts[-1]  # run1, run2, etc.

    # Map to condition labels
    condition_map = {
        "conventional": "A",
        "paper-format": "B",
        "pdd-template": "C",
        "checklist": "D",
    }

    return {
        "cs": cs,
        "condition": condition,
        "condition_label": condition_map.get(condition, "?"),
        "run": run,
    }


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    all_results = {"cs1": [], "cs2": []}

    # CS1 implementations
    cs1_dir = IMPL_DIR / "cs1"
    cs1_test = TESTS_DIR / "test_cs1.py"
    if cs1_dir.exists():
        for impl_file in sorted(cs1_dir.glob("*.py")):
            print(f"Testing CS1: {impl_file.name}...", end=" ", flush=True)
            try:
                result = run_tests_for_impl(impl_file, cs1_test)
                meta = parse_filename(impl_file.name)
                result.update(meta)
                all_results["cs1"].append(result)
                print(f"{result['passed']}/{result['total']} passed")
            except subprocess.TimeoutExpired:
                print("TIMEOUT")
                meta = parse_filename(impl_file.name)
                all_results["cs1"].append(
                    {**meta, "impl_file": impl_file.name, "total": 10, "passed": 0, "failed": 0, "errors": 10, "pass_rate": 0.0, "tests": [], "compile_success": False, "timeout": True}
                )
            except Exception as e:
                print(f"ERROR: {e}")

    # CS2 implementations
    cs2_dir = IMPL_DIR / "cs2"
    cs2_test = TESTS_DIR / "test_cs2.py"
    if cs2_dir.exists():
        for impl_file in sorted(cs2_dir.glob("*.py")):
            print(f"Testing CS2: {impl_file.name}...", end=" ", flush=True)
            try:
                result = run_tests_for_impl(impl_file, cs2_test)
                meta = parse_filename(impl_file.name)
                result.update(meta)
                all_results["cs2"].append(result)
                print(f"{result['passed']}/{result['total']} passed")
            except subprocess.TimeoutExpired:
                print("TIMEOUT")
                meta = parse_filename(impl_file.name)
                all_results["cs2"].append(
                    {**meta, "impl_file": impl_file.name, "total": 10, "passed": 0, "failed": 0, "errors": 10, "pass_rate": 0.0, "tests": [], "compile_success": False, "timeout": True}
                )
            except Exception as e:
                print(f"ERROR: {e}")

    # Save raw results
    with open(RESULTS_DIR / "test_results.json", "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for cs_label in ["cs1", "cs2"]:
        if not all_results[cs_label]:
            continue
        print(f"\n{cs_label.upper()}:")
        by_condition = {}
        for r in all_results[cs_label]:
            label = r.get("condition_label", "?")
            by_condition.setdefault(label, []).append(r["pass_rate"])

        for label in sorted(by_condition):
            rates = by_condition[label]
            mean = sum(rates) / len(rates)
            print(f"  {label}: mean pass rate = {mean:.1%} (n={len(rates)}, rates={[f'{r:.0%}' for r in rates]})")

    # Save summary table
    summary_lines = ["# Downstream Outcome Test Results\n"]
    summary_lines.append("| CS | Condition | Run | Pass Rate | Passed | Total |")
    summary_lines.append("|---|---|---|---|---|---|")
    for cs_label in ["cs1", "cs2"]:
        for r in sorted(all_results[cs_label], key=lambda x: (x.get("condition_label", ""), x.get("run", ""))):
            summary_lines.append(
                f"| {r.get('cs', '')} | {r.get('condition_label', '')}:{r.get('condition', '')} | {r.get('run', '')} | {r['pass_rate']:.0%} | {r['passed']} | {r['total']} |"
            )

    with open(RESULTS_DIR / "summary.md", "w") as f:
        f.write("\n".join(summary_lines) + "\n")

    print(f"\nResults saved to {RESULTS_DIR / 'test_results.json'}")
    print(f"Summary saved to {RESULTS_DIR / 'summary.md'}")


if __name__ == "__main__":
    main()
