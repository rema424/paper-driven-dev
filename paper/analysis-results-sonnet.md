# Statistical Analysis Results — Sonnet 4.6 External Validity (N=3)

> **Date**: 2026-02-22
> **Protocol**: v1 §7 (replication)
> **Scorer**: Author (CC-assisted, Rubric v2)
> **Script**: `paper/analysis/statistical_analysis_sonnet.py`
> **Parameters**: Seed=43, Permutations=10,000, Bootstrap=10,000

---

## 1. Descriptive Statistics

### Co-primary Indicators

| Condition | CR mean (SD) | TP mean (SD) |
|-----------|-------------|-------------|
| A: Conventional | 1.17 (0.98) | 0.00 (0.00) |
| B: Paper Format | 1.17 (0.98) | 0.00 (0.00) |
| C: PDD Template | 3.17 (0.41) | 6.83 (1.17) |
| D: Checklist | 3.17 (0.41) | 5.33 (0.82) |

### Per-CS Breakdown

| CS | Cond | CR mean (SD) | TP mean (SD) |
|----|------|-------------|-------------|
| CS1 | A | 0.33 (0.58) | 0.00 (0.00) |
| CS1 | B | 0.33 (0.58) | 0.00 (0.00) |
| CS1 | C | 3.33 (0.58) | 6.67 (0.58) |
| CS1 | D | 3.00 (0.00) | 5.00 (1.00) |
| CS2 | A | 2.00 (0.00) | 0.00 (0.00) |
| CS2 | B | 2.00 (0.00) | 0.00 (0.00) |
| CS2 | C | 3.00 (0.00) | 7.00 (1.73) |
| CS2 | D | 3.33 (0.58) | 5.67 (0.58) |

---

## 2. Main Analysis A: Externalization Effect

**{C,D} vs {A,B}** — one-sided stratified permutation test, α = 0.025

| Indicator | Observed diff | p-value | Significant? |
|-----------|--------------|---------|--------------|
| CR | 2.000 | < 0.0001 | Yes *** |
| TP | 6.083 | < 0.0001 | Yes *** |

**Effect sizes (Cliff's delta, grouped)**:

| Indicator | δ | 95% CI | Interpretation |
|-----------|---|--------|----------------|
| CR | 1.000 | [1.000, 1.000] | Complete separation |
| TP | 1.000 | [1.000, 1.000] | Complete separation |

**Pairwise effect sizes**:

| Pair | CR δ [95% CI] | TP δ [95% CI] |
|------|---------------|---------------|
| C vs A | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| C vs B | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| D vs A | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| D vs B | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |

→ **Externalization effect replicated** with complete separation identical to GPT-5.2.

---

## 3. Main Analysis B: Framing Effect

**C vs D** — one-sided stratified permutation test (C > D), α = 0.025

| Indicator | Observed diff (C − D) | p-value | Significant? |
|-----------|-----------------------|---------|--------------|
| CR | 0.000 | 0.7495 | No |
| TP | 1.500 | 0.0286 | No |

→ **Framing effect not supported** (consistent with GPT-5.2 result).

---

## 4. Equivalence Test (TOST): C vs D

| Indicator | Observed diff | Δ | p_TOST | Equivalent? |
|-----------|-------------|------|--------|-------------|
| CR | 0.000 | 1.25 | 0.0020 | Yes (α = 0.05) |
| TP | 1.500 | 3.25 | 0.0096 | Yes (α = 0.05) |

→ **C ≈ D equivalence replicated** within pre-specified margins.

---

## 5. Post-hoc: B vs A (Three-Tier Hierarchy Check)

| Indicator | Observed diff (B − A) | p-value | Significant? |
|-----------|----------------------|---------|--------------|
| CR | 0.000 | 0.7932 | No |
| TP | 0.000 | 1.0000 | No |

→ **Three-tier hierarchy NOT replicated with Sonnet 4.6.** B ≈ A for both indicators. The intermediate B effect (TP ≈ 2.0 with GPT-5.2) appears to be model-specific.

---

## 6. Per-CS Direction Consistency

| CS | Indicator | {C,D} mean | {A,B} mean | Direction |
|----|-----------|-----------|-----------|-----------|
| CS1 | CR | 3.17 | 0.33 | CD > AB ✓ |
| CS1 | TP | 5.83 | 0.00 | CD > AB ✓ |
| CS2 | CR | 3.17 | 2.00 | CD > AB ✓ |
| CS2 | TP | 6.33 | 0.00 | CD > AB ✓ |

→ All 4 comparisons consistent across both case studies.

---

## 7. Cross-Model Summary

| Finding | GPT-5.2 (N=10) | Sonnet 4.6 (N=6) | Replicated? |
|---------|----------------|-------------------|-------------|
| {C,D} > {A,B} (CR) | p < 0.0001, δ=1.000 | p < 0.0001, δ=1.000 | Yes |
| {C,D} > {A,B} (TP) | p < 0.0001, δ=1.000 | p < 0.0001, δ=1.000 | Yes |
| C ≈ D (TOST CR) | p < 0.0001 | p = 0.0020 | Yes |
| C ≈ D (TOST TP) | p < 0.0001 | p = 0.0096 | Yes |
| C > D framing | n.s. | n.s. | Yes (null) |
| B > A (TP) | p < 0.0001 | n.s. (B TP = 0) | No |
| Three-tier hierarchy | A < B << {C,D} | A ≈ B << {C,D} | Partial |

→ The externalization effect and C ≈ D equivalence are model-invariant. The B intermediate effect is model-specific.
