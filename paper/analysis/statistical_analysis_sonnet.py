"""
Statistical analysis for Sonnet 4.6 external validity experiment.
Replicates protocol v1 §7 analysis with N=3 per condition per CS.

Seed: 43 (distinct from Phase 2 seed=42)
Permutation iterations: 10,000
Bootstrap iterations: 10,000
"""

import random
import math
from typing import List

SEED = 43
N_PERM = 10_000
N_BOOT = 10_000

# ── Raw data ──────────────────────────────────────────────────────

DATA = {
    "CS1-A": {"CR": [1, 0, 0], "TP": [0, 0, 0], "CD": [4, 3, 5], "EA": [3, 3, 4], "FI": [0, 0, 0], "TL": [259, 305, 341]},
    "CS1-B": {"CR": [0, 0, 1], "TP": [0, 0, 0], "CD": [3, 3, 4], "EA": [3, 3, 2], "FI": [3, 2, 0], "TL": [373, 236, 310]},
    "CS1-C": {"CR": [3, 4, 3], "TP": [6, 7, 7], "CD": [3, 4, 3], "EA": [4, 4, 4], "FI": [0, 1, 0], "TL": [342, 413, 341]},
    "CS1-D": {"CR": [3, 3, 3], "TP": [5, 4, 6], "CD": [5, 4, 6], "EA": [4, 4, 4], "FI": [0, 0, 0], "TL": [332, 339, 435]},
    "CS2-A": {"CR": [2, 2, 2], "TP": [0, 0, 0], "CD": [3, 4, 3], "EA": [3, 0, 2], "FI": [0, 0, 0], "TL": [476, 311, 239]},
    "CS2-B": {"CR": [2, 2, 2], "TP": [0, 0, 0], "CD": [3, 3, 3], "EA": [3, 3, 2], "FI": [0, 0, 0], "TL": [328, 289, 384]},
    "CS2-C": {"CR": [3, 3, 3], "TP": [9, 6, 6], "CD": [3, 4, 3], "EA": [4, 4, 4], "FI": [0, 0, 0], "TL": [330, 325, 371]},
    "CS2-D": {"CR": [3, 4, 3], "TP": [6, 6, 5], "CD": [4, 3, 5], "EA": [4, 4, 4], "FI": [0, 0, 0], "TL": [292, 244, 289]},
}

CONDITIONS = ["A", "B", "C", "D"]
CASE_STUDIES = ["CS1", "CS2"]


def mean(xs: List[float]) -> float:
    return sum(xs) / len(xs)


def sd(xs: List[float]) -> float:
    m = mean(xs)
    if len(xs) < 2:
        return 0.0
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def get_values(cs: str, cond: str, indicator: str) -> List[float]:
    return [float(x) for x in DATA[f"{cs}-{cond}"][indicator]]


def get_all_values(cond: str, indicator: str) -> List[float]:
    result = []
    for cs in CASE_STUDIES:
        result.extend(get_values(cs, cond, indicator))
    return result


# ── §7.2 Stratified Permutation Test ─────────────────────────────

def stratified_mean_diff(group1_conds, group2_conds, indicator):
    diffs = []
    for cs in CASE_STUDIES:
        g1 = []
        for c in group1_conds:
            g1.extend(get_values(cs, c, indicator))
        g2 = []
        for c in group2_conds:
            g2.extend(get_values(cs, c, indicator))
        diffs.append(mean(g1) - mean(g2))
    return mean(diffs)


def stratified_permutation_test(group1_conds, group2_conds, indicator, n_perm=N_PERM, seed=SEED):
    rng = random.Random(seed)
    observed = stratified_mean_diff(group1_conds, group2_conds, indicator)

    count_ge = 0
    for _ in range(n_perm):
        perm_stat_parts = []
        for cs in CASE_STUDIES:
            g1 = []
            for c in group1_conds:
                g1.extend(get_values(cs, c, indicator))
            g2 = []
            for c in group2_conds:
                g2.extend(get_values(cs, c, indicator))
            pooled = g1 + g2
            rng.shuffle(pooled)
            n1 = len(g1)
            perm_stat_parts.append(mean(pooled[:n1]) - mean(pooled[n1:]))
        perm_stat = mean(perm_stat_parts)
        if perm_stat >= observed:
            count_ge += 1

    p_value = count_ge / n_perm
    return observed, p_value


