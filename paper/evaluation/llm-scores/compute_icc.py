#!/usr/bin/env python3
"""
Compute ICC(2,1) and condition estimation accuracy for LLM blind evaluation.

Evaluators: Author, GPT-5.2, Opus 4.6, Sonnet 4.6
Targets: 40 blinded outputs (output-001 through output-040)
Indicators: CR, TP, CD (co-primary and exploratory)

ICC model: Two-way random, single measures, absolute agreement — ICC(2,1)
"""

import math
import json
from collections import Counter

# ============================================================
# DATA
# ============================================================

# True conditions from mapping-secret.json
# output-NNN -> condition letter
TRUE_CONDITIONS = [
    "B", "A", "C", "D", "B", "A", "C", "C", "A", "C",  # 001-010
    "A", "B", "A", "D", "C", "C", "D", "B", "C", "A",  # 011-020
    "A", "C", "D", "B", "D", "D", "D", "C", "A", "A",  # 021-030
    "D", "B", "B", "B", "B", "C", "D", "D", "A", "B",  # 031-040
]

# Mapping: output-NNN -> original filename
OUTPUT_MAP = {
    1: "cs1-paper-format-run5", 2: "cs1-conventional-run4",
    3: "cs1-pdd-template-run1", 4: "cs2-checklist-run2",
    5: "cs2-paper-format-run1", 6: "cs2-conventional-run5",
    7: "cs2-pdd-template-run1", 8: "cs1-pdd-template-run2",
    9: "cs1-conventional-run5", 10: "cs2-pdd-template-run3",
    11: "cs2-conventional-run2", 12: "cs2-paper-format-run4",
    13: "cs2-conventional-run4", 14: "cs1-checklist-run4",
    15: "cs1-pdd-template-run3", 16: "cs2-pdd-template-run5",
    17: "cs2-checklist-run1", 18: "cs2-paper-format-run2",
    19: "cs1-pdd-template-run4", 20: "cs2-conventional-run3",
    21: "cs2-conventional-run1", 22: "cs2-pdd-template-run2",
    23: "cs2-checklist-run3", 24: "cs2-paper-format-run5",
    25: "cs1-checklist-run5", 26: "cs1-checklist-run2",
    27: "cs2-checklist-run5", 28: "cs2-pdd-template-run4",
    29: "cs1-conventional-run3", 30: "cs1-conventional-run1",
    31: "cs2-checklist-run4", 32: "cs2-paper-format-run3",
    33: "cs1-paper-format-run1", 34: "cs1-paper-format-run2",
    35: "cs1-paper-format-run4", 36: "cs1-pdd-template-run5",
    37: "cs1-checklist-run1", 38: "cs1-checklist-run3",
    39: "cs1-conventional-run2", 40: "cs1-paper-format-run3",
}

# Scores: [output-001 .. output-040], each row = [Author, GPT-5.2, Opus, Sonnet]
# Rater indices: 0=Author, 1=GPT-5.2, 2=Opus, 3=Sonnet

CR = [
    [0, 0, 0, 0],  # 001
    [0, 0, 0, 0],  # 002
    [3, 3, 3, 3],  # 003
    [4, 4, 4, 4],  # 004
    [1, 0, 0, 0],  # 005
    [1, 1, 0, 0],  # 006
    [4, 4, 4, 4],  # 007
    [3, 3, 3, 3],  # 008
    [0, 0, 0, 0],  # 009
    [3, 3, 3, 3],  # 010
    [0, 0, 0, 0],  # 011
    [1, 0, 1, 1],  # 012
    [0, 0, 0, 0],  # 013
    [3, 3, 3, 3],  # 014
    [3, 3, 3, 3],  # 015
    [3, 3, 3, 3],  # 016
    [4, 4, 4, 4],  # 017
    [1, 0, 1, 0],  # 018
    [3, 3, 3, 3],  # 019
    [1, 1, 1, 1],  # 020
    [1, 1, 1, 1],  # 021
    [3, 3, 3, 3],  # 022
    [4, 4, 4, 4],  # 023
    [1, 1, 1, 0],  # 024
    [4, 4, 4, 4],  # 025
    [3, 3, 3, 3],  # 026
    [4, 4, 4, 4],  # 027
    [4, 4, 4, 4],  # 028
    [0, 0, 0, 0],  # 029
    [0, 0, 0, 0],  # 030
    [4, 4, 4, 4],  # 031
    [1, 0, 0, 0],  # 032
    [0, 0, 0, 0],  # 033
    [0, 0, 0, 0],  # 034
    [0, 0, 0, 0],  # 035
    [3, 3, 3, 3],  # 036
    [3, 3, 3, 3],  # 037
    [4, 4, 4, 4],  # 038
    [0, 0, 0, 0],  # 039
    [0, 0, 0, 0],  # 040
]

