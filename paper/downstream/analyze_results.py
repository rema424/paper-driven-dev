#!/usr/bin/env python3
"""Statistical analysis of downstream outcome test results.

Analyzes test pass rates across conditions to determine whether
structured analysis requirements lead to better implementations.

Usage:
    python3 paper/downstream/analyze_results.py
"""

import json
import math
import random
from pathlib import Path

RESULTS_FILE = Path(__file__).parent / "results" / "test_results.json"
SEED = 44
N_PERMUTATIONS = 10_000
N_BOOTSTRAP = 10_000
ALPHA = 0.025  # one-sided, Bonferroni-like consistency with main analysis


def load_data():
    """Load and structure test results."""
    with open(RESULTS_FILE) as f:
        raw = json.load(f)

    data = []
    for cs_label in ["cs1", "cs2"]:
        for entry in raw[cs_label]:
            data.append({
                "cs": cs_label,
                "condition": entry["condition_label"],
                "run": entry["run"],
                "pass_rate": entry["pass_rate"],
                "passed": entry["passed"],
                "total": entry["total"],
                "compile_success": entry.get("compile_success", True),
            })
    return data


def descriptive_stats(data):
    """Print descriptive statistics by condition."""
    print("=" * 60)
    print("1. DESCRIPTIVE STATISTICS")
    print("=" * 60)

    # By condition (pooled across CS)
    by_condition = {}
    for d in data:
        by_condition.setdefault(d["condition"], []).append(d["pass_rate"])

    print("\n### Pass Rate by Condition (pooled)")
    print(f"{'Condition':<15} {'Mean':>8} {'SD':>8} {'N':>4} {'Values'}")
    for cond in sorted(by_condition):
        vals = by_condition[cond]
        mean = sum(vals) / len(vals)
        sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / max(len(vals) - 1, 1))
        print(f"{cond:<15} {mean:>8.3f} {sd:>8.3f} {len(vals):>4} {[round(v, 2) for v in vals]}")

    # By condition × CS
    print("\n### Pass Rate by Condition × CS")
    by_cond_cs = {}
    for d in data:
        key = (d["condition"], d["cs"])
        by_cond_cs.setdefault(key, []).append(d["pass_rate"])

    print(f"{'CS':<5} {'Cond':<15} {'Mean':>8} {'SD':>8} {'N':>4}")
    for cs in ["cs1", "cs2"]:
        for cond in sorted(set(d["condition"] for d in data)):
            key = (cond, cs)
            if key in by_cond_cs:
                vals = by_cond_cs[key]
                mean = sum(vals) / len(vals)
                sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / max(len(vals) - 1, 1))
                print(f"{cs:<5} {cond:<15} {mean:>8.3f} {sd:>8.3f} {len(vals):>4}")

    # Grouped: {C,D} vs {A,B}
    cd_vals = [d["pass_rate"] for d in data if d["condition"] in ("C", "D")]
    ab_vals = [d["pass_rate"] for d in data if d["condition"] in ("A", "B")]
    cd_mean = sum(cd_vals) / len(cd_vals) if cd_vals else 0
    ab_mean = sum(ab_vals) / len(ab_vals) if ab_vals else 0
    print(f"\n### Grouped")
    print(f"  {{C,D}} mean = {cd_mean:.3f} (n={len(cd_vals)})")
    print(f"  {{A,B}} mean = {ab_mean:.3f} (n={len(ab_vals)})")
    print(f"  Difference = {cd_mean - ab_mean:.3f}")

    return by_condition


def stratified_permutation_test(data, group1_labels, group2_labels, n_perms=10_000):
    """Stratified permutation test (stratified by CS), one-sided: group1 > group2."""
    random.seed(SEED)

    # Organize by CS
    strata = {}
    for d in data:
        strata.setdefault(d["cs"], []).append(d)

    # Observed statistic: mean(group1) - mean(group2), computed within each stratum
    def compute_stat(data_items):
        g1_vals = [d["pass_rate"] for d in data_items if d["condition"] in group1_labels]
        g2_vals = [d["pass_rate"] for d in data_items if d["condition"] in group2_labels]
        if not g1_vals or not g2_vals:
            return 0
        return (sum(g1_vals) / len(g1_vals)) - (sum(g2_vals) / len(g2_vals))

    observed = compute_stat(data)

    # Permutation
    count_ge = 0
    for _ in range(n_perms):
        permuted = []
        for cs, items in strata.items():
            labels = [d["condition"] for d in items]
            random.shuffle(labels)
            for i, item in enumerate(items):
                permuted.append({**item, "condition": labels[i]})
        stat = compute_stat(permuted)
        if stat >= observed:
            count_ge += 1

    p_value = (count_ge + 1) / (n_perms + 1)
    return observed, p_value


