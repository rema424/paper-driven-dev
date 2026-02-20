"""
Statistical analysis for Paper-Driven Development experiment.
Implements protocol v1 §7 (Statistical Analysis Plan).
No external dependencies — uses only Python standard library.

Seed: 42 (fixed for reproducibility)
Permutation iterations: 10,000
Bootstrap iterations: 10,000
"""

import random
import math
from typing import List, Tuple

SEED = 42
N_PERM = 10_000
N_BOOT = 10_000

# ── Raw data ──────────────────────────────────────────────────────

DATA = {
    "CS1-A": {"CR": [0, 0, 0, 0, 0], "TP": [0, 0, 0, 2, 0], "CD": [3, 4, 3, 3, 3], "EA": [3, 0, 0, 2, 0], "FI": [0, 0, 0, 0, 0], "TL": [32, 40, 33, 56, 52]},
    "CS1-B": {"CR": [0, 0, 0, 0, 0], "TP": [2, 2, 2, 2, 2], "CD": [4, 4, 3, 4, 3], "EA": [0, 2, 0, 0, 0], "FI": [0, 0, 1, 1, 0], "TL": [54, 60, 63, 71, 48]},
    "CS1-C": {"CR": [3, 3, 3, 3, 3], "TP": [4, 5, 5, 6, 6], "CD": [5, 3, 4, 3, 4], "EA": [4, 4, 3, 3, 3], "FI": [0, 1, 0, 0, 0], "TL": [127, 117, 125, 86, 114]},
    "CS1-D": {"CR": [3, 3, 4, 3, 4], "TP": [5, 4, 6, 5, 5], "CD": [4, 3, 3, 3, 4], "EA": [5, 3, 4, 3, 2], "FI": [0, 0, 0, 0, 0], "TL": [102, 89, 62, 71, 95]},
    "CS2-A": {"CR": [1, 0, 1, 0, 1], "TP": [0, 0, 0, 0, 0], "CD": [0, 0, 0, 2, 1], "EA": [2, 0, 0, 0, 0], "FI": [0, 0, 0, 0, 0], "TL": [33, 35, 33, 36, 39]},
    "CS2-B": {"CR": [1, 1, 1, 1, 1], "TP": [3, 2, 2, 2, 1], "CD": [2, 1, 2, 1, 2], "EA": [1, 2, 2, 2, 1], "FI": [0, 1, 1, 1, 2], "TL": [101, 72, 77, 68, 71]},
    "CS2-C": {"CR": [4, 3, 3, 4, 3], "TP": [5, 5, 5, 6, 5], "CD": [5, 3, 4, 4, 4], "EA": [4, 3, 3, 3, 3], "FI": [0, 1, 0, 1, 0], "TL": [106, 82, 101, 95, 100]},
    "CS2-D": {"CR": [4, 4, 4, 4, 4], "TP": [5, 5, 6, 6, 6], "CD": [4, 3, 3, 3, 3], "EA": [5, 4, 3, 4, 4], "FI": [0, 0, 0, 0, 0], "TL": [106, 52, 82, 54, 68]},
}

CONDITIONS = ["A", "B", "C", "D"]
CASE_STUDIES = ["CS1", "CS2"]


def mean(xs: List[float]) -> float:
    return sum(xs) / len(xs)


