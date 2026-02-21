# LLM Blind Evaluation — Aggregated Scores

> **Date**: 2026-02-21
> **Evaluators**: GPT-5.2, Opus 4.6, Sonnet 4.6
> **Rubric**: Protocol v1 §5 (rubric-v2)
> **Scope**: 40 blinded outputs + 5 calibration items

---

## Calibration Round (5 items)

All 3 evaluators achieved perfect agreement on CR and TP for calibration:

| Calibration | CR (all) | TP (all) |
|-------------|----------|----------|
| Cal-001 (CS2) | 0 | 0 |
| Cal-002 (CS1) | 0 | 0 |
| Cal-003 (CS2) | 0 | 0 |
| Cal-004 (CS1) | 2 | 6 |
| Cal-005 (CS2) | 3 | 7 |

---

## Main Scoring (40 items) — CR

| Output | True | Author | GPT-5.2 | Opus | Sonnet |
|--------|------|-------:|--------:|-----:|-------:|
| 001 | B | 0 | 0 | 0 | 0 |
| 002 | A | 0 | 0 | 0 | 0 |
| 003 | C | 3 | 3 | 3 | 3 |
| 004 | D | 4 | 4 | 4 | 4 |
| 005 | B | 1 | 0 | 0 | 0 |
| 006 | A | 1 | 1 | 0 | 0 |
| 007 | C | 4 | 4 | 4 | 4 |
| 008 | C | 3 | 3 | 3 | 3 |
| 009 | A | 0 | 0 | 0 | 0 |
| 010 | C | 3 | 3 | 3 | 3 |
| 011 | A | 0 | 0 | 0 | 0 |
| 012 | B | 1 | 0 | 1 | 1 |
| 013 | A | 0 | 0 | 0 | 0 |
| 014 | D | 3 | 3 | 3 | 3 |
| 015 | C | 3 | 3 | 3 | 3 |
| 016 | C | 3 | 3 | 3 | 3 |
| 017 | D | 4 | 4 | 4 | 4 |
| 018 | B | 1 | 0 | 1 | 0 |
| 019 | C | 3 | 3 | 3 | 3 |
| 020 | A | 1 | 1 | 1 | 1 |
| 021 | A | 1 | 1 | 1 | 1 |
| 022 | C | 3 | 3 | 3 | 3 |
| 023 | D | 4 | 4 | 4 | 4 |
| 024 | B | 1 | 1 | 1 | 0 |
| 025 | D | 4 | 4 | 4 | 4 |
| 026 | D | 3 | 3 | 3 | 3 |
| 027 | D | 4 | 4 | 4 | 4 |
| 028 | C | 4 | 4 | 4 | 4 |
| 029 | A | 0 | 0 | 0 | 0 |
| 030 | A | 0 | 0 | 0 | 0 |
| 031 | D | 4 | 4 | 4 | 4 |
| 032 | B | 1 | 0 | 0 | 0 |
| 033 | B | 0 | 0 | 0 | 0 |
| 034 | B | 0 | 0 | 0 | 0 |
| 035 | B | 0 | 0 | 0 | 0 |
| 036 | C | 3 | 3 | 3 | 3 |
| 037 | D | 3 | 3 | 3 | 3 |
| 038 | D | 4 | 4 | 4 | 4 |
| 039 | A | 0 | 0 | 0 | 0 |
| 040 | B | 0 | 0 | 0 | 0 |

## Main Scoring (40 items) — TP

| Output | True | Author | GPT-5.2 | Opus | Sonnet |
|--------|------|-------:|--------:|-----:|-------:|
| 001 | B | 2 | 0 | 0 | 0 |
| 002 | A | 2 | 0 | 0 | 0 |
| 003 | C | 4 | 4 | 4 | 4 |
| 004 | D | 5 | 2 | 5 | 5 |
| 005 | B | 3 | 0 | 0 | 0 |
| 006 | A | 0 | 0 | 0 | 0 |
| 007 | C | 5 | 4 | 5 | 5 |
| 008 | C | 5 | 5 | 5 | 5 |
| 009 | A | 0 | 0 | 0 | 0 |
| 010 | C | 5 | 4 | 5 | 5 |
| 011 | A | 0 | 0 | 0 | 0 |
| 012 | B | 2 | 0 | 0 | 0 |
| 013 | A | 0 | 0 | 0 | 0 |
| 014 | D | 5 | 5 | 5 | 5 |
| 015 | C | 5 | 5 | 5 | 5 |
| 016 | C | 5 | 3 | 5 | 5 |
| 017 | D | 5 | 5 | 5 | 5 |
| 018 | B | 2 | 0 | 0 | 0 |
| 019 | C | 6 | 6 | 6 | 6 |
| 020 | A | 0 | 0 | 0 | 0 |
| 021 | A | 0 | 0 | 0 | 0 |
| 022 | C | 5 | 5 | 5 | 5 |
| 023 | D | 6 | 6 | 6 | 6 |
| 024 | B | 1 | 0 | 0 | 0 |
| 025 | D | 5 | 5 | 5 | 5 |
| 026 | D | 4 | 4 | 4 | 4 |
| 027 | D | 6 | 6 | 6 | 6 |
| 028 | C | 6 | 6 | 6 | 6 |
| 029 | A | 0 | 0 | 0 | 0 |
| 030 | A | 0 | 0 | 0 | 0 |
| 031 | D | 6 | 3 | 5 | 6 |
| 032 | B | 2 | 0 | 0 | 0 |
| 033 | B | 2 | 0 | 0 | 0 |
| 034 | B | 2 | 0 | 6 | 0 |
| 035 | B | 2 | 0 | 0 | 0 |
| 036 | C | 6 | 6 | 6 | 6 |
| 037 | D | 5 | 5 | 5 | 5 |
| 038 | D | 6 | 6 | 6 | 6 |
| 039 | A | 0 | 0 | 0 | 0 |
| 040 | B | 2 | 0 | 0 | 0 |