def cliffs_delta(group1, group2):
    """Compute Cliff's delta between two groups."""
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        return 0.0
    count = sum(
        (1 if x > y else -1 if x < y else 0)
        for x in group1
        for y in group2
    )
    return count / (n1 * n2)


def bootstrap_ci(group1, group2, n_boot=10_000, alpha=0.05):
    """Bootstrap 95% CI for Cliff's delta."""
    random.seed(SEED + 1)
    deltas = []
    for _ in range(n_boot):
        g1 = random.choices(group1, k=len(group1))
        g2 = random.choices(group2, k=len(group2))
        deltas.append(cliffs_delta(g1, g2))
    deltas.sort()
    lo = deltas[int(n_boot * alpha / 2)]
    hi = deltas[int(n_boot * (1 - alpha / 2))]
    return lo, hi


def main_analysis_externalization(data):
    """Main Analysis A: {C,D} vs {A,B} on pass rate."""
    print("\n" + "=" * 60)
    print("2. MAIN ANALYSIS: EXTERNALIZATION EFFECT ON PASS RATE")
    print("   {C,D} vs {A,B}, one-sided stratified permutation test")
    print("=" * 60)

    obs, p = stratified_permutation_test(
        data, group1_labels={"C", "D"}, group2_labels={"A", "B"}, n_perms=N_PERMUTATIONS
    )
    print(f"\n  Observed diff (CD - AB): {obs:.3f}")
    print(f"  p-value: {p:.4f}")
    print(f"  Significant at α={ALPHA}? {'Yes' if p < ALPHA else 'No'}")

    # Effect size
    cd = [d["pass_rate"] for d in data if d["condition"] in ("C", "D")]
    ab = [d["pass_rate"] for d in data if d["condition"] in ("A", "B")]
    delta = cliffs_delta(cd, ab)
    lo, hi = bootstrap_ci(cd, ab, N_BOOTSTRAP)
    print(f"\n  Cliff's δ = {delta:.3f} [{lo:.3f}, {hi:.3f}]")
    interp = (
        "Complete separation" if abs(delta) == 1.0
        else "Large" if abs(delta) >= 0.474
        else "Medium" if abs(delta) >= 0.33
        else "Small" if abs(delta) >= 0.147
        else "Negligible"
    )
    print(f"  Interpretation: {interp}")

    return obs, p, delta, lo, hi


def main_analysis_framing(data):
    """Main Analysis B: C vs D on pass rate."""
    print("\n" + "=" * 60)
    print("3. FRAMING EFFECT: C vs D ON PASS RATE")
    print("   One-sided stratified permutation test (C > D)")
    print("=" * 60)

    obs, p = stratified_permutation_test(
        data, group1_labels={"C"}, group2_labels={"D"}, n_perms=N_PERMUTATIONS
    )
    print(f"\n  Observed diff (C - D): {obs:.3f}")
    print(f"  p-value: {p:.4f}")
    print(f"  Significant at α={ALPHA}? {'Yes' if p < ALPHA else 'No'}")

    c_vals = [d["pass_rate"] for d in data if d["condition"] == "C"]
    d_vals = [d["pass_rate"] for d in data if d["condition"] == "D"]
    delta = cliffs_delta(c_vals, d_vals)
    lo, hi = bootstrap_ci(c_vals, d_vals, N_BOOTSTRAP)
    print(f"\n  Cliff's δ = {delta:.3f} [{lo:.3f}, {hi:.3f}]")

    return obs, p, delta, lo, hi


