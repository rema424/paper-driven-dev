# Statistical Analysis Results — Phase 2 (N=5)

> **Date**: 2026-02-20
> **Protocol**: v1 §7
> **Scorer**: Author (CC-assisted, Rubric v2)
> **Script**: `paper/analysis/statistical_analysis.py`
> **Parameters**: Seed=42, Permutations=10,000, Bootstrap=10,000

---

## 1. Descriptive Statistics

### Co-primary Indicators

| Condition | CR mean (SD) | TP mean (SD) |
|-----------|-------------|-------------|
| A: Conventional | 0.30 (0.48) | 0.20 (0.63) |
| B: Paper Format | 0.50 (0.53) | 2.00 (0.47) |
| C: PDD Template | 3.20 (0.42) | 5.20 (0.63) |
| D: Checklist | 3.70 (0.48) | 5.30 (0.67) |

### Per-CS Breakdown

| CS | Cond | CR mean (SD) | TP mean (SD) |
|----|------|-------------|-------------|
| CS1 | A | 0.00 (0.00) | 0.40 (0.89) |
| CS1 | B | 0.00 (0.00) | 2.00 (0.00) |
| CS1 | C | 3.00 (0.00) | 5.20 (0.84) |
| CS1 | D | 3.40 (0.55) | 5.00 (0.71) |
| CS2 | A | 0.60 (0.55) | 0.00 (0.00) |
| CS2 | B | 1.00 (0.00) | 2.00 (0.71) |
| CS2 | C | 3.40 (0.55) | 5.20 (0.45) |
| CS2 | D | 4.00 (0.00) | 5.60 (0.55) |

### All Indicators

| Condition | CR | TP | CD | EA | FI | TL |
|-----------|----|----|----|----|----|------|
| A | 0.30 | 0.20 | 1.90 | 0.70 | 0.00 | 38.9 |
| B | 0.50 | 2.00 | 2.60 | 1.00 | 0.70 | 68.5 |
| C | 3.20 | 5.20 | 3.90 | 3.30 | 0.30 | 105.3 |
| D | 3.70 | 5.30 | 3.30 | 3.70 | 0.00 | 78.1 |

---

## 2. Main Analysis A: Externalization Effect

**Comparison**: {C, D} vs {A, B} (one-sided stratified permutation test)
**α**: 0.025 per indicator (Bonferroni for 2 co-primary)

| Indicator | Observed diff | p-value | Significant? |
|-----------|-------------|---------|-------------|
| CR | 3.050 | < 0.0001 | Yes (***) |
| TP | 4.150 | < 0.0001 | Yes (***) |

**Result**: Externalization effect strongly supported. Conditions with explicit analysis step requirements ({C, D}) produce dramatically more conflicting requirements and testable properties than conditions without ({A, B}).

---

## 3. Main Analysis B: Framing Effect

**Comparison**: C vs D (one-sided stratified permutation test, C > D)
**α**: 0.025 per indicator (Bonferroni)

| Indicator | Observed diff | p-value | Significant? |
|-----------|-------------|---------|-------------|
| CR | −0.500 | 1.0000 | No |
| TP | −0.100 | 0.5756 | No |

**Result**: Framing effect not supported. C does not outperform D on either co-primary indicator. In fact, D shows slightly higher values than C on both indicators (though this difference is also not significant in the reverse direction).

---

## 4. Post-hoc Pairwise Comparisons

**α**: 0.025/4 ≈ 0.006 per pair per indicator (Bonferroni)

| Pair | CR diff | CR p | TP diff | TP p |
|------|---------|------|---------|------|
| C vs A | 2.900 | < 0.0001 (***) | 5.000 | < 0.0001 (***) |
| C vs B | 2.700 | < 0.0001 (***) | 3.200 | < 0.0001 (***) |
| D vs A | 3.400 | < 0.0001 (***) | 5.100 | < 0.0001 (***) |
| D vs B | 3.200 | < 0.0001 (***) | 3.300 | < 0.0001 (***) |

**Result**: All pairwise comparisons between {C, D} and {A, B} are highly significant, with complete separation (no overlap in distributions).

---

## 5. Effect Sizes: Cliff's Delta [95% Bootstrap CI]

### CR