TP = [
    [2, 0, 0, 0],  # 001
    [2, 0, 0, 0],  # 002
    [4, 4, 4, 4],  # 003
    [5, 2, 5, 5],  # 004
    [3, 0, 0, 0],  # 005
    [0, 0, 0, 0],  # 006
    [5, 4, 5, 5],  # 007
    [5, 5, 5, 5],  # 008
    [0, 0, 0, 0],  # 009
    [5, 4, 5, 5],  # 010
    [0, 0, 0, 0],  # 011
    [2, 0, 0, 0],  # 012
    [0, 0, 0, 0],  # 013
    [5, 5, 5, 5],  # 014
    [5, 5, 5, 5],  # 015
    [5, 3, 5, 5],  # 016
    [5, 5, 5, 5],  # 017
    [2, 0, 0, 0],  # 018
    [6, 6, 6, 6],  # 019
    [0, 0, 0, 0],  # 020
    [0, 0, 0, 0],  # 021
    [5, 5, 5, 5],  # 022
    [6, 6, 6, 6],  # 023
    [1, 0, 0, 0],  # 024
    [5, 5, 5, 5],  # 025
    [4, 4, 4, 4],  # 026
    [6, 6, 6, 6],  # 027
    [6, 6, 6, 6],  # 028
    [0, 0, 0, 0],  # 029
    [0, 0, 0, 0],  # 030
    [6, 3, 5, 6],  # 031
    [2, 0, 0, 0],  # 032
    [2, 0, 0, 0],  # 033
    [2, 0, 6, 0],  # 034
    [2, 0, 0, 0],  # 035
    [6, 6, 6, 6],  # 036
    [5, 5, 5, 5],  # 037
    [6, 6, 6, 6],  # 038
    [0, 0, 0, 0],  # 039
    [2, 0, 0, 0],  # 040
]

CD = [
    [3, 0, 0, 0],  # 001
    [3, 1, 0, 0],  # 002
    [5, 4, 3, 3],  # 003
    [3, 2, 2, 2],  # 004
    [2, 2, 2, 2],  # 005
    [1, 0, 0, 0],  # 006
    [5, 4, 3, 3],  # 007
    [3, 2, 2, 2],  # 008
    [3, 2, 2, 2],  # 009
    [4, 3, 2, 2],  # 010
    [0, 1, 0, 0],  # 011
    [1, 0, 1, 0],  # 012
    [2, 2, 0, 0],  # 013
    [3, 3, 3, 3],  # 014
    [4, 3, 3, 2],  # 015
    [4, 3, 3, 3],  # 016
    [4, 3, 3, 3],  # 017
    [1, 1, 1, 1],  # 018
    [3, 3, 3, 3],  # 019
    [0, 0, 0, 0],  # 020
    [0, 1, 0, 0],  # 021
    [3, 2, 2, 2],  # 022
    [3, 3, 3, 3],  # 023
    [2, 1, 1, 1],  # 024
    [4, 3, 2, 2],  # 025
    [3, 3, 3, 2],  # 026
    [3, 2, 2, 2],  # 027
    [4, 4, 1, 1],  # 028
    [3, 0, 0, 0],  # 029
    [3, 2, 0, 0],  # 030
    [3, 3, 3, 3],  # 031
    [2, 1, 1, 1],  # 032
    [4, 1, 0, 1],  # 033
    [4, 4, 3, 3],  # 034
    [4, 0, 0, 0],  # 035
    [4, 3, 3, 3],  # 036
    [4, 4, 2, 3],  # 037
    [3, 3, 2, 3],  # 038
    [4, 0, 0, 2],  # 039
    [3, 3, 1, 3],  # 040
]