# ── §7.4 TOST ─────────────────────────────────────────────────────

def stratified_tost(cond1, cond2, indicator, delta, n_perm=N_PERM, seed=SEED):
    observed = stratified_mean_diff([cond1], [cond2], indicator)

    rng_u = random.Random(seed)
    count_upper = 0
    shifted_obs = observed - delta
    for _ in range(n_perm):
        perm_parts = []
        for cs in CASE_STUDIES:
            g1 = get_values(cs, cond1, indicator)
            g2 = get_values(cs, cond2, indicator)
            g1_shifted = [x - delta for x in g1]
            pooled = g1_shifted + g2
            rng_u.shuffle(pooled)
            n1 = len(g1)
            perm_parts.append(mean(pooled[:n1]) - mean(pooled[n1:]))
        perm_diff = mean(perm_parts)
        if perm_diff <= shifted_obs:
            count_upper += 1
    p_upper = count_upper / n_perm

    rng_l = random.Random(seed + 1)
    count_lower = 0
    shifted_obs_l = observed + delta
    for _ in range(n_perm):
        perm_parts = []
        for cs in CASE_STUDIES:
            g1 = get_values(cs, cond1, indicator)
            g2 = get_values(cs, cond2, indicator)
            g1_shifted = [x + delta for x in g1]
            pooled = g1_shifted + g2
            rng_l.shuffle(pooled)
            n1 = len(g1)
            perm_parts.append(mean(pooled[:n1]) - mean(pooled[n1:]))
        perm_diff = mean(perm_parts)
        if perm_diff >= shifted_obs_l:
            count_lower += 1
    p_lower = count_lower / n_perm

    p_tost = max(p_upper, p_lower)
    return observed, p_tost, p_upper, p_lower


# ── Cliff's delta + Bootstrap CI ──────────────────────────────────

def cliffs_delta(x, y):
    nx, ny = len(x), len(y)
    count = 0
    for xi in x:
        for yj in y:
            if xi > yj:
                count += 1
            elif xi < yj:
                count -= 1
    return count / (nx * ny)


def cliffs_delta_bootstrap_ci(x, y, n_boot=N_BOOT, seed=SEED, alpha=0.05):
    rng = random.Random(seed)
    deltas = []
    for _ in range(n_boot):
        bx = [rng.choice(x) for _ in range(len(x))]
        by = [rng.choice(y) for _ in range(len(y))]
        deltas.append(cliffs_delta(bx, by))
    deltas.sort()
    lo_idx = int(n_boot * alpha / 2)
    hi_idx = int(n_boot * (1 - alpha / 2)) - 1
    return cliffs_delta(x, y), deltas[lo_idx], deltas[hi_idx]


def interpret_cliffs_delta(d):
    ad = abs(d)
    if ad < 0.147:
        return "negligible"
    elif ad < 0.33:
        return "small"
    elif ad < 0.474:
        return "medium"
    else:
        return "large"


# ── Main ──────────────────────────────────────────────────────────