def sd(xs: List[float]) -> float:
    m = mean(xs)
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
    """Stratified permutation-based TOST using data-shifting approach.

    Upper test: H0: diff >= delta  → shift cond1 down by delta, test left tail
    Lower test: H0: diff <= -delta → shift cond1 up by delta, test right tail
    """
    observed = stratified_mean_diff([cond1], [cond2], indicator)

    # Upper test: H0: diff >= delta, H1: diff < delta
    # Shift cond1 down by delta to create exchangeable data under H0
    rng_u = random.Random(seed)
    count_upper = 0
    shifted_obs = observed - delta  # observed statistic in shifted frame
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

    # Lower test: H0: diff <= -delta, H1: diff > -delta
    # Shift cond1 up by delta to create exchangeable data under H0
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
    p("STATISTICAL ANALYSIS — Paper-Driven Development Experiment")
    p(f"Protocol v1 §7 | Seed={SEED} | Perms={N_PERM:,} | Boot={N_BOOT:,}")
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

    # ── Post-hoc pairwise ──
    p()
    p("=" * 70)
    p("## Post-hoc Pairwise Comparisons")
    p("   α = 0.025/4 ≈ 0.006 per pair per indicator")
    p("=" * 70)

    pairs = [("C", "A"), ("C", "B"), ("D", "A"), ("D", "B")]
    for indicator in ["CR", "TP"]:
        p(f"  ### {indicator}")
        for c1, c2 in pairs:
            obs, pval = stratified_permutation_test([c1], [c2], indicator)
            sig = "***" if pval < 0.001 else "**" if pval < 0.006 else "*" if pval < 0.025 else "n.s."
            p(f"    {c1} vs {c2}: diff = {obs:.3f}, p = {pval:.4f} {sig}")

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

    # ── H_framing: B vs A (EA) ──
    p()
    p("=" * 70)
    p("## Secondary: H_framing — B vs A (Existing Approaches)")
    p("   One-sided (B > A) | α = 0.05")
    p("=" * 70)

    obs, pval = stratified_permutation_test(["B"], ["A"], "EA")
    sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else "n.s."
    p(f"  EA: diff = {obs:.3f}, p = {pval:.4f} {sig}")

    p("  Co-primary B vs A (expect n.s.):")
    for indicator in ["CR", "TP"]:
        obs, pval = stratified_permutation_test(["B"], ["A"], indicator)
        sig = "*" if pval < 0.05 else "n.s."
        p(f"    {indicator}: diff = {obs:.3f}, p = {pval:.4f} {sig}")

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

    # ── Sensitivity: CD ──
    p()
    p("=" * 70)
    p("## Sensitivity: Exploratory (CD)")
    p("=" * 70)

    obs, pval = stratified_permutation_test(["C", "D"], ["A", "B"], "CD")
    p(f"  Externalization: diff = {obs:.3f}, p = {pval:.4f}")

    obs, pval = stratified_permutation_test(["C"], ["D"], "CD")
    p(f"  Framing (C vs D): diff = {obs:.3f}, p = {pval:.4f}")

    # ── Sensitivity: Line-normalized ──
    p()
    p("=" * 70)
    p("## Sensitivity: Line-Normalized CR/TL and TP/TL")
    p("=" * 70)

    for indicator in ["CR", "TP"]:
        p(f"  ### {indicator}/TL * 100")
        norm_data = {}
        for cond in CONDITIONS:
            vals = []
            for cs in CASE_STUDIES:
                raw = get_values(cs, cond, indicator)
                tl = get_values(cs, cond, "TL")
                vals.extend([r / t * 100 for r, t in zip(raw, tl)])
            norm_data[cond] = vals
            p(f"    {cond}: mean = {mean(vals):.3f}, SD = {sd(vals):.3f}")

        # Permutation test on normalized values
        obs_parts = []
        for cs in CASE_STUDIES:
            g1_vals = []
            for c in ["C", "D"]:
                raw = get_values(cs, c, indicator)
                tl = get_values(cs, c, "TL")
                g1_vals.extend([r / t * 100 for r, t in zip(raw, tl)])
            g2_vals = []
            for c in ["A", "B"]:
                raw = get_values(cs, c, indicator)
                tl = get_values(cs, c, "TL")
                g2_vals.extend([r / t * 100 for r, t in zip(raw, tl)])
            obs_parts.append(mean(g1_vals) - mean(g2_vals))
        obs_norm = mean(obs_parts)

        rng = random.Random(SEED)
        count_ge = 0
        for _ in range(N_PERM):
            perm_parts = []
            for cs in CASE_STUDIES:
                all_normed = []
                for c in CONDITIONS:
                    raw = get_values(cs, c, indicator)
                    tl = get_values(cs, c, "TL")
                    all_normed.extend([r / t * 100 for r, t in zip(raw, tl)])
                rng.shuffle(all_normed)
                n1 = 10
                perm_parts.append(mean(all_normed[:n1]) - mean(all_normed[n1:]))
            if mean(perm_parts) >= obs_norm:
                count_ge += 1

        p_norm = count_ge / N_PERM
        p(f"    Externalization test: diff = {obs_norm:.4f}, p = {p_norm:.4f}")
        p()

    # ── Per-CS consistency ──
    p("=" * 70)
    p("## Sensitivity: Per-CS Direction Consistency")
    p("=" * 70)

    for indicator in ["CR", "TP"]:
        p(f"  ### {indicator}")
        for cs in CASE_STUDIES:
            cd_m = mean([mean(get_values(cs, c, indicator)) for c in ["C", "D"]])
            ab_m = mean([mean(get_values(cs, c, indicator)) for c in ["A", "B"]])
            direction = "CD > AB" if cd_m > ab_m else "CD <= AB"
            p(f"    {cs}: CD={cd_m:.2f}, AB={ab_m:.2f} → {direction}")

    # ── Summary ──
    p()
    p("=" * 70)
    p("## Success Criteria Summary (§7.6)")
    p("=" * 70)

    ext_cr_sig = p_values_ext["CR"] < 0.025
    ext_tp_sig = p_values_ext["TP"] < 0.025
    frm_cr_sig = p_values_frm["CR"] < 0.025
    frm_tp_sig = p_values_frm["TP"] < 0.025

    p(f"  Externalization ({'{C,D}'} vs {'{A,B}'}):")
    p(f"    CR: p = {p_values_ext['CR']:.4f} {'✓' if ext_cr_sig else '✗'}")
    p(f"    TP: p = {p_values_ext['TP']:.4f} {'✓' if ext_tp_sig else '✗'}")
    p(f"  Framing (C vs D):")
    p(f"    CR: p = {p_values_frm['CR']:.4f} {'✓' if frm_cr_sig else '✗'}")
    p(f"    TP: p = {p_values_frm['TP']:.4f} {'✓' if frm_tp_sig else '✗'}")

    if ext_cr_sig and ext_tp_sig and frm_cr_sig and frm_tp_sig:
        p("  → H_main FULLY SUPPORTED")
    elif ext_cr_sig and ext_tp_sig:
        if not (frm_cr_sig or frm_tp_sig):
            p("  → PARTIAL SUPPORT (externalization only)")
            p("    Explicit requirement elicitation effective;")
            p("    academic framing adds no significant value over checklist.")
        else:
            p("  → PARTIAL SUPPORT (externalization + partial framing)")
    elif ext_cr_sig or ext_tp_sig:
        p("  → PARTIAL SUPPORT (single indicator)")
    else:
        p("  → NOT SUPPORTED")

    return "\n".join(lines)


if __name__ == "__main__":
    output = main()
    with open("paper/analysis/analysis-results.txt", "w") as f:
        f.write(output)
    print(f"\n\nResults saved to paper/analysis/analysis-results.txt")