# Condition guesses by LLM evaluators
# (Author is not included — knows true condition)
# Index: [GPT-5.2, Opus, Sonnet]
CONDITION_GUESSES = [
    ["B", "B", "B"],  # 001
    ["D", "D", "D"],  # 002
    ["C", "C", "C"],  # 003
    ["D", "C", "C"],  # 004
    ["B", "B", "B"],  # 005
    ["A", "A", "A"],  # 006
    ["C", "C", "C"],  # 007
    ["C", "C", "C"],  # 008
    ["A", "A", "A"],  # 009
    ["C", "C", "C"],  # 010
    ["A", "A", "A"],  # 011
    ["B", "B", "B"],  # 012
    ["A", "A", "A"],  # 013
    ["D", "D", "D"],  # 014
    ["C", "C", "C"],  # 015
    ["C", "C", "C"],  # 016
    ["D", "D", "D"],  # 017
    ["B", "B", "B"],  # 018
    ["C", "C", "C"],  # 019
    ["A", "A", "A"],  # 020
    ["A", "A", "A"],  # 021
    ["C", "C", "C"],  # 022
    ["D", "D", "D"],  # 023
    ["B", "B", "B"],  # 024
    ["D", "D", "D"],  # 025
    ["D", "D", "C"],  # 026
    ["D", "D", "D"],  # 027
    ["C", "C", "C"],  # 028
    ["A", "A", "A"],  # 029
    ["A", "A", "A"],  # 030
    ["D", "D", "A"],  # 031
    ["B", "B", "B"],  # 032
    ["B", "B", "B"],  # 033
    ["B", "C", "B"],  # 034
    ["B", "C", "B"],  # 035
    ["C", "C", "C"],  # 036
    ["D", "D", "A"],  # 037
    ["D", "D", "A"],  # 038
    ["A", "A", "D"],  # 039
    ["B", "B", "B"],  # 040
]


# ============================================================
# ICC(2,1) COMPUTATION
# ============================================================

def compute_icc_2_1(data):
    """
    Compute ICC(2,1): two-way random, single measures, absolute agreement.

    Parameters:
        data: list of lists, shape (n_targets, k_raters)

    Returns:
        dict with icc, ms_rows, ms_cols, ms_error, f_value, n, k
    """
    n = len(data)
    k = len(data[0])

    # Grand mean
    total = sum(x for row in data for x in row)
    grand_mean = total / (n * k)

    # Row means (target means)
    row_means = [sum(row) / k for row in data]

    # Column means (rater means)
    col_means = [sum(data[i][j] for i in range(n)) / n for j in range(k)]

    # Sum of squares
    ss_total = sum((data[i][j] - grand_mean) ** 2
                   for i in range(n) for j in range(k))
    ss_rows = k * sum((rm - grand_mean) ** 2 for rm in row_means)
    ss_cols = n * sum((cm - grand_mean) ** 2 for cm in col_means)
    ss_error = ss_total - ss_rows - ss_cols

    # Mean squares
    ms_rows = ss_rows / (n - 1) if n > 1 else 0
    ms_cols = ss_cols / (k - 1) if k > 1 else 0
    ms_error = ss_error / ((n - 1) * (k - 1)) if (n > 1 and k > 1) else 0

    # ICC(2,1)
    denom = ms_rows + (k - 1) * ms_error + k * (ms_cols - ms_error) / n
    icc = (ms_rows - ms_error) / denom if denom != 0 else 0

    # F-test for rows (targets differ)
    f_value = ms_rows / ms_error if ms_error > 0 else float('inf')

    return {
        "icc": icc,
        "ms_rows": ms_rows,
        "ms_cols": ms_cols,
        "ms_error": ms_error,
        "f_value": f_value,
        "n": n,
        "k": k,
    }