## Main Scoring (40 items) — CD

| Output | True | Author | GPT-5.2 | Opus | Sonnet |
|--------|------|-------:|--------:|-----:|-------:|
| 001 | B | 3 | 0 | 0 | 0 |
| 002 | A | 3 | 1 | 0 | 0 |
| 003 | C | 5 | 4 | 3 | 3 |
| 004 | D | 3 | 2 | 2 | 2 |
| 005 | B | 2 | 2 | 2 | 2 |
| 006 | A | 1 | 0 | 0 | 0 |
| 007 | C | 5 | 4 | 3 | 3 |
| 008 | C | 3 | 2 | 2 | 2 |
| 009 | A | 3 | 2 | 2 | 2 |
| 010 | C | 4 | 3 | 2 | 2 |
| 011 | A | 0 | 1 | 0 | 0 |
| 012 | B | 1 | 0 | 1 | 0 |
| 013 | A | 2 | 2 | 0 | 0 |
| 014 | D | 3 | 3 | 3 | 3 |
| 015 | C | 4 | 3 | 3 | 2 |
| 016 | C | 4 | 3 | 3 | 3 |
| 017 | D | 4 | 3 | 3 | 3 |
| 018 | B | 1 | 1 | 1 | 1 |
| 019 | C | 3 | 3 | 3 | 3 |
| 020 | A | 0 | 0 | 0 | 0 |
| 021 | A | 0 | 1 | 0 | 0 |
| 022 | C | 3 | 2 | 2 | 2 |
| 023 | D | 3 | 3 | 3 | 3 |
| 024 | B | 2 | 1 | 1 | 1 |
| 025 | D | 4 | 3 | 2 | 2 |
| 026 | D | 3 | 3 | 3 | 2 |
| 027 | D | 3 | 2 | 2 | 2 |
| 028 | C | 4 | 4 | 1 | 1 |
| 029 | A | 3 | 0 | 0 | 0 |
| 030 | A | 3 | 2 | 0 | 0 |
| 031 | D | 3 | 3 | 3 | 3 |
| 032 | B | 2 | 1 | 1 | 1 |
| 033 | B | 4 | 1 | 0 | 1 |
| 034 | B | 4 | 4 | 3 | 3 |
| 035 | B | 4 | 0 | 0 | 0 |
| 036 | C | 4 | 3 | 3 | 3 |
| 037 | D | 4 | 4 | 2 | 3 |
| 038 | D | 3 | 3 | 2 | 3 |
| 039 | A | 4 | 0 | 0 | 2 |
| 040 | B | 3 | 3 | 1 | 3 |

---

## ICC(2,1) Results

### All 4 Raters (Author + 3 LLM)

| Indicator | ICC(2,1) | Interpretation | Pass (≥0.60) |
|-----------|----------|----------------|:------------:|
| CR | 0.985 | Excellent | Yes |
| TP | 0.908 | Excellent | Yes |
| CD | 0.560 | Fair | No |

### 3 LLM Raters Only

| Indicator | ICC(2,1) |
|-----------|----------|
| CR | 0.989 |
| TP | 0.931 |
| CD | 0.790 |

### Key Finding for CD Divergence

The Author consistently scored CD higher than all 3 LLM evaluators (mean absolute difference: GPT-5.2 = 0.98, Opus = 1.38, Sonnet = 1.28). The LLM-only ICC for CD was 0.79 (good), indicating the divergence is primarily between Author and LLMs rather than among LLMs. This suggests the Author applied a broader interpretation of "constraints disclosed" — counting implementation recommendations and boundary conditions that LLMs classified as design choices rather than failure/degradation conditions.

---

## Condition Estimation

| Evaluator | Accuracy | Errors |
|-----------|----------|--------|
| GPT-5.2 | 97.5% (39/40) | 1 |
| Opus 4.6 | 90.0% (36/40) | 4 |
| Sonnet 4.6 | 82.5% (33/40) | 7 |
| Inter-LLM Agreement | 80.0% (32/40) | — |

### GPT-5.2 Confusion Matrix

| True\Guess | A | B | C | D |
|------------|--:|--:|--:|--:|
| A | 9 | 0 | 0 | 1 |
| B | 0 | 10| 0 | 0 |
| C | 0 | 0 | 10| 0 |
| D | 0 | 0 | 0 | 10|

### Opus 4.6 Confusion Matrix

| True\Guess | A | B | C | D |
|------------|--:|--:|--:|--:|
| A | 9 | 0 | 0 | 1 |
| B | 0 | 8 | 2 | 0 |
| C | 0 | 0 | 10| 0 |
| D | 0 | 0 | 1 | 9 |

### Sonnet 4.6 Confusion Matrix

| True\Guess | A | B | C | D |
|------------|--:|--:|--:|--:|
| A | 8 | 0 | 0 | 2 |
| B | 0 | 10| 0 | 0 |
| C | 0 | 0 | 10| 0 |
| D | 3 | 0 | 2 | 5 |

### Interpretation

High condition estimation accuracy (82.5–97.5%) indicates the experimental conditions produce structurally distinct outputs, which is the expected consequence of different prompting strategies. The blinding prevents evaluators from knowing the hypothesis or which conditions are hypothesized to produce higher counts, preserving evaluation independence. All evaluators correctly identified Condition C (PDD template) with 100% accuracy, while errors concentrated on A↔D and B↔C confusions.