| Pair | δ | 95% CI | Interpretation |
|------|------|---------|----------------|
| C vs A | 1.000 | [1.000, 1.000] | large |
| C vs B | 1.000 | [1.000, 1.000] | large |
| D vs A | 1.000 | [1.000, 1.000] | large |
| D vs B | 1.000 | [1.000, 1.000] | large |
| C vs D | −0.500 | [−0.900, −0.100] | large |
| B vs A | 0.200 | [−0.200, 0.600] | small |

### TP

| Pair | δ | 95% CI | Interpretation |
|------|------|---------|----------------|
| C vs A | 1.000 | [1.000, 1.000] | large |
| C vs B | 1.000 | [1.000, 1.000] | large |
| D vs A | 1.000 | [1.000, 1.000] | large |
| D vs B | 1.000 | [1.000, 1.000] | large |
| C vs D | −0.090 | [−0.540, 0.360] | negligible |
| B vs A | 0.900 | [0.670, 1.000] | large |

**Note on δ = 1.000 for C/D vs A/B**: This indicates perfect separation — every observation in {C, D} exceeds every observation in {A, B}. This is a ceiling effect driven by the near-zero values in A/B and consistently high values in C/D.

**Note on B vs A for TP**: δ = 0.900 (large) is unexpected. B consistently produces TP ≈ 2 while A produces TP ≈ 0. This is discussed in §8 below.

---

## 6. Equivalence Test (TOST): C vs D

**Equivalence margins**: Δ(CR) = 1.25, Δ(TP) = 3.25 (50% of Phase 1 C-condition means)
**Method**: Stratified permutation-based TOST with data shifting
**α**: 0.05

| Indicator | Observed diff | Δ | p_upper | p_lower | p_TOST | Equivalent? |
|-----------|-------------|------|---------|---------|--------|-------------|
| CR | −0.500 | 1.25 | < 0.0001 | < 0.0001 | < 0.0001 | Yes |
| TP | −0.100 | 3.25 | < 0.0001 | < 0.0001 | < 0.0001 | Yes |

**Result**: Equivalence strongly established for both co-primary indicators. The difference between C and D falls well within the pre-specified equivalence margins. Per protocol §7.4 and §9.1, this means: **D ≈ C — the structured checklist achieves equivalent co-primary indicator levels without academic paper framing.**

**Interpretation (protocol §2, H_checklist)**: This corresponds to the "D ≈ C" scenario — analysis step structuring is the active ingredient, and paper format is not essential.

---

## 7. Secondary Analysis: H_framing (B vs A)

### Existing Approaches (EA)

**Comparison**: B vs A (one-sided, B > A) | α = 0.05

| Indicator | Observed diff | p-value | Significant? |
|-----------|-------------|---------|-------------|
| EA | 0.300 | 0.2027 | No |

**Result**: H_framing not supported for exploration breadth. Paper format (B) does not produce significantly more existing approaches than conventional (A).

### Co-primary B vs A (expected n.s.)

| Indicator | Observed diff | p-value |
|-----------|-------------|---------|
| CR | 0.200 | 0.2162 (n.s.) |
| TP | 1.800 | < 0.0001 (*) |

**Unexpected finding**: B vs A for TP is significant. Paper format consistently produces ~2 testable properties while conventional produces ~0. This contradicts the protocol's prediction that B and A would both show zero co-primary indicators. See §8 for discussion.

---

## 8. Unexpected Findings and Protocol Deviations

### 8.1 B produces non-zero TP

Protocol §2 (H_framing) predicted: "B と A の co-primary 2指標は共にゼロ付近で差がない." The data contradicts this for TP:
- B produces TP = 2.00 ± 0.47 (consistently 2 per output)
- A produces TP = 0.20 ± 0.63 (mostly 0)

Examining the B outputs, the TP ≈ 2 comes from mathematical proof-like statements (e.g., "map immutability", "single-source consistency" for CS1; "old version tokens rejected", "propagation delay bound" for CS2). These are formal properties derived from B's tendency to generate proof-like sections, not from explicit prompting for testable properties.