def compute_pairwise_icc(data, rater_names):
    """Compute ICC(2,1) for all pairs of raters."""
    k = len(data[0])
    results = []
    for i in range(k):
        for j in range(i + 1, k):
            pair_data = [[row[i], row[j]] for row in data]
            r = compute_icc_2_1(pair_data)
            results.append({
                "rater_a": rater_names[i],
                "rater_b": rater_names[j],
                "icc": r["icc"],
            })
    return results


# ============================================================
# CONDITION ESTIMATION ANALYSIS
# ============================================================

def compute_condition_accuracy(true_conds, guesses, evaluator_names):
    """Compute accuracy and confusion matrix for condition estimation."""
    results = {}
    for eidx, ename in enumerate(evaluator_names):
        correct = 0
        total = len(true_conds)
        confusion = {c: Counter() for c in "ABCD"}
        for i in range(total):
            true_c = true_conds[i]
            guess_c = guesses[i][eidx]
            confusion[true_c][guess_c] += 1
            if true_c == guess_c:
                correct += 1
        results[ename] = {
            "accuracy": correct / total,
            "correct": correct,
            "total": total,
            "confusion": confusion,
        }
    return results


# ============================================================
# MAIN
# ============================================================

def main():
    rater_names = ["Author", "GPT-5.2", "Opus 4.6", "Sonnet 4.6"]
    llm_names = ["GPT-5.2", "Opus 4.6", "Sonnet 4.6"]

    indicators = {
        "CR": CR,
        "TP": TP,
        "CD": CD,
    }

    print("=" * 70)
    print("LLM BLIND EVALUATION — ICC ANALYSIS")
    print("=" * 70)
    print(f"Targets: {len(CR)} outputs")
    print(f"Raters: {', '.join(rater_names)}")
    print()

    # --- ICC(2,1) for each indicator ---
    print("-" * 70)
    print("ICC(2,1) — 4 Raters (Author + 3 LLM)")
    print("-" * 70)
    print(f"{'Indicator':<12} {'ICC(2,1)':>10} {'MS_Row':>10} {'MS_Col':>10} "
          f"{'MS_Error':>10} {'F':>10} {'Interpret':>15}")
    print("-" * 70)

    icc_results = {}
    for name, data in indicators.items():
        r = compute_icc_2_1(data)
        icc_results[name] = r
        # Interpretation
        icc_val = r["icc"]
        if icc_val >= 0.90:
            interp = "Excellent"
        elif icc_val >= 0.75:
            interp = "Good"
        elif icc_val >= 0.60:
            interp = "Moderate"
        elif icc_val >= 0.40:
            interp = "Fair"
        else:
            interp = "Poor"

        print(f"{name:<12} {icc_val:>10.4f} {r['ms_rows']:>10.4f} "
              f"{r['ms_cols']:>10.4f} {r['ms_error']:>10.4f} "
              f"{r['f_value']:>10.2f} {interp:>15}")

    print()
    print("Pass criterion: ICC >= 0.60 (moderate agreement)")
    for name, r in icc_results.items():
        status = "PASS" if r["icc"] >= 0.60 else "FAIL"
        print(f"  {name}: {r['icc']:.4f} — {status}")

    # --- Pairwise ICC ---
    print()
    print("-" * 70)
    print("Pairwise ICC(2,1)")
    print("-" * 70)

    for ind_name, data in indicators.items():
        print(f"\n  {ind_name}:")
        pairs = compute_pairwise_icc(data, rater_names)
        for p in pairs:
            print(f"    {p['rater_a']:>12} vs {p['rater_b']:<12}: "
                  f"ICC = {p['icc']:.4f}")

    # --- LLM-only ICC (excluding author) ---
    print()
    print("-" * 70)
    print("ICC(2,1) — 3 LLM Raters Only (excluding Author)")
    print("-" * 70)

    for ind_name, data in indicators.items():
        llm_data = [[row[1], row[2], row[3]] for row in data]
        r = compute_icc_2_1(llm_data)
        print(f"  {ind_name}: ICC = {r['icc']:.4f}")

    # --- Condition Estimation Accuracy ---
    print()
    print("=" * 70)
    print("CONDITION ESTIMATION ACCURACY")
    print("=" * 70)

    cond_results = compute_condition_accuracy(
        TRUE_CONDITIONS, CONDITION_GUESSES, llm_names
    )

    for ename, res in cond_results.items():
        print(f"\n{ename}: {res['correct']}/{res['total']} "
              f"= {res['accuracy']:.1%}")
        print(f"  {'True\\Guess':>10}  {'A':>4} {'B':>4} {'C':>4} {'D':>4}")
        for true_c in "ABCD":
            row = res["confusion"][true_c]
            print(f"  {true_c:>10}  {row.get('A',0):>4} {row.get('B',0):>4} "
                  f"{row.get('C',0):>4} {row.get('D',0):>4}")

    # --- Overall condition estimation agreement ---
    print()
    print("-" * 70)
    print("Inter-LLM Agreement on Condition Estimation")
    print("-" * 70)
    agree_count = 0
    for i in range(len(CONDITION_GUESSES)):
        if (CONDITION_GUESSES[i][0] == CONDITION_GUESSES[i][1] ==
                CONDITION_GUESSES[i][2]):
            agree_count += 1
    print(f"All 3 LLMs agree: {agree_count}/{len(CONDITION_GUESSES)} "
          f"= {agree_count/len(CONDITION_GUESSES):.1%}")

    # --- Author vs LLM Mean Absolute Difference ---
    print()
    print("-" * 70)
    print("Mean Absolute Difference: Author vs Each LLM")
    print("-" * 70)
    print(f"{'Indicator':<12} {'GPT-5.2':>10} {'Opus 4.6':>10} {'Sonnet 4.6':>10}")
    for ind_name, data in indicators.items():
        diffs = []
        for j in range(1, 4):  # LLM raters
            d = sum(abs(data[i][0] - data[i][j]) for i in range(len(data)))
            d /= len(data)
            diffs.append(d)
        print(f"{ind_name:<12} {diffs[0]:>10.3f} {diffs[1]:>10.3f} "
              f"{diffs[2]:>10.3f}")

    # --- Summary for paper ---
    print()
    print("=" * 70)
    print("SUMMARY FOR PAPER §4.6")
    print("=" * 70)
    print()
    print("Table: ICC(2,1) by indicator (4 raters)")
    print(f"| Indicator | ICC(2,1) | Interpretation |")
    print(f"|-----------|----------|----------------|")
    for name, r in icc_results.items():
        icc_val = r["icc"]
        if icc_val >= 0.90:
            interp = "Excellent"
        elif icc_val >= 0.75:
            interp = "Good"
        elif icc_val >= 0.60:
            interp = "Moderate"
        elif icc_val >= 0.40:
            interp = "Fair"
        else:
            interp = "Poor"
        print(f"| {name:<9} | {icc_val:.3f}    | {interp:<14} |")

    print()
    print("Table: Condition estimation accuracy")
    print(f"| Evaluator  | Accuracy |")
    print(f"|------------|----------|")
    for ename, res in cond_results.items():
        print(f"| {ename:<10} | {res['accuracy']:.1%}    |")

    # --- JSON output for further processing ---
    output = {
        "icc": {name: {"icc": r["icc"], "f": r["f_value"]}
                for name, r in icc_results.items()},
        "condition_accuracy": {
            ename: {"accuracy": res["accuracy"],
                    "correct": res["correct"],
                    "total": res["total"]}
            for ename, res in cond_results.items()
        },
    }
    with open("paper/evaluation/llm-scores/icc-results.json", "w") as f:
        json.dump(output, f, indent=2)
    print()
    print("Results saved to paper/evaluation/llm-scores/icc-results.json")


if __name__ == "__main__":
    main()