def main():
    lines = []

    def p(text=""):
        lines.append(text)
        print(text)

    p("=" * 70)
    p("STATISTICAL ANALYSIS — Sonnet 4.6 External Validity Experiment")
    p(f"Seed={SEED} | N=3/condition/CS | Perms={N_PERM:,} | Boot={N_BOOT:,}")
    p("=" * 70)

    # ── Descriptive ──
    p()
    p("## Descriptive Statistics")
    p()
    for indicator in ["CR", "TP", "CD", "EA", "FI", "TL"]:
        p(f"### {indicator}")
        p(f"  {'Cond':<6} {'CS1 mean(SD)':<18} {'CS2 mean(SD)':<18} {'All mean(SD)':<18}")
        for cond in CONDITIONS:
            cs1 = get_values("CS1", cond, indicator)
            cs2 = get_values("CS2", cond, indicator)
            both = get_all_values(cond, indicator)
            p(f"  {cond:<6} {mean(cs1):>5.2f}({sd(cs1):.2f})      "
              f"{mean(cs2):>5.2f}({sd(cs2):.2f})      "
              f"{mean(both):>5.2f}({sd(both):.2f})")
        p()

    # ── Main Analysis A: Externalization ──
    p("=" * 70)
    p("## Main Analysis A: Externalization Effect {C,D} vs {A,B}")
    p("   One-sided stratified permutation | α = 0.025 (Bonferroni)")
    p("=" * 70)

    p_values_ext = {}
    for indicator in ["CR", "TP"]:
        obs, pval = stratified_permutation_test(["C", "D"], ["A", "B"], indicator)
        p_values_ext[indicator] = pval
        sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.025 else "n.s."
        p(f"  {indicator}: diff = {obs:.3f}, p = {pval:.4f} {sig}")

    # ── Main Analysis B: Framing ──
    p()
    p("=" * 70)
    p("## Main Analysis B: Framing Effect C vs D")
    p("   One-sided stratified permutation (C > D) | α = 0.025 (Bonferroni)")
    p("=" * 70)

    p_values_frm = {}
    for indicator in ["CR", "TP"]:
        obs, pval = stratified_permutation_test(["C"], ["D"], indicator)
        p_values_frm[indicator] = pval
        sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.025 else "n.s."
        p(f"  {indicator}: diff = {obs:.3f}, p = {pval:.4f} {sig}")

    # ── Effect sizes ──
    p()
    p("=" * 70)
    p("## Effect Sizes: Cliff's delta [95% Bootstrap CI]")
    p("=" * 70)

    all_pairs = [("C", "A"), ("C", "B"), ("D", "A"), ("D", "B"), ("C", "D"), ("B", "A")]
    for indicator in ["CR", "TP"]:
        p(f"  ### {indicator}")
        for c1, c2 in all_pairs:
            x = get_all_values(c1, indicator)
            y = get_all_values(c2, indicator)
            d, lo, hi = cliffs_delta_bootstrap_ci(x, y)
            interp = interpret_cliffs_delta(d)
            p(f"    {c1} vs {c2}: δ = {d:.3f} [{lo:.3f}, {hi:.3f}] ({interp})")

    # ── Grouped effect size: {C,D} vs {A,B} ──
    p()
    p("  ### Grouped: {C,D} vs {A,B}")
    for indicator in ["CR", "TP"]:
        cd_vals = get_all_values("C", indicator) + get_all_values("D", indicator)
        ab_vals = get_all_values("A", indicator) + get_all_values("B", indicator)
        d, lo, hi = cliffs_delta_bootstrap_ci(cd_vals, ab_vals)
        interp = interpret_cliffs_delta(d)
        p(f"    {indicator}: δ = {d:.3f} [{lo:.3f}, {hi:.3f}] ({interp})")

    # ── TOST: C vs D ──
    p()
    p("=" * 70)
    p("## Equivalence (TOST): C vs D")
    p("   Δ(CR) = 1.25, Δ(TP) = 3.25 | α = 0.05")
    p("=" * 70)

    for indicator, delta in [("CR", 1.25), ("TP", 3.25)]:
        obs, p_tost, p_upper, p_lower = stratified_tost("C", "D", indicator, delta)
        sig = "*" if p_tost < 0.05 else "n.s."
        p(f"  {indicator}: diff = {obs:.3f}, Δ = {delta}")
        p(f"    p_upper = {p_upper:.4f}, p_lower = {p_lower:.4f}, p_TOST = {p_tost:.4f} {sig}")

    # ── B vs A comparison ──
    p()
    p("=" * 70)
    p("## Post-hoc: B vs A (three-tier hierarchy check)")
    p("=" * 70)

    for indicator in ["CR", "TP"]:
        obs, pval = stratified_permutation_test(["B"], ["A"], indicator)
        sig = "*" if pval < 0.05 else "n.s."
        p(f"  {indicator}: diff = {obs:.3f}, p = {pval:.4f} {sig}")

    # ── Per-CS consistency ──
    p()
    p("=" * 70)
    p("## Per-CS Direction Consistency")
    p("=" * 70)

    for indicator in ["CR", "TP"]:
        p(f"  ### {indicator}")
        for cs in CASE_STUDIES:
            cd_m = mean([mean(get_values(cs, c, indicator)) for c in ["C", "D"]])
            ab_m = mean([mean(get_values(cs, c, indicator)) for c in ["A", "B"]])
            direction = "CD > AB" if cd_m > ab_m else "CD <= AB"
            p(f"    {cs}: CD={cd_m:.2f}, AB={ab_m:.2f} → {direction}")

    # ── Cross-model comparison ──
    p()
    p("=" * 70)
    p("## Cross-Model Comparison (GPT-5.2 vs Sonnet 4.6)")
    p("=" * 70)

    gpt_means = {
        "A": {"CR": 0.30, "TP": 0.20},
        "B": {"CR": 0.50, "TP": 2.00},
        "C": {"CR": 3.20, "TP": 5.20},
        "D": {"CR": 3.70, "TP": 5.30},
    }
    p(f"  {'Cond':<6} {'GPT CR':<10} {'Son CR':<10} {'GPT TP':<10} {'Son TP':<10}")
    for cond in CONDITIONS:
        son_cr = mean(get_all_values(cond, "CR"))
        son_tp = mean(get_all_values(cond, "TP"))
        p(f"  {cond:<6} {gpt_means[cond]['CR']:<10.2f} {son_cr:<10.2f} "
          f"{gpt_means[cond]['TP']:<10.2f} {son_tp:<10.2f}")

    p()
    p("  Direction consistency:")
    for indicator in ["CR", "TP"]:
        gpt_cd = (gpt_means["C"][indicator] + gpt_means["D"][indicator]) / 2
        gpt_ab = (gpt_means["A"][indicator] + gpt_means["B"][indicator]) / 2
        son_cd = mean(get_all_values("C", indicator) + get_all_values("D", indicator))
        son_ab = mean(get_all_values("A", indicator) + get_all_values("B", indicator))
        p(f"    {indicator}: GPT {'{C,D}'}={gpt_cd:.2f} > {'{A,B}'}={gpt_ab:.2f} | "
          f"Sonnet {'{C,D}'}={son_cd:.2f} > {'{A,B}'}={son_ab:.2f}")

    # ── Summary ──
    p()
    p("=" * 70)
    p("## Summary")
    p("=" * 70)

    ext_cr_sig = p_values_ext["CR"] < 0.025
    ext_tp_sig = p_values_ext["TP"] < 0.025

    p(f"  Externalization ({'{C,D}'} vs {'{A,B}'}):")
    p(f"    CR: p = {p_values_ext['CR']:.4f} {'✓ REPLICATED' if ext_cr_sig else '✗'}")
    p(f"    TP: p = {p_values_ext['TP']:.4f} {'✓ REPLICATED' if ext_tp_sig else '✗'}")

    if ext_cr_sig and ext_tp_sig:
        p("  → Externalization effect REPLICATED with Sonnet 4.6")
    else:
        p("  → Externalization effect NOT fully replicated")

    return "\n".join(lines)


if __name__ == "__main__":
    output = main()
    with open("paper/analysis/analysis-results-sonnet.txt", "w") as f:
        f.write(output)
    print(f"\n\nResults saved to paper/analysis/analysis-results-sonnet.txt")