**Implication**: Paper format does partially elicit testable properties (through mathematical formalization), but at a much lower level than C/D (TP ≈ 5.2-5.3). The gap between B and C/D remains large (Cliff's δ = 1.000, perfect separation).

### 8.2 D slightly exceeds C

On both co-primary indicators, D (checklist) slightly outperforms C (PDD template):
- CR: D = 3.70 vs C = 3.20
- TP: D = 5.30 vs C = 5.20

This is opposite to the protocol's directional hypothesis (C > D). The difference is not significant, and TOST confirms equivalence. The practical interpretation is that C and D produce indistinguishable quality.

---

## 9. Sensitivity Analyses

### 9.1 Exploratory Indicator: Constraints Disclosed (CD)

| Comparison | Observed diff | p-value |
|-----------|-------------|---------|
| {C,D} vs {A,B} | 1.350 | < 0.0001 |
| C vs D | 0.600 | 0.0525 |

CD shows the same externalization pattern as co-primary indicators. The C vs D difference (C slightly higher) is marginally non-significant at α = 0.05.

### 9.2 Line-Normalized Indicators

Normalizing by total lines (indicator/TL × 100) does not change the pattern:

| Indicator/TL | A mean | B mean | C mean | D mean | Ext. p-value |
|-------------|--------|--------|--------|--------|-------------|
| CR/TL × 100 | 0.862 | 0.656 | 3.106 | 5.083 | < 0.0001 |
| TP/TL × 100 | 0.357 | 2.989 | 5.074 | 7.296 | < 0.0001 |

**Note**: D shows higher density (more indicators per line) than C, consistent with D's shorter but equally substantive outputs.

### 9.3 Per-CS Direction Consistency

| CS | Indicator | CD mean | AB mean | Direction |
|----|-----------|---------|---------|-----------|
| CS1 | CR | 3.20 | 0.00 | CD > AB |
| CS1 | TP | 5.10 | 1.20 | CD > AB |
| CS2 | CR | 3.70 | 0.80 | CD > AB |
| CS2 | TP | 5.40 | 1.00 | CD > AB |

The externalization effect is consistent across both case studies, with the same direction and similar magnitude.

---

## 10. Success Criteria Assessment (Protocol §7.6)

| Criterion | Required | Observed | Met? |
|-----------|----------|----------|------|
| Main A: Externalization (CR) | p < 0.025 | p < 0.0001 | Yes |
| Main A: Externalization (TP) | p < 0.025 | p < 0.0001 | Yes |
| Main B: Framing (CR) | p < 0.025 | p = 1.000 | No |
| Main B: Framing (TP) | p < 0.025 | p = 0.576 | No |

**Overall**: **Partial support (externalization only).**

Explicit requirement elicitation — prompting for conflicting requirements, testable properties, existing approaches, and constraints — is highly effective regardless of whether the output is framed as an academic paper (C) or a structured checklist (D). Academic paper framing provides no additional benefit over structured checklist framing for co-primary indicators.

---

## 11. Implications for Paper Narrative

### What the data supports

1. **Structuring the analysis process matters**: {C, D} >> {A, B} on both co-primary indicators with perfect separation (δ = 1.000)
2. **Paper format is not the active ingredient**: D ≈ C (TOST p < 0.0001 for both indicators within pre-specified equivalence margins)
3. **The effect is robust**: Consistent across both case studies, robust to line normalization, with near-zero within-condition variance

### What the data does not support

1. ~~H_main (full): PDD template (C) outperforms all other conditions~~ — D matches C
2. ~~H_framing (EA): Paper format increases exploration breadth~~ — B ≈ A for EA
3. ~~Paper format has no effect on TP~~ — B produces TP ≈ 2 (unexpected)

### Revised narrative direction

The results suggest the paper should reframe from "paper-driven development" to "structured analysis elicitation." The key finding is:

> **Explicitly prompting LLMs to identify conflicting requirements, analyze existing approaches, derive testable properties, and disclose constraints dramatically improves design analysis quality — but this effect is independent of whether the output is framed as an academic paper or a structured checklist.**

This is a stronger finding than the original hypothesis in one sense (the effect is huge: δ = 1.000) but challenges the paper's core framing (the "paper" part is not essential).

### Protocol §9.1 trigger

> "D 条件で C と統計的に同等の co-primary 指標が出た場合: テンプレート効果の主張は成立しない。チェックリスト効果の研究に方向転換を検討"

This trigger is activated. The paper should pivot to emphasize:
1. The externalization/structuring effect as the primary contribution
2. The paper format as one possible (but not unique) implementation
3. The practical value: even a simple checklist achieves the same quality

---

## 12. Raw Data Reference

Full scoring data with evidence: `paper/scoring-data-v2.md`
Analysis script: `paper/analysis/statistical_analysis.py`
LLM outputs: `docs/examples/fullpaper/cs{1,2}-{conventional,paper-format,pdd-template,checklist}-run{1-5}.md`