def posthoc_b_vs_a(data):
    """Post-hoc: B vs A."""
    print("\n" + "=" * 60)
    print("4. POST-HOC: B vs A ON PASS RATE")
    print("=" * 60)

    obs, p = stratified_permutation_test(
        data, group1_labels={"B"}, group2_labels={"A"}, n_perms=N_PERMUTATIONS
    )
    print(f"\n  Observed diff (B - A): {obs:.3f}")
    print(f"  p-value: {p:.4f}")

    b_vals = [d["pass_rate"] for d in data if d["condition"] == "B"]
    a_vals = [d["pass_rate"] for d in data if d["condition"] == "A"]
    delta = cliffs_delta(b_vals, a_vals)
    lo, hi = bootstrap_ci(b_vals, a_vals, N_BOOTSTRAP)
    print(f"\n  Cliff's δ = {delta:.3f} [{lo:.3f}, {hi:.3f}]")


def pairwise_effects(data):
    """Pairwise Cliff's delta for all condition pairs."""
    print("\n" + "=" * 60)
    print("5. PAIRWISE EFFECT SIZES")
    print("=" * 60)

    conditions = sorted(set(d["condition"] for d in data))
    by_cond = {}
    for d in data:
        by_cond.setdefault(d["condition"], []).append(d["pass_rate"])

    print(f"\n{'Pair':<10} {'δ':>8} {'95% CI':>20}")
    for i, c1 in enumerate(conditions):
        for c2 in conditions[i + 1 :]:
            delta = cliffs_delta(by_cond[c1], by_cond[c2])
            lo, hi = bootstrap_ci(by_cond[c1], by_cond[c2], N_BOOTSTRAP)
            print(f"{c1} vs {c2:<5} {delta:>8.3f} [{lo:.3f}, {hi:.3f}]")


def compile_success_analysis(data):
    """Analyze compile/run success rates by condition."""
    print("\n" + "=" * 60)
    print("6. COMPILE/RUN SUCCESS RATE")
    print("=" * 60)

    by_condition = {}
    for d in data:
        by_condition.setdefault(d["condition"], []).append(d["compile_success"])

    for cond in sorted(by_condition):
        vals = by_condition[cond]
        rate = sum(vals) / len(vals)
        print(f"  {cond}: {sum(vals)}/{len(vals)} = {rate:.0%}")


def per_test_analysis(data_raw):
    """Analyze per-test pass rates across conditions."""
    print("\n" + "=" * 60)
    print("7. PER-TEST ANALYSIS")
    print("=" * 60)

    with open(RESULTS_FILE) as f:
        raw = json.load(f)

    for cs_label in ["cs1", "cs2"]:
        print(f"\n### {cs_label.upper()}")
        test_by_cond = {}
        for entry in raw[cs_label]:
            cond = entry["condition_label"]
            for t in entry.get("tests", []):
                key = (cond, t["name"])
                test_by_cond.setdefault(key, []).append(1 if t["result"] == "passed" else 0)

        # Aggregate by test name
        test_names = sorted(set(k[1] for k in test_by_cond))
        conds = sorted(set(k[0] for k in test_by_cond))

        if test_names:
            header = f"{'Test':<45}" + "".join(f"{c:>6}" for c in conds)
            print(header)
            for tn in test_names:
                row = f"{tn:<45}"
                for c in conds:
                    vals = test_by_cond.get((c, tn), [])
                    if vals:
                        rate = sum(vals) / len(vals)
                        row += f"{rate:>5.0%} "
                    else:
                        row += "   N/A"
                print(row)


def main():
    if not RESULTS_FILE.exists():
        print(f"Error: {RESULTS_FILE} not found. Run run_tests.py first.")
        return

    data = load_data()
    if not data:
        print("No data found.")
        return

    print(f"Loaded {len(data)} observations")
    print(f"Seed: {SEED}, Permutations: {N_PERMUTATIONS:,}, Bootstrap: {N_BOOTSTRAP:,}")

    descriptive_stats(data)
    main_analysis_externalization(data)
    main_analysis_framing(data)
    posthoc_b_vs_a(data)
    pairwise_effects(data)
    compile_success_analysis(data)
    per_test_analysis(data)


if __name__ == "__main__":
    main()
