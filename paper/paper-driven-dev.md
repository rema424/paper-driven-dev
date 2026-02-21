# Structured Analysis Requirements Drive LLM Design Quality Beyond Paper Framing: A Four-Condition Controlled Experiment

> **実験条件**: Model: GPT-5.2 (via Codex) | 4 conditions (A/B/C/D) × 2 CS × 5 runs = 40 executions | Date: 2026-02 | Evaluator: 著者（第三者盲検進行中）

## Abstract

We investigate whether structured analysis requirements — explicitly prompting LLMs to identify conflicting requirements, analyze existing approaches, derive testable properties, and disclose constraints — improve software design analysis quality, and whether academic paper framing provides additional benefit beyond structuring alone. In a four-condition controlled experiment with GPT-5.2 (N=10 per condition, two software design problems, 40 total executions), replicated with Claude Sonnet 4.6 (N=6 per condition, 24 executions), we compared: (A) conventional prompting, (B) paper-format instruction without template, (C) a paper-format template (Paper-Driven Development), and (D) a structurally isomorphic checklist without paper framing. Conditions with structured requirements ({C, D}) achieved complete separation from those without ({A, B}) on both co-primary indicators — conflicting requirements identified (CR) and testable properties derived (TP) — with Cliff's δ = 1.000 for all pairwise comparisons across both models (p < 0.0001). Crucially, the paper template (C) and checklist (D) produced statistically equivalent results (TOST p < 0.0001 for both indicators), triggering a pre-registered pivot criterion: the active ingredient is the structuring of analysis steps, not the academic paper format. Paper-format framing alone (B) contributed a model-specific secondary effect on TP (≈2.0 vs A's ≈0.2 in GPT-5.2, absent in Sonnet) through mathematical formalization, but this was dwarfed by structured requirements (C/D: TP ≈5.2–6.8). We term the mechanism structured elicitation through information externalization and provide both implementations — paper template and checklist — as open-source tools.

## 1. Introduction

Large Language Models (LLMs) have become integral to software development workflows, assisting with code generation, debugging, and design analysis. However, the quality of LLM output varies significantly depending on how problems are presented. The emerging field of prompt engineering has demonstrated that structured prompts can substantially improve reasoning quality [1, 2], but the mechanisms underlying these improvements — and which aspects of prompt structure matter most — remain poorly understood.

This study originated from an observation we called **Paper-Driven Development (PDD)**: instructing an LLM to "write a paper" about a software design problem, guided by a seven-section academic paper template (template §1–§7), appeared to produce more thorough design analysis than conventional prompting. An exploratory Phase 1 study (N=2; Appendix C) confirmed that two verification-relevant indicators — conflicting requirements identified and testable properties derived — appeared only under the PDD template condition, remaining at zero under both conventional prompting and paper-format-only instruction. However, this Phase 1 design could not distinguish two confounded factors within the PDD template: (1) the explicit analysis step requirements (e.g., "identify conflicting requirements," "derive testable properties") and (2) the academic paper framing.

To separate these factors, we designed a fourth condition — a structured checklist (D) that requests the same analysis steps as the PDD template but without academic paper framing. If D achieves equivalent results to C (PDD template), the active ingredient is the structuring of analysis steps, not the paper format. We pre-registered this equivalence test as a pivot criterion (protocol §9.1): if D ≈ C, the paper's thesis pivots from "PDD template superiority" to "structured analysis requirements as the active ingredient."

The Phase 2 experiment (4 conditions × 2 case studies × 5 runs = 40 executions with GPT-5.2, replicated with Claude Sonnet 4.6 at N=3) produced three main findings: (1) conditions with structured analysis requirements ({C, D}) dramatically outperform those without ({A, B}), with complete separation on both co-primary indicators (Cliff's δ = 1.000), replicated across both model families; (2) the PDD template (C) and the structured checklist (D) produce statistically equivalent results (TOST p < 0.0001), triggering the pre-registered pivot; and (3) paper-format framing alone (B) contributes a model-specific secondary effect on testable properties through mathematical formalization (observed in GPT-5.2 but not Sonnet 4.6), dwarfed by structured requirements in both models.

We interpret the mechanism as **structured elicitation through information externalization**: LLMs possess the analytical capabilities to identify trade-offs and derive verification conditions, but do not reliably exercise them without explicit prompting. Structured requirements — whether formatted as a paper template or a checklist — convert this sporadic capability into consistent output.

This paper contributes:

- Experimental evidence that structured analysis requirements produce complete separation (δ = 1.000) in verification-relevant indicators (conflicting requirements, testable properties) compared to unstructured prompting, replicated across two model families (GPT-5.2, Claude Sonnet 4.6)
- An equivalence demonstration (TOST) showing that academic paper framing provides no additional benefit over a structured checklist for co-primary indicators
- A three-tier hierarchy of prompting effects (A < B << {C, D}) clarifying the limited role of paper-format framing, with the caveat that the intermediate B effect is model-specific
- A pre-registered four-condition experimental protocol with an explicit pivot criterion (protocol §9.1), which was activated by the data
- Two equivalent open-source implementations (PDD template and structured checklist) as Claude Code plugins

## 2. Background

### 2.1 LLM-Assisted Software Development

Recent tools and methodologies leverage LLMs for software design:

- **Spec-Driven Development** [3, 4]: Emerged in 2025 with AWS Kiro and GitHub Spec Kit. Focuses on translating natural language requirements into structured specifications (requirements.md → design.md → tasks.md). Addresses "what to build" but not "why to build it that way."
- **Amazon Narratives** [5]: Six-page memo format that forces structured prose over slides. Demonstrates that writing format affects thinking quality. Focuses on customer-facing narratives rather than technical analysis.
- **RFC/ADR** [6]: Architecture Decision Records capture context → decision → consequences. Record design rationale but do not structurally enforce exhaustive alternatives analysis.
- **Design Docs** [7]: Standard practice at Google, Uber, and Meta. Include "Alternatives Considered" sections, but their depth depends on the author rather than being structurally enforced.
- **Checklists in Professional Practice** [9]: Gawande demonstrated that checklists reduce omission errors in surgery and aviation not by teaching new skills but by making required steps explicit. This principle — that structured enumeration of steps prevents omission of known-but-skippable actions — provides theoretical grounding for the structured analysis requirements tested in this study.

### 2.2 Structured Output and Reasoning

Research on LLM reasoning suggests that output structure affects quality:

- **Chain-of-Thought (CoT)** [1]: Instructing models to reason step-by-step improves accuracy on complex tasks.
- **Persona Prompting** [8]: Assigning roles (e.g., "as a security researcher") affects output quality and focus.
- **Format Constraints** [2]: The "Let Me Speak Freely?" study found that strict format constraints can degrade reasoning, while moderate structure can improve it. This suggests an optimal level of structural guidance.

### 2.3 Gap in Existing Approaches

No existing methodology structurally enforces the combination of exhaustive alternatives survey, critical evaluation with limitations, and derivation of testable properties in LLM-assisted design analysis. Spec-driven development addresses requirements clarity but not design rationale. RFC/ADR records decisions but does not enforce analysis depth. CoT improves reasoning but does not structure the output for design review. Checklists enforce step completion but have not been systematically applied to LLM prompting for software design analysis. This study investigates whether structured analysis requirements — explicitly prompting an LLM to perform specific analytical steps — can fill this gap, and whether the format of those requirements (academic paper template vs. structured checklist) matters.

## 3. Methods

### 3.1 Experimental Design

We conducted a four-condition controlled experiment to investigate whether structured analysis requirements improve LLM design analysis quality, and whether academic paper framing provides additional benefit beyond structuring alone. The experiment extends an exploratory Phase 1 study (N=2, three conditions A/B/C; see Appendix C) that generated the hypotheses tested here.

**Design.** Four prompting conditions (§3.2) × two case studies (§3.3) × five independent runs = 40 LLM executions. All conditions shared identical problem descriptions; only the instruction prefix differed.

**Hypotheses.**

- **H_main (externalization effect)**: Conditions with explicit analysis step requirements ({C, D}) produce higher co-primary indicator counts than conditions without ({A, B}).
- **H_framing (framing effect)**: The PDD template condition (C), framed as an academic paper, produces higher co-primary indicator counts than the structurally isomorphic checklist condition (D).
- **H_checklist (equivalence)**: If C does not significantly exceed D, we test whether C and D are statistically equivalent within pre-specified margins (TOST; §3.6).

**Rationale for condition D.** Phase 1 identified two confounded factors in the PDD template condition (C): (1) explicit analysis step requirements and (2) academic paper framing. Condition D—a structured checklist requesting the same analysis steps without paper framing—was designed to separate these factors. If D ≈ C, the active ingredient is the structuring of analysis steps, not the paper format. This separation follows the pre-registered pivot criterion (protocol §9.1).

### 3.2 Conditions

Four conditions were compared. All shared identical problem descriptions (§3.3); only the instruction prefix differed.

| Condition | Label | Instruction framing |
|-----------|-------|-------------------|
| A | Conventional | Design analysis prompt (no structural requirements) |
| B | Paper-format | "Write in academic paper format" (no template) |
| C | PDD Template | Paper-format instruction + template §1–§7 guidelines |
| D | Structured Checklist | Checklist instruction + equivalent analysis items (no paper framing) |

**Condition A (Conventional).** "以下の技術的な問題について、設計分析と解決策を提案してください。" (Please propose a design analysis and solution for this problem.)

**Condition B (Paper-format).** "以下の技術的な問題について、学術論文の形式で書いてください。" (Please write about this problem in academic paper format.) This corresponds to Phase 1's B1 condition.

**Condition C (PDD Template).** Condition B's instruction plus explicit seven-section template guidelines (template §1–§7) specifying: problem definition with conflicting requirements (template §1.2), current architecture (template §2), existing approaches with limitations (template §3), problem essence (template §4), proposed method (template §5), testable properties in Given/When/Then format (template §6), and constraints (template §7). The full template is reproduced in Appendix A.1. Key design decisions: template §1.2 requires ≥2 conflicting requirements (forcing identification of genuine trade-offs); template §3 requires explicit limitations per approach (preventing the common failure of listing only advantages); template §6 requires Given/When/Then testable properties (bridging design analysis and TDD); template §7 requires honest constraint disclosure (counteracting LLMs' tendency to present proposals as universally applicable).

**Condition D (Structured Checklist).** "以下の技術的な問題について、以下の分析項目に従って順番に分析してください。" (Please analyze the following problem by following these analysis items in order.) D requests the same nine analysis steps as C—including ≥2 conflicting requirements (item 2) and Given/When/Then testable conditions (item 8)—using numbered list notation (1–9) instead of paper section notation (template §1–§7). The structural granularity (sub-items, approach-level method/advantages/limitations) is isomorphic to C; only the framing differs (technical analysis vs. academic paper). Full prompt in Appendix A.1.

**Demand characteristics.** Both C and D explicitly request the co-primary indicators (conflicting requirements, testable properties). This is intentional: the research question is not whether LLMs spontaneously produce these analyses, but (1) whether explicit requirements elicit information that is otherwise omitted (A/B vs. C/D), and (2) whether academic paper framing provides additional value over checklist framing when the same analysis steps are required (C vs. D). Conditions A and B, which do not request these items, serve as the baseline for spontaneous occurrence.

### 3.3 Case Studies

**CS1: Real-Time Citation Rendering in RAG Streaming.** Citations must be displayed as sequential numbers ([1], [2], [3]) without gaps during LLM streaming output, but renumbering requires knowing all citations—which is impossible when the full text has not yet been generated.

**CS2: Multi-Tenant SaaS Session Management.** A session management system must simultaneously support multi-device login, administrator-initiated immediate session revocation, horizontal scaling, and low latency—requirements that create tension between stateless and stateful architectures.

Both problems are identical to those used in the Phase 1 exploratory study. Problem descriptions were presented in Japanese; see Appendix A.1 for the full prompt text.

### 3.4 Execution Protocol

**Model.** GPT-5.2, accessed via Codex CLI (OpenAI). This is the same model and access method used in Phase 1.

**Parameters.** Temperature was left at the Codex CLI default (not explicitly set). No system prompt was used. Maximum output tokens were unrestricted.

**Independence.** Each of the 40 runs was executed in a fresh Codex thread with no prior conversation history. No run had access to any other run's output.

**Randomization.** The 40 runs (4 conditions × 2 case studies × 5 repetitions) were executed in a randomized order (seed = 42) to prevent order effects. Runs were distributed across sessions to avoid concentrating any single condition within a session.

**Exclusion criteria.** Runs were excluded and replaced if: the API returned an error, the output was visibly truncated (sentence mid-break), context compression occurred within the thread, or an incorrect prompt was used. Excluded runs were preserved with reasons in `docs/examples/fullpaper/excluded/`. No runs required exclusion during the actual experiment.

**Replication study (Sonnet 4.6).** To assess external validity across model families, the same four-condition experiment was replicated with Claude Sonnet 4.6 (Anthropic), accessed via Claude Code CLI. N=3 runs per condition per case study (24 total) were executed in a randomized order (seed = 43, distinct from the main experiment). All other parameters — prompts, case studies, independence constraints, exclusion criteria — were identical to the main experiment. The reduced N (3 vs 5) was justified by the large effect sizes observed in the main experiment (Cliff's δ = 1.000, complete separation).

### 3.5 Evaluation Framework

We assessed LLM outputs using a six-indicator rubric (Rubric v2), refined from Phase 1 based on self-blinded rescoring disagreements (Appendix B).

**Co-primary indicators** (two; Bonferroni-corrected α = 0.025 each):

- **Conflicting requirements identified (CR)**: Count of explicitly stated pairs of opposing requirements or trade-offs. Implicit tensions (e.g., "balancing X and Y" without formal definition) score zero. Counting unit: undirected unique pair.
- **Testable properties derived (TP)**: Count of concrete conditions derived from the proposed solution that could be translated to test cases. Each property must specify three elements: precondition (Given), operation (When), and observable expected outcome (Then). **Critical distinction**: Input requirements defining the problem (e.g., R1–R4 notation) are not counted; only properties derived from the proposed approach (verifying how the solution behaves) are counted. This distinction, identified through Phase 1 rescoring disagreements, is the principal refinement in Rubric v2.

**Exploratory indicator** (one; reported but not used for primary claims):

- **Constraints disclosed (CD)**: Explicit limitations, boundary conditions, or failure modes of the proposed approach. Reclassified from co-primary after Phase 1 rescoring revealed 30% inter-rater agreement due to definition boundary ambiguity.

**Secondary indicators** (three):

- **Existing approaches analyzed (EA)**: Distinct alternatives enumerated and evaluated (name-only mentions excluded)
- **Formal invariants/proofs (FI)**: Mathematically or logically formalized properties
- **Total output length (TL)**: Line count excluding metadata headers

**Per-line normalization.** To control for the output length confound identified in Phase 1, we compute normalized values (indicator / TL × 100) as a sensitivity analysis for each co-primary and exploratory indicator.

Detailed counting rules, boundary case examples, and decision flowcharts are provided in Appendix A.2 (Rubric v2 full specification).

### 3.6 Statistical Analysis Plan

All analyses were pre-registered in the experiment protocol (protocol v1, tag `v1-protocol`) before data collection.

**Main Analysis A (externalization effect).** Stratified permutation test comparing {C, D} vs. {A, B} on each co-primary indicator, stratified by case study. One-sided ({C,D} > {A,B}). 10,000 permutations (seed = 42). Significance: α = 0.025 per indicator (Bonferroni correction for two co-primary indicators).

**Main Analysis B (framing effect).** Stratified permutation test comparing C vs. D on each co-primary indicator, stratified by case study. One-sided (C > D). Same permutation and significance parameters as Analysis A.

**Effect sizes.** Cliff's delta (δ) with 95% bootstrap confidence intervals (10,000 resamples) for all pairwise comparisons.

**Equivalence test (TOST).** If Main Analysis B is non-significant, a stratified permutation-based Two One-Sided Tests (TOST) is conducted to test whether C and D are equivalent within pre-specified margins: Δ(CR) = 1.25 and Δ(TP) = 3.25 (50% of Phase 1 C-condition means). α = 0.05.

**Post-hoc pairwise comparisons.** If Main Analysis A is significant, pairwise comparisons (C vs. A, C vs. B, D vs. A, D vs. B) are conducted with Bonferroni correction (α = 0.025/4 ≈ 0.006 per pair per indicator).

**Sensitivity analyses.** (1) Per-line normalized indicators; (2) per-case-study direction consistency; (3) exploratory indicator (CD) with the same test battery; (4) Poisson regression (`count ~ condition + case_study`) with bootstrap confidence intervals.

**Pre-registered pivot criterion (protocol §9.1).** If D achieves statistically equivalent co-primary indicators to C, the paper's thesis pivots from "PDD template superiority" to "structured analysis requirements as the active ingredient." This criterion was activated by the data (§4).

### 3.7 Third-Party Blinded Evaluation

To address the author-evaluation limitation identified in Phase 1, a single-blind third-party evaluation is conducted.

**Blinding procedure.** All 40 outputs are stripped of condition labels, file names, and metadata headers. Outputs are presented to evaluators in a randomized order (seed = 142, distinct from the execution seed). Evaluators receive only the rubric (§3.5) and scoring instructions.

**Calibration round.** Before scoring the 40 experimental outputs, evaluators independently score 5 calibration items drawn from Phase 1 outputs (selected for condition diversity). Disagreements are discussed and the rubric interpretation is aligned. If rubric adjustments are needed, reasons are recorded. The calibration rubric becomes the final scoring instrument.

**Scoring.** Each evaluator independently scores all 40 outputs on the two co-primary indicators (CR, TP) and the exploratory indicator (CD). For each count, the evaluator records the evidence (quoted passage and line reference). Evaluators also record their estimate of which condition produced each output, enabling analysis of blinding effectiveness.

**Reliability assessment.** Inter-rater reliability is assessed via ICC (two-way random, absolute agreement) on raw count values. Pass criterion: ICC ≥ 0.60 (moderate agreement). If not met, the rubric is recalibrated and scoring repeated (maximum two rounds). Indicators failing ICC ≥ 0.60 after two rounds are reclassified as exploratory.

**Blinding limitations.** This is single-blind: condition labels are removed, but output format features (§-structured sections in C, numbered checklist in D, academic conventions in B) may allow condition inference. Evaluator condition estimation accuracy is reported and its potential impact on scoring bias is discussed.

## 4. Results

### 4.1 Descriptive Statistics

Table 1 summarizes the co-primary indicators across the four conditions (N=10 per condition: 2 case studies × 5 runs).

**Table 1. Co-primary indicators by condition (mean ± SD)**

| Condition | CR mean (SD) | TP mean (SD) |
|-----------|-------------|-------------|
| A: Conventional | 0.30 (0.48) | 0.20 (0.63) |
| B: Paper Format | 0.50 (0.53) | 2.00 (0.47) |
| C: PDD Template | 3.20 (0.42) | 5.20 (0.63) |
| D: Checklist | 3.70 (0.48) | 5.30 (0.67) |

Conditions with explicit analysis step requirements ({C, D}) produced dramatically higher co-primary indicator values than conditions without ({A, B}). Within each group, within-condition variance was low (SD ≤ 0.67), indicating highly consistent output across runs.

Table 2 presents all six indicators including the exploratory and secondary measures.

**Table 2. All indicators by condition (mean)**

| Condition | CR | TP | CD | EA | FI | TL |
|-----------|----|----|----|----|----|------|
| A: Conventional | 0.30 | 0.20 | 1.90 | 0.70 | 0.00 | 38.9 |
| B: Paper Format | 0.50 | 2.00 | 2.60 | 1.00 | 0.70 | 68.5 |
| C: PDD Template | 3.20 | 5.20 | 3.90 | 3.30 | 0.30 | 105.3 |
| D: Checklist | 3.70 | 5.30 | 3.30 | 3.70 | 0.00 | 78.1 |

The per-case-study breakdown (Table 3) confirms that the externalization effect is consistent across both problem domains.

**Table 3. Co-primary indicators by condition and case study (mean ± SD)**

| CS | Condition | CR mean (SD) | TP mean (SD) |
|----|-----------|-------------|-------------|
| CS1 | A | 0.00 (0.00) | 0.40 (0.89) |
| CS1 | B | 0.00 (0.00) | 2.00 (0.00) |
| CS1 | C | 3.00 (0.00) | 5.20 (0.84) |
| CS1 | D | 3.40 (0.55) | 5.00 (0.71) |
| CS2 | A | 0.60 (0.55) | 0.00 (0.00) |
| CS2 | B | 1.00 (0.00) | 2.00 (0.71) |
| CS2 | C | 3.40 (0.55) | 5.20 (0.45) |
| CS2 | D | 4.00 (0.00) | 5.60 (0.55) |

In both CS1 and CS2, {C, D} values consistently exceed {A, B} values with no overlap in the distributions.

### 4.2 Externalization Effect

**Main Analysis A** tested whether conditions with explicit analysis step requirements ({C, D}) produce higher co-primary indicator counts than conditions without ({A, B}), using a one-sided stratified permutation test (stratified by case study, 10,000 permutations, seed = 42).

| Indicator | Observed diff ({C,D} − {A,B}) | p-value | Significant? |
|-----------|-------------------------------|---------|--------------|
| CR | 3.050 | < 0.0001 | Yes (α = 0.025) |
| TP | 4.150 | < 0.0001 | Yes (α = 0.025) |

The externalization effect is strongly supported: conditions with explicit analysis step requirements produce dramatically more conflicting requirements and testable properties than conditions without.

**Effect sizes.** Cliff's delta for all pairwise comparisons between {C, D} and {A, B} conditions:

| Pair | CR δ [95% CI] | TP δ [95% CI] |
|------|---------------|---------------|
| C vs A | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| C vs B | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| D vs A | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| D vs B | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |

All four pairwise comparisons yield δ = 1.000 with degenerate confidence intervals, indicating **complete separation**: every observation in {C, D} exceeds every observation in {A, B} on both co-primary indicators. Post-hoc pairwise permutation tests confirm all four pairs are significant (p < 0.0001 for each, Bonferroni-corrected α = 0.006).

### 4.3 Framing Effect and Equivalence

**Main Analysis B** tested whether the PDD template condition (C), framed as an academic paper, produces higher co-primary indicator counts than the structurally isomorphic checklist condition (D), using a one-sided stratified permutation test (C > D).

| Indicator | Observed diff (C − D) | p-value | Significant? |
|-----------|----------------------|---------|--------------|
| CR | −0.500 | 1.0000 | No (α = 0.025) |
| TP | −0.100 | 0.5756 | No (α = 0.025) |

The framing effect is not supported: C does not outperform D on either co-primary indicator. D shows slightly higher values than C on both indicators (CR: 3.70 vs. 3.20; TP: 5.30 vs. 5.20), though neither difference is significant.

**Equivalence test (TOST).** Because Main Analysis B was non-significant, a stratified permutation-based Two One-Sided Tests (TOST) was conducted with pre-specified equivalence margins: Δ(CR) = 1.25 and Δ(TP) = 3.25 (50% of Phase 1 C-condition means).

| Indicator | Observed diff | Δ | p_TOST | Equivalent? |
|-----------|-------------|------|--------|-------------|
| CR | −0.500 | 1.25 | < 0.0001 | Yes (α = 0.05) |
| TP | −0.100 | 3.25 | < 0.0001 | Yes (α = 0.05) |

Equivalence is supported: the difference between C and D falls within the pre-specified margins. Per the pre-registered pivot criterion (protocol §9.1), this activates the thesis pivot: the active ingredient in the PDD template is the structuring of analysis steps, not the academic paper framing. D—a structured checklist requesting the same analysis steps without paper framing—achieves statistically equivalent co-primary indicator levels.

### 4.4 Post-hoc Finding: Paper Format and Testable Properties

An unexpected finding emerged from the B vs. A comparison. The protocol predicted that both B and A — lacking explicit analysis step requirements — would show near-zero co-primary indicators. This prediction held for CR (B: 0.50 vs. A: 0.30, p = 0.216, n.s.) but not for TP:

| Indicator | B mean (SD) | A mean (SD) | Observed diff | p-value | Cliff's δ [95% CI] |
|-----------|-------------|-------------|--------------|---------|---------------------|
| TP | 2.00 (0.47) | 0.20 (0.63) | 1.80 | < 0.0001 | 0.900 [0.670, 1.000] |

Paper-format framing (B) consistently produces approximately 2 testable properties per output, while conventional prompting (A) produces near-zero. Examining the B outputs, these TP ≈ 2 arise from mathematical proof-like statements (e.g., "map immutability," "single-source consistency" for CS1; "old version tokens rejected," "propagation delay bound" for CS2)—formal properties derived from B's tendency to generate proof-like sections, not from explicit prompting for testable properties.

This finding establishes a three-tier hierarchy: A (TP ≈ 0.2) < B (TP ≈ 2.0) << {C, D} (TP ≈ 5.2–5.3). Paper-format framing partially elicits testable properties through mathematical formalization, but at a much lower level than explicit requirements. Critically, the gap between B and {C, D} remains a complete separation (Cliff's δ = 1.000).

This result is reported as a **post-hoc exploratory finding** (protocol deviation #2), not as a pre-registered hypothesis test. It is consistent with, but does not causally establish, a partial framing effect on testable property generation.

### 4.5 Sensitivity Analyses

Three sensitivity analyses were conducted to assess the robustness of the main findings.

**Line-normalized indicators.** Per-line normalization (indicator / TL × 100) does not change the externalization pattern:

| Indicator/TL × 100 | A | B | C | D | {C,D} vs {A,B} p |
|---------------------|-------|-------|-------|-------|-------------------|
| CR | 0.862 | 0.656 | 3.106 | 5.083 | < 0.0001 |
| TP | 0.357 | 2.989 | 5.074 | 7.296 | < 0.0001 |

D shows higher density (more indicators per line) than C, consistent with D's shorter but equally substantive outputs (TL: D = 78.1 vs. C = 105.3).

**Per-case-study direction consistency.** Both case studies show the same direction for the externalization effect (Table 3), with similar magnitude. The effect is not driven by a single problem domain.

**Exploratory indicator: constraints disclosed (CD).** CD shows the same externalization pattern as the co-primary indicators ({C, D} vs. {A, B}: observed diff = 1.350, p < 0.0001). The C vs. D comparison for CD shows C slightly higher (3.90 vs. 3.30), with a marginally non-significant difference (p = 0.0525 at α = 0.05). CD is reported as exploratory (see §3.5); this marginal result does not affect the primary conclusions.

### 4.6 Third-Party Blinded Evaluation

**Preliminary LLM evaluation.** As a preliminary step before human third-party evaluation, three LLM models (GPT-5.2, Opus 4.6, Sonnet 4.6) independently scored all 40 blinded outputs following the protocol described in §3.7. Each evaluator received only the rubric (§3.5), scoring instructions, and blinded outputs — with no access to condition labels, the paper, hypotheses, or other evaluators' scores. A five-item calibration round preceded the main scoring; all three evaluators achieved perfect agreement on CR and TP counts for all calibration items.

**Inter-rater reliability (ICC).** Table 6 reports ICC(2,1) (two-way random, absolute agreement, single measures) across the four raters (author + three LLMs).

*Table 6. Inter-rater reliability: ICC(2,1) across 4 raters (40 targets).*

| Indicator | ICC(2,1) | Interpretation | Pass (≥ 0.60) |
|-----------|----------|----------------|:--------------:|
| CR | 0.985 | Excellent | Yes |
| TP | 0.908 | Excellent | Yes |
| CD | 0.560 | Fair | No |

The co-primary indicators (CR, TP) exceed the pre-registered pass criterion of ICC ≥ 0.60, with excellent agreement. The exploratory indicator CD falls below the threshold (ICC = 0.560). Pairwise analysis reveals the source: the LLM-only ICC for CD is 0.790 (good agreement among themselves), but the author scored CD systematically higher than all three LLMs (mean absolute difference: 0.98–1.38 per output). This suggests a broader author interpretation of "constraints disclosed" — counting implementation recommendations that LLMs classified as design choices rather than failure conditions. The author-LLM divergence on CD is consistent with the Phase 1 self-blinded rescoring observation (§5.6), where CD showed 30% inter-rater agreement.

**Condition estimation accuracy.** Table 7 reports how accurately each LLM evaluator identified the experimental condition from the blinded output alone.

*Table 7. Condition estimation accuracy (3 LLM evaluators, 40 items).*

| Evaluator | Accuracy |
|-----------|----------|
| GPT-5.2 | 97.5% (39/40) |
| Opus 4.6 | 90.0% (36/40) |
| Sonnet 4.6 | 82.5% (33/40) |

All evaluators identified condition C (PDD template) with 100% accuracy; errors concentrated on A↔D and B↔C confusions. High condition estimation accuracy (82.5–97.5%) confirms that the experimental conditions produce structurally distinct outputs — an expected consequence of different prompting strategies (§3.7, blinding limitations). The blinding prevents evaluators from knowing which conditions are hypothesized to score higher, preserving evaluation independence. However, the ability to infer conditions means that evaluator expectations could potentially influence scoring; the excellent CR and TP agreement across raters (including the author, who knows the true conditions) suggests that any such bias is minimal for the co-primary indicators.

**Limitations of LLM evaluation.** This preliminary evaluation uses LLM models as evaluators, which introduces the possibility of correlated biases with the LLM-generated outputs being scored (protocol deviation #3). Human third-party evaluation remains pending and is required to fully address the author-evaluation limitation. The current LLM evaluation provides preliminary evidence that the author's CR and TP scoring is reproducible, but does not substitute for independent human evaluation.

### 4.7 External Validity: Sonnet 4.6 Replication

To assess whether the externalization effect generalizes across model families, the four-condition experiment was replicated with Claude Sonnet 4.6 (N=3 per condition per case study, 24 total; §3.4).

**Externalization effect.** Table 8 shows the replication results alongside the main GPT-5.2 findings.

*Table 8. Cross-model replication of the externalization effect.*

| Finding | GPT-5.2 (N=10) | Sonnet 4.6 (N=6) |
|---------|----------------|-------------------|
| {C,D} vs {A,B} CR | p < 0.0001, δ = 1.000 | p < 0.0001, δ = 1.000 |
| {C,D} vs {A,B} TP | p < 0.0001, δ = 1.000 | p < 0.0001, δ = 1.000 |
| C ≈ D (TOST CR) | p < 0.0001 | p = 0.002 |
| C ≈ D (TOST TP) | p < 0.0001 | p = 0.010 |

The externalization effect replicates with identical effect sizes: Cliff's δ = 1.000 for all {C, D} vs {A, B} comparisons, with complete separation on both co-primary indicators. The C ≈ D equivalence also replicates within pre-specified TOST margins.

**TP complete separation.** For TP, the Sonnet replication shows even starker separation than GPT-5.2: all {A, B} runs produced TP = 0 (GPT-5.2 A produced occasional non-zero TP), while all {C, D} runs produced TP ≥ 4.

**Model-specific differences.** Two notable differences emerged between models:

1. *Sonnet produces higher baseline CR in A/B conditions.* Sonnet A/B CR means (1.17) exceed GPT-5.2 A/B means (0.30/0.50), driven primarily by CS2 where Sonnet consistently identified 2 conflicting requirements even without explicit prompting. Despite this higher baseline, the gap between {C, D} (CR ≈ 3.17) and {A, B} (CR ≈ 1.17) remains statistically significant with complete separation (δ = 1.000).

2. *The three-tier hierarchy (A < B << {C, D}) does not replicate.* GPT-5.2 showed B TP ≈ 2.0 (significantly higher than A), attributed to mathematical formalization induced by paper-format framing (§4.4). Sonnet shows B TP = 0, identical to A. The intermediate B effect appears model-specific — likely reflecting differences in how each model responds to academic framing conventions. The primary finding (externalization effect) is unaffected.

**Consistency across case studies.** Both CS1 and CS2 show {C, D} > {A, B} for both CR and TP with Sonnet, confirming cross-domain consistency within the replication.

### 4.8 Downstream Outcome: Implementation Test Pass Rate

To address the limitation that co-primary indicators measure the *presence* of verification-relevant information but not its *downstream utility* (§5.5), we conducted a downstream outcome measurement: whether design analyses produced under different conditions lead to functionally correct code implementations.

**Method.** All 40 design analysis outputs (4 conditions × 2 CS × 5 runs) were used as design input for code implementation. A separate LLM (Claude Sonnet 4.6) generated Python implementations from each design analysis, using a standardized prompt that included the problem statement, the design analysis output, and an interface specification. The implementation model had no access to the hidden test suites. Hidden test suites were derived solely from the original problem requirements: 10 tests for CS1 (citation renumbering) and 15 tests for CS2 (session management, including 5 edge-case tests targeting idempotency, tenant isolation, and state recovery). A reference implementation verified that all tests are satisfiable (10/10 and 15/15 respectively).

*Table 9. Downstream implementation test pass rates by condition.*

| Condition | CS1 Pass Rate | CS2 Pass Rate | Combined Mean |
|-----------|:------------:|:------------:|:-------------:|
| A (conventional) | 72.0% (SD=11.0) | 100.0% (SD=0.0) | 86.0% (SD=16.5) |
| B (paper-format) | 100.0% (SD=0.0) | 100.0% (SD=0.0) | 100.0% (SD=0.0) |
| C (PDD template) | 100.0% (SD=0.0) | 98.7% (SD=3.0) | 99.3% (SD=2.1) |
| D (checklist) | 100.0% (SD=0.0) | 93.3% (SD=0.0) | 96.7% (SD=3.5) |

**Main analysis.** The pre-registered comparison {C,D} vs {A,B} on test pass rate was not significant (stratified permutation test, p = 0.071, Cliff's δ = 0.025 [−0.275, 0.312]). The externalization effect observed for co-primary indicators does not directly translate to a downstream implementation quality advantage when using a capable implementation model.

**Post-hoc finding.** The comparison B vs A was significant (p = 0.0001, Cliff's δ = 0.500 [0.200, 0.800]). This difference is driven entirely by CS1, where condition A implementations consistently failed two tests related to token buffering and text preservation (0% pass rate on `test_first_appearance_order` and `test_text_preservation`), while B, C, and D all achieved 100%.

**Qualitative failure analysis.** The pattern of failures reveals an unexpected interaction between analysis depth and implementation complexity:

- *CS1 condition A failures*: Conventional analysis outputs lacked sufficient detail about streaming token boundary handling. The implementation model produced code that buffered partial patterns (`source_`) excessively, consuming trailing characters from non-citation text. All 5 runs exhibited the same systematic failure.
- *CS2 condition D failures*: All 5 checklist-derived implementations failed the idempotent bulk invalidation test (`test_idempotent_bulk_invalidation`). The checklist analyses specified a session-version counter architecture (atomic INCR) that correctly invalidates all sessions but does not track which sessions were *already* invalidated — returning the total session count on repeated calls rather than 0. This represents an over-engineered design choice guided by the analysis that introduces a subtle edge-case bug.
- *CS2 condition C failure*: One of 5 PDD template runs (run 5) failed `test_session_recreation_after_bulk_invalidation`. The analysis specified a JWT-based epoch architecture where bulk invalidation sets `revoked_after` to the current timestamp; new sessions created in the same second inherit `iat ≤ revoked_after`, causing immediate rejection.

**Interpretation.** The downstream results present a nuanced picture. The main externalization effect ({C,D} vs {A,B}) — which showed complete separation (δ = 1.000) on co-primary indicators — does not produce a statistically significant improvement in implementation test pass rates. This is partly due to a ceiling effect: a capable implementation model (Sonnet 4.6) can produce correct implementations even from minimal design analyses, particularly for CS2 where all conditions A and B achieved 100%. The interesting variance is concentrated in CS1 (where A underperforms) and in CS2 edge cases (where D and marginally C underperform).

The qualitative finding that structured analyses (C, D) occasionally led to *more complex* architectures that introduced edge-case bugs — while unstructured analyses (A, B) led to simpler, correct implementations — suggests a trade-off between analysis thoroughness and implementation simplicity. This is consistent with the observation that structured elicitation produces richer design documentation (§4.1) which, when faithfully followed by an implementation model, may over-engineer solutions for problems where simpler approaches suffice.

## 5. Discussion

### 5.1 Structured Elicitation as the Active Ingredient

The central finding of this study is that D (structured checklist) and C (PDD template) produced statistically equivalent co-primary indicator levels (TOST p < 0.0001 for both CR and TP; §4.3), while both dramatically outperformed A and B (§4.2). This D ≈ C equivalence triggers the pre-registered pivot criterion (protocol §9.1): when a checklist achieves the same indicator levels as the paper template, the paper format cannot be the active ingredient. We therefore update the thesis from "PDD template superiority" to "structured analysis requirements as the active ingredient" (formal deviation record: protocol §9.1; documented in `protocol-deviations.md`).

We term this mechanism **structured elicitation through information externalization**. Conditions C and D share a common structure: both explicitly request the identification of conflicting requirements, analysis of existing approaches, derivation of testable properties, and disclosure of constraints. They differ only in output framing — C requests an academic paper, D requests a structured checklist. The equivalence of their outcomes indicates that the active ingredient is the specification of analysis steps, not the format in which results are presented.

This finding connects to Gawande's checklist research [9]: in surgery and aviation, checklists reduce omission errors not by teaching new skills but by making required steps explicit. Similarly, LLMs can identify conflicting requirements and derive testable properties — as evidenced by the occasional non-zero values even in condition A (CR: 0.30 mean) — but do not reliably produce these analyses without explicit prompting. The structured requirements in C and D externalize what would otherwise remain implicit, converting sporadic capability into consistent output.

The tautology concern — that we are merely measuring template compliance — is partially addressed by the D condition. D uses a different format (numbered checklist items rather than paper sections) yet produces equivalent indicator levels. If the effect were purely template compliance, D's different format should yield different results. Instead, the equivalence suggests that the model performs genuine analytical work in response to the requirements, not mechanical format-filling. However, this argument has limits: both C and D explicitly name the same analysis categories, so the concern that we measure "requirement compliance" rather than "independent analytical quality" remains partially valid. What we can claim is that this compliance itself has practical value — it surfaces verification-relevant information that is otherwise omitted.

The practical implication is significant: practitioners need not adopt academic paper format to obtain the benefits of structured analysis. A simple checklist requesting the same analysis steps achieves equivalent results, with lower adoption barriers and shorter outputs (D: 78.1 lines vs C: 105.3 lines on average).

### 5.2 Three-Tier Hierarchy of Prompting Effects

The data reveal a three-tier hierarchy of prompting effects on co-primary indicators: A < B << {C, D}.

**Tier 1 (A: Conventional)**. Conventional prompting produces near-zero co-primary indicators (CR: 0.30, TP: 0.20). The model focuses on solution delivery without systematic analysis of trade-offs or verification conditions.

**Tier 2 (B: Paper Format)**. Paper-format framing produces a notable but asymmetric effect. For testable properties, B achieves TP ≈ 2.0 — significantly higher than A (p < 0.0001, Cliff's δ = 0.900; §4.4). This is an unexpected finding that contradicts the protocol's prediction of B ≈ A for both co-primary indicators (Deviation #2). Examination of B outputs reveals that this effect operates through mathematical formalization: paper-format framing induces proof-like sections where formal properties (e.g., "map immutability," "propagation delay bound") emerge as by-products of academic writing conventions. For conflicting requirements, however, B remains near zero (CR: 0.50, n.s. vs A), suggesting that the indirect formalization pathway elicits some verification-relevant information but not systematic trade-off analysis. The Phase 1 B-variant experiment (B1/B2/B3; Appendix C) further showed that varying the framing wording progressively increased output structure and exploration breadth but never produced non-zero CR — establishing a **framing effect ceiling** for this indicator.

**Tier 3 ({C, D}: Structured Requirements)**. Explicit analysis step requirements produce dramatically higher indicators (CR: 3.20–3.70, TP: 5.20–5.30), with complete separation from Tiers 1 and 2 (Cliff's δ = 1.000 for all {C, D} vs {A, B} pairs; §4.2). The gap between Tier 2 and Tier 3 is decisive: even B's partial TP effect (≈2.0) is fully dominated by structured requirements (≈5.2–5.3), with no overlap in the distributions.

This three-tier structure clarifies the role of paper-format framing: it exists but is limited. Framing contributes a secondary effect on TP through indirect formalization, but this effect is dwarfed by the primary effect of structured requirements. The practical implication reinforces §5.1: while changing instruction framing to "write a paper" may provide modest benefits (particularly for eliciting formal properties), the substantive improvement comes from explicitly specifying which analysis steps to perform.

**Downstream caveat.** The three-tier hierarchy on co-primary indicators does not map linearly to downstream implementation quality (§4.8). When a capable model implements designs from each condition, the pass rate ordering is B ≥ C > D > A — with condition A's deficit concentrated in CS1 (streaming buffer bugs from insufficient analysis detail) and condition D's deficit in CS2 (over-engineered revocation architecture introducing edge-case bugs). This suggests that the relationship between analysis thoroughness and implementation quality is non-monotonic: both too little analysis (A) and analysis that over-specifies architecture (D in some cases) can reduce implementation correctness.

**Cross-model caveat.** The three-tier hierarchy is partially model-specific. In the Sonnet 4.6 replication (§4.7), the intermediate B effect (Tier 2) was absent: B produced TP = 0, identical to A. The hierarchy collapsed to a two-tier structure: A ≈ B << {C, D}. This suggests that the mathematical formalization pathway — through which paper-format framing elicits testable properties in GPT-5.2 — is not a universal model behavior. The primary externalization effect (Tier 1/2 vs Tier 3), in contrast, replicated with identical effect sizes across both models, confirming its robustness.

### 5.3 Hypotheses for Prompting Effects

We retain three non-mutually-exclusive hypotheses for why structured prompting affects LLM output, updated with Phase 2 evidence:

**H1: Training Data Quality Bias.** Academic papers undergo peer review and exhibit rigorous logical structure. LLMs trained on this data may activate higher-quality generation patterns when the output format matches paper conventions. However, this hypothesis is weakened by the D ≈ C result: if training data quality bias were the primary mechanism, paper-format output (C) should outperform checklist-format output (D), which it does not. Training data composition is not publicly disclosed for most models, making this hypothesis difficult to verify directly.

**H2: Implicit Chain-of-Thought.** Structured analysis requirements enforce a reasoning sequence: problem definition → analysis of existing work → identification of conflicting requirements → proposal → derivation of testable properties → disclosure of constraints. This mirrors CoT prompting but is induced by task structure rather than explicit "think step by step" instruction [1]. The D ≈ C equivalence strengthens this hypothesis: both C and D impose the same analytical sequence regardless of output format, and both produce equivalent results. The active ingredient may be the implicit reasoning chain embedded in the analysis step specification, not the paper or checklist format itself.

**H3: Persona Effect.** "Write a paper" implicitly sets the persona to "researcher," which activates behavioral patterns associated with academic rigor [8]. Phase 2 data provides nuanced support: B vs A shows a significant effect on TP (p < 0.0001) but not on CR (§4.4), suggesting that the persona effect operates selectively — it elicits mathematical formalization (yielding testable properties as by-products) but does not trigger systematic trade-off analysis. The Phase 1 B-variant data (Appendix C) further showed progressive persona activation from B1 to B3, with increased academic conventions but persistent zero CR. The persona effect thus accounts for B's partial TP gains but not for the full externalization achieved by {C, D}.

### 5.4 Relationship to Format Constraint Research

The "Let Me Speak Freely?" study [2] found that strict format constraints (e.g., rigid JSON schemas) can degrade LLM reasoning by consuming cognitive capacity on format compliance. The structured analysis requirements used in conditions C and D are moderately structured: they specify analysis topics (conflicting requirements, existing approaches, testable properties, constraints) but not sentence-level format. This places structured elicitation in the "sweet spot" of structural guidance — enough to direct reasoning without constraining it. The three-tier hierarchy (§5.2) is consistent with this interpretation: the lightest constraint (B: paper-format framing) produces modest gains; moderate structure (C/D: analysis step specification) produces dramatic improvement; and there is no evidence that the additional formatting overhead of paper structure (C) degrades performance relative to a simpler checklist (D).

### 5.5 Limitations and Threats to Validity

- **Limited problem domains (2 case studies)**: Although each condition was run N=5 times (40 total executions), only two software design problems were used (citation rendering, session management). The externalization effect is consistent across both case studies (§4.5), but generalization to other problem domains (e.g., authentication, distributed systems, data modeling) remains unestablished.
- **Two models, same problem domains**: The main experiment used GPT-5.2 (N=10 per condition); a replication with Claude Sonnet 4.6 (N=6 per condition; §4.7) confirmed the externalization effect with identical effect sizes (δ = 1.000). However, both experiments used the same two problem domains. Model-specific differences were observed: the intermediate B effect (TP ≈ 2.0 in GPT-5.2) did not replicate with Sonnet (B TP = 0), suggesting that some secondary effects are model-dependent.
- **Author evaluation**: All Phase 2 indicators were scored by the author using Rubric v2 (§3.5). Preliminary LLM-based blinded evaluation (§4.6) shows excellent inter-rater reliability for the co-primary indicators (ICC: CR = 0.985, TP = 0.908), but LLM evaluators may share correlated biases with the LLM-generated outputs being scored. Human third-party evaluation is pending; until independent human evaluation confirms the scoring, evaluator bias cannot be fully ruled out.
- **Tautology concern**: The co-primary indicators (conflicting requirements, testable properties) are closely aligned with the analysis step requirements in conditions C and D. As discussed in §5.1, the D ≈ C equivalence partially addresses this concern — D's different format produces equivalent indicators, suggesting genuine analytical work rather than mechanical format-filling — but the concern that we measure "requirement compliance" rather than independent analytical quality remains partially valid.
- **Output length confound**: Condition C produced longer outputs (105.3 lines avg) than A (38.9 lines) and B (68.5 lines). However, line-normalized analysis (§4.5) confirms that the externalization effect persists after controlling for output volume: D produces the highest indicator density (CR/TL, TP/TL) despite shorter outputs than C, indicating that the effect is not an artifact of output length.
- **Prompt optimization**: The conventional prompt (A) was not optimized with CoT, persona, or other prompting techniques. A well-engineered conventional prompt might narrow the observed gap between A and {C, D}. However, B (which implicitly includes persona activation) still shows a large gap with {C, D} (Cliff's δ = 1.000), suggesting that standard prompting enhancements alone are unlikely to close the full gap.
- **Hallucination risk**: LLMs may fabricate non-existent approaches or citations. The structured requirements mitigate this by directing analysis toward known technologies, but do not eliminate the risk.
- **Confirmation bias**: Structured output may *appear* more rigorous without improving actual design quality. A preliminary downstream outcome measurement (§4.8) found that the externalization effect on co-primary indicators does not directly translate to implementation test pass rate improvements (p = 0.071), partly due to ceiling effects with a capable implementation model. The co-primary indicators measure the presence of verification-relevant information; their relationship to downstream implementation quality is complex (§4.8).
- **Temperature default**: All LLM executions used the default temperature setting (not explicitly controlled). Temperature variation could affect output variability, though the low within-condition variance observed (§4.1) suggests that this parameter had limited impact in practice.

### 5.6 Robustness Check: Self-Blinded Rescoring

This section reports a self-blinded rescoring procedure conducted on the **Phase 1** data (N=2, 5 conditions × 2 case studies = 10 outputs). This rescoring preceded the Phase 2 experiment and informed rubric refinements for Phase 2 scoring (Rubric v2; §3.5).

All 10 Phase 1 output files were stripped of condition labels, randomized, and re-scored by an independent AI agent (Claude Code) using only the rubric definitions in Appendix A.2. The rescorer had no access to condition labels or original scores. Full results are reported in Appendix B.

**Agreement rates by indicator**: existing approaches 90%, conflicting requirements 80%, formal invariants 90%, testable properties 50%, constraints disclosed 30%.

**Core claim robustness.** For conflicting requirements and testable properties under the strict definition (derived properties only, not input requirements), the Phase 1 finding that "these indicators were zero in all non-template conditions and non-zero only in C" was supported by the rescoring under the strict interpretation (see B.5 for the impact of strict vs. broad definitions on B-condition scoring). In condition C, both indicators showed perfect agreement between original and rescoring (conflicting requirements: 2/2, 3/3; testable properties: 6/6, 7/7). This pattern was subsequently confirmed at scale in Phase 2 (§4.2).

**Rubric sensitivity.** The two low-agreement indicators reveal rubric ambiguity:
- *Testable properties (50%)*: The rescorer counted B-condition input requirements (R1–R4 notation) as testable properties, while the original scoring distinguished input requirements (what the system must do) from derived testable properties (how the proposed solution behaves). Under the strict definition, B=0 holds; under the broad definition, B conditions contain 3–4 testable conditions. This distinction was clarified in Rubric v2 (§3.5) and applied consistently in Phase 2 scoring.
- *Constraints disclosed (30%)*: The original scoring included operational advice and future work items as constraint disclosure, while the rescorer counted only explicit limitations and boundary conditions of the proposed approach. The baseline values shift (A/B: 1.5 → 0–1), but the increase pattern under C is preserved.

**Post-hoc reclassification.** Based on the measurement reliability findings above, constraints disclosed was reclassified from co-primary to exploratory indicator. This reclassification was motivated by measurement instability (30% agreement, definition boundary ambiguity), not by the effect direction — the increase pattern under C was preserved under both scoring interpretations. In Phase 2, constraints disclosed is reported as an exploratory indicator (§4.5) with this reclassification applied from the outset.

**Limitations of this procedure.** This is not independent third-party evaluation. The rescoring was conducted by an AI agent under author instruction, and both scorer and rescorer are AI systems with potentially correlated biases. The procedure serves as a supplementary robustness check for Phase 1, not a substitute for the third-party blinded evaluation currently in progress for Phase 2 (§4.6).

## 6. Related Work

**Spec-Driven Development.** Kiro (AWS) and GitHub Spec Kit [3, 4] structure requirements into specifications that guide LLM code generation. Structured analysis requirements complement SDD by addressing design rationale — why to build it that way — rather than requirements specification alone.

**Amazon Six-Pager / PR FAQ** [5]. Demonstrates that writing format affects thinking quality. Our findings refine this principle: while format (paper vs. checklist) has limited impact on verification-relevant indicators, the structuring of analytical steps within the format is the primary driver.

**RFC / ADR** [6]. Architecture Decision Records capture context → decision → consequences. The structured analysis requirements tested in this study (existing approaches, conflicting requirements, testable properties, constraints) provide a more systematic framework for design analysis than typical ADR templates.

**Checklists in Professional Practice** [9]. Gawande demonstrated that checklists reduce omission errors in surgery and aviation by making required steps explicit. Our D ≈ C equivalence result directly supports this principle in the LLM prompting domain: a structured checklist achieves the same analytical quality as a more elaborate paper template, suggesting that step enumeration — not format — is the active mechanism.

**Prompt Engineering** [1, 2, 8]. CoT, persona prompting, and format constraint research provide theoretical grounding for the observed effects. The structured analysis requirements can be viewed as a domain-specific application of these techniques to software design analysis, with the three-tier hierarchy (§5.2) empirically distinguishing the contributions of persona activation (B's TP effect) from explicit step structuring ({C, D}'s full externalization).

**Prompt Engineering Surveys.** The Prompt Report [10] catalogued 58 text-based prompting techniques across six problem-solving categories, establishing a taxonomy for the fragmented prompting landscape. Structured analysis requirements can be positioned within this taxonomy as a domain-specific template prompt combining elements of role prompting, structured output, and implicit CoT — applied specifically to software design analysis rather than general-purpose reasoning.

**Self-Planning Code Generation.** Jiang et al. [11] decompose code generation into a planning phase (deriving solution steps from the problem intent) and an implementation phase. Structured analysis requirements similarly separate design analysis from implementation but operate at the architectural level — structuring trade-off analysis and constraint identification rather than function-level code planning.

**Prompt Templates in Practice.** A systematic analysis of prompt templates in real-world LLM-powered applications [12] found that template structure — component ordering, role placement, and example positioning — affects LLM instruction-following performance. The structured analysis requirements tested in this study are a specific instance of this broader observation, with the additional finding that the content of the template (which analytical steps to require) matters more than the format (paper vs. checklist).

## 7. Future Work

1. **Human third-party blinded evaluation**: Independent human evaluators scoring outputs without condition labels (§3.7). Preliminary LLM-based evaluation (§4.6) confirms excellent agreement on co-primary indicators (ICC: CR = 0.985, TP = 0.908), but human evaluation is needed to rule out correlated LLM biases. Evaluation packages have been prepared and blinded; evaluator recruitment is pending.
2. **Additional model validation**: The externalization effect replicates across GPT-5.2 and Claude Sonnet 4.6 (§4.7), but validation with additional model families (e.g., Gemini, open-weight models) would strengthen the generalizability claim. The model-specific B effect (§4.7) suggests that secondary effects may vary across architectures.
3. **Multi-domain validation**: Apply structured analysis requirements to problem domains beyond citation rendering and session management (e.g., authentication, distributed systems, data modeling) to assess generalizability.
4. **Extended downstream impact measurement**: Preliminary downstream measurement (§4.8) found that a capable implementation model achieves high test pass rates across all conditions, with ceiling effects limiting differentiation. Future work should use more challenging problem domains, larger test suites, and varied implementation model capabilities to better distinguish downstream quality differences. Metrics beyond pass/fail (e.g., code complexity, maintainability, performance) may reveal additional downstream effects.
5. **Ablation study**: Determine which analysis steps in the structured requirements are most effective. The current C and D conditions include all four categories (conflicting requirements, existing approaches, testable properties, constraints) as a bundle. Systematic removal of individual categories would identify the minimum effective checklist.
6. **Enhanced prompt comparison**: Compare structured analysis requirements against optimized conventional prompts (e.g., CoT + persona + detailed instructions) to establish whether the observed gap persists under best-practice prompting.
7. **Causal mechanism investigation**: The implicit chain-of-thought hypothesis (§5.3, H2) suggests that structured requirements work by inducing a reasoning sequence. Controlled experiments varying the order and granularity of analysis steps could test this hypothesis and distinguish it from alternative mechanisms (training data bias, persona effects).

## 8. Conclusion

In a four-condition controlled experiment with GPT-5.2 (N=10 per condition, two software design problems), replicated with Claude Sonnet 4.6 (N=6 per condition; §4.7), we found that structured analysis requirements — explicitly prompting an LLM to identify conflicting requirements, analyze existing approaches, derive testable properties, and disclose constraints — dramatically improve design analysis quality as measured by two co-primary indicators. Conditions with structured requirements (C: PDD template, D: structured checklist) achieved complete separation from conditions without them (A: conventional, B: paper-format), with Cliff's δ = 1.000 for all pairwise comparisons across both models (§4.2, §4.7).

Crucially, the PDD template (C) and the structured checklist (D) produced statistically equivalent co-primary indicator levels (TOST p < 0.0001; §4.3). This equivalence triggered the pre-registered pivot criterion (protocol §9.1): the active ingredient is the structuring of analysis steps, not the academic paper format. Paper-format framing contributes a limited secondary effect — eliciting testable properties through mathematical formalization (B: TP ≈ 2.0 vs A: TP ≈ 0.2; §4.4) — but this effect is dwarfed by structured requirements (C/D: TP ≈ 5.2–5.3).

We interpret the mechanism as **structured elicitation through information externalization** (§5.1): LLMs possess the analytical capabilities to identify trade-offs and derive verification conditions, but do not reliably exercise them without explicit prompting. Structured requirements — whether formatted as a paper template or a checklist — convert this sporadic capability into consistent output, analogous to how surgical checklists reduce omission errors [9].

For practitioners, the key implication is that a structured checklist is sufficient. Academic paper format is not required to obtain the benefits of structured analysis. We provide both implementations — the PDD template and an equivalent checklist — as open-source tools at https://github.com/rema424/paper-driven-dev.

These findings replicate across two model families (GPT-5.2 and Claude Sonnet 4.6; §4.7) but are limited to two problem domains. Preliminary LLM-based blinded evaluation (§4.6) confirms excellent inter-rater reliability for the co-primary indicators (ICC ≥ 0.90); human third-party evaluation is pending. A downstream implementation test (§4.8) found that the externalization effect on co-primary indicators does not directly translate to statistically significant implementation quality differences when a capable implementation model is used, though qualitative analysis reveals that structured analyses can both prevent errors (CS1: avoiding streaming buffer bugs) and introduce them (CS2: over-engineered revocation architectures). Domain generalization and extended downstream measurement remain future work (§7).

## References

### Academic

[1] J. Wei et al., "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models," NeurIPS 2022. https://arxiv.org/abs/2201.11903

[2] Y. Tam et al., "Let Me Speak Freely? A Study on the Impact of Format Restrictions on Performance of Large Language Models," 2024. https://arxiv.org/abs/2408.02442

### Practitioner

[3] Thoughtworks, "Spec-driven development: unpacking 2025's new engineering practices," 2025. https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices

[4] M. Fowler, "Spec-Driven Development Tools," 2025. https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html

[5] Six Pager Memo, "What Is an Amazon Six-Pager?" https://www.sixpagermemo.com/blog/what-is-an-amazon-six-pager

[6] M. Nygard, "Documenting Architecture Decisions," 2011. https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions

[7] Google Engineering Practices, "Design Documents." https://google.github.io/eng-practices/

### Tutorial / Explainer

[8] Learn Prompting, "Role Prompting." https://learnprompting.org/docs/advanced/zero_shot/role_prompting

### Surveys

[10] S. Schulhoff et al., "The Prompt Report: A Systematic Survey of Prompting Techniques," arXiv:2406.06608, 2024. https://arxiv.org/abs/2406.06608

### Software Engineering

[11] X. Jiang et al., "Self-Planning Code Generation with Large Language Models," ACM Trans. Softw. Eng. Methodol. 33(7), 2024. https://dl.acm.org/doi/10.1145/3672456

[12] Y. Mao et al., "From Prompts to Templates: A Systematic Prompt Template Analysis for Real-world LLMapps," Proc. FSE 2025 (Industry). https://arxiv.org/abs/2504.02052

### Books

[9] A. Gawande, "The Checklist Manifesto: How to Get Things Right," Metropolitan Books, 2009.

---

## Appendix A: Reproducibility Package

### A.1 Prompts

All prompts were in Japanese. The problem description was identical across conditions; only the instruction prefix differed.

**Phase 2 conditions (4 conditions × 2 CS × 5 runs = 40 executions):**

| Condition | Instruction prefix (Japanese) | Translation |
|-----------|------------------------------|-------------|
| A: Conventional | 「以下の技術的な問題について、設計分析と解決策を提案してください」 | "Please propose a design analysis and solution for this problem" |
| B: Paper-format | 「以下の技術的な問題について、学術論文の形式で書いてください」 | "Please write about this problem in academic paper format" |
| C: PDD Template | B の指示文 + テンプレート §1–§7 ガイドライン | B instruction + template §1–§7 guidelines |
| D: Checklist | 「以下の技術的な問題について、以下の分析項目に従って順番に分析してください」+ 分析項目1–9 | "Please analyze by following these analysis items in order" + items 1–9 |

The template §1–§7 guidelines (condition C) and the 1–9 analysis items (condition D) are defined in §3.2. Conditions C and D share the same analytical requirements in isomorphic structure; only the output framing differs. The complete Japanese prompt text for each condition (instruction prefix + problem description) is available in the project repository (see A.3).

**Phase 1 B-variant conditions (Appendix C):** B1 = Phase 2's B condition; B2 ("論文を書いてください"); B3 ("学術論文を書いてください").

### A.2 Scoring Rubric

Each indicator was counted manually by the first author using the following definitions:

| Indicator | Counting rule |
|-----------|--------------|
| **Conflicting requirements** | Count of explicitly stated pairs of opposing requirements or trade-offs. Implicit tensions (e.g., "balancing X and Y" without formal definition) are counted as 0. |
| **Testable properties** | Count of concrete conditions derived from the proposed solution that could be translated to test cases. Given/When/Then format counts as 1 per property. Evaluation metrics (e.g., "accuracy should be 100%") count as 1 per metric. **Distinction**: Input requirements that define the problem (e.g., R1–R4 notation formalizing what the system must do) are not counted; only properties derived from the proposed approach (verifying how the solution behaves) are counted. See Appendix B for the impact of this distinction on inter-rater agreement. |
| **Constraints disclosed** | Count of explicitly stated limitations, boundary conditions, or failure modes of the proposed approach. General disclaimers (e.g., "further testing needed") do not count. |
| **Existing approaches analyzed** | Count of distinct alternative approaches enumerated and evaluated. Passing mentions without evaluation do not count. |
| **Formal invariants/proofs** | Count of mathematical or logical properties formally stated (definitions, theorems, proofs). Informal reasoning does not count. |
| **Total lines** | Line count of LLM output, excluding metadata headers. Empty lines included. |

### A.3 Raw Data and Outputs

All raw outputs and measurement data are publicly available in the project repository:

- **Phase 2 LLM outputs**: `docs/examples/fullpaper/cs{1,2}-{conventional,paper-format,pdd-template,checklist}-run{1-5}.md` (40 files)
- **Phase 2 scoring data**: `paper/scoring-data-v2.md` (Rubric v2 applied, all indicators with evidence)
- **Phase 2 statistical analysis**: `paper/analysis-results-v2.md` (results), `paper/analysis/statistical_analysis.py` (script)
- **Sonnet replication LLM outputs**: `docs/examples/fullpaper/sonnet/cs{1,2}-{conventional,paper-format,pdd-template,checklist}-run{1-3}.md` (24 files)
- **Sonnet replication scoring data**: `paper/scoring-data-sonnet.md`
- **Sonnet replication statistical analysis**: `paper/analysis-results-sonnet.md` (results), `paper/analysis/statistical_analysis_sonnet.py` (script)
- **Phase 1 LLM outputs**: `docs/examples/cs{1,2}-{conventional,paper-format,pdd-template}.md` (A/B1/C), `docs/examples/cs{1,2}-{paper-write,academic-paper}.md` (B2/B3)
- **Phase 1 quantitative measurements**: `paper/comparison-data.md`
- **Repository**: https://github.com/rema424/paper-driven-dev

### A.4 Execution Environment

**Phase 2 (main experiment):**
- **Model**: GPT-5.2, accessed via Codex CLI (OpenAI), February 2026
- **Temperature**: Default (not explicitly set; see §5.5)
- **Runs**: 5 independent runs per condition per case study (40 total). Each run used a fresh Codex thread with no prior conversation history.
- **Execution order**: Randomized across conditions and case studies (seed=42) to prevent ordering effects.

**Sonnet 4.6 replication (§4.7):**
- **Model**: Claude Sonnet 4.6, accessed via Claude Code CLI (Anthropic), February 2026
- **Temperature**: Default (not explicitly set)
- **Runs**: 3 independent runs per condition per case study (24 total). Each run used a fresh agent invocation with no prior conversation history.
- **Execution order**: Randomized across conditions and case studies (seed=43) to prevent ordering effects.

**Phase 1 (exploratory; Appendix C):**
- Same model and access method as Phase 2. Each condition was executed once per case study (N=2). CS2-B3 was recovered after context compression in the same Codex thread.

---

## Appendix B: Self-Blinded Rescoring

### B.1 Procedure

1. All 10 output files (5 conditions × 2 case studies) were stripped of condition labels and file names
2. Files were presented in randomized order
3. An independent AI agent (Claude Code) scored each file using only the rubric definitions in Appendix A.2
4. The rescorer had no access to condition labels, original scores, or the paper's claims

This procedure is author-initiated AI-based rescoring, not independent human evaluation. See §5.6 for interpretation and limitations.

### B.2 Rescoring Results

**CS1: RAG Citation Renumbering**

| Metric | A (orig) | A (rescore) | B1 (orig) | B1 (rescore) | B2 (orig) | B2 (rescore) | B3 (orig) | B3 (rescore) | C (orig) | C (rescore) |
|--------|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Total lines | 58 | 63 | 96 | 101 | 86 | 92 | 98 | 104 | 137 | 142 |
| Existing approaches | 0 | 0 | 0 | 0 | 2 | 1 | 3 | 3 | 4 | 4 |
| Conflicting requirements | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 2 |
| Formal invariants | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 |
| Testable properties | 0 | 0 | 0 | 3 | 0 | 4 | 0 | 4 | 6 | 6 |
| Constraints disclosed | 2 | 1 | 2 | 2 | 2 | 1 | 2 | 1 | 6 | 3 |

**CS2: Multi-Tenant Session Management**

| Metric | A (orig) | A (rescore) | B1 (orig) | B1 (rescore) | B2 (orig) | B2 (rescore) | B3 (orig) | B3 (rescore) | C (orig) | C (rescore) |
|--------|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Total lines | 65 | 70 | 83 | 88 | 117 | 123 | 109 | 115 | 121 | 126 |
| Existing approaches | 3 | 3 | 4 | 4 | 3 | 3 | 4 | 4 | 4 | 4 |
| Conflicting requirements | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 3 | 3 |
| Formal invariants | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Testable properties | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 4 | 7 | 7 |
| Constraints disclosed | 1 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | 5 | 5 |

### B.3 Agreement Rates

| Indicator | Agreements / Total | Agreement Rate |
|-----------|---:|---:|
| Existing approaches | 9/10 | 90% |
| Conflicting requirements | 8/10 | 80% |
| Formal invariants | 9/10 | 90% |
| Testable properties | 5/10 | 50% |
| Constraints disclosed | 3/10 | 30% |

### B.4 Agreement in Condition C

| Indicator | CS1-C | CS2-C |
|-----------|-------|-------|
| Existing approaches | 4 / 4 ✓ | 4 / 4 ✓ |
| Conflicting requirements | 2 / 2 ✓ | 3 / 3 ✓ |
| Testable properties | 6 / 6 ✓ | 7 / 7 ✓ |
| Constraints disclosed | 6 → 3 ✗ | 5 / 5 ✓ |

In condition C, conflicting requirements and testable properties showed perfect agreement across both case studies. Constraints disclosed diverged in CS1 due to the inclusion/exclusion of future work items.

### B.5 Analysis of Disagreements

**Testable properties (50% agreement).** All disagreements occurred in B conditions, where the rescorer counted input requirements (R1–R4 notation) as testable properties. The original scoring distinguished input requirements (problem-level specifications) from derived testable properties (solution-level verifiable behaviors). Under the strict definition (derived properties only), B=0 holds across all variants. Under the broad definition (any testable condition), B conditions contain 3–4 items. The strict definition is adopted in this paper because template section §6 (testable properties) requests properties of the proposed solution, not restatements of problem requirements.

**Constraints disclosed (30% agreement).** Two sources of disagreement: (1) In A/B conditions, the original scoring counted operational advice as constraint disclosure while the rescorer did not. This reduces baseline values from 1.5 to 0–1 but preserves the increase pattern under C. (2) In CS1-C, the original scoring included 3 future work items as constraints; the rescorer excluded these. The C-condition increase relative to A/B is maintained under both interpretations.

**Conflicting requirements (80% agreement).** In CS2-B1 and CS2-B3, the rescorer counted narrative tension descriptions as conflicting requirements (1 each), while the original scoring required formally defined pairs (as in template §1.2). The qualitative difference between narrative mention and formal definition remains.

---

## Appendix C: Phase 1 Exploratory Study (N=2)

This appendix preserves the results of the Phase 1 exploratory study (N=2, three conditions A/B/C plus B-variant comparison), which generated the hypotheses tested in the Phase 2 experiment (§3–§4). Per protocol §10.2, Phase 1 data are not included in the main analysis.

### C.1 Three-Condition Comparison (A/B/C)

Three conditions were compared: (A) conventional prompting, (B) paper-format instruction without template, and (C) PDD template with template §1–§7 guidelines. Each condition was run once per case study (N=2 total).

| Metric | A: Conventional (avg) | B: Paper-format (avg) | C: PDD Template (avg) |
| --- | ---: | ---: | ---: |
| Total lines | 62 | 90 | 129 |
| Existing approaches analyzed | 1.5 | 2.0 | 4.0 |
| Conflicting requirements | 0 | 0 | 2.5 |
| Testable properties | 0 | 0 | 6.5 |
| Constraints disclosed | 1.5 | 1.5 | 4.0 |

**Co-primary indicators.** Conflicting requirements and testable properties were observed only under condition C, remaining at zero for both A and B under the strict scoring definition. Self-blinded rescoring confirmed this pattern with perfect agreement in condition C (§5.6). **Note on B vs. Phase 2 discrepancy**: Phase 2 found B produces TP ≈ 2.0 (§4.4), whereas Phase 1 scored B as TP = 0. The Phase 1 rescoring (Appendix B.5) revealed that B outputs contain formalized properties (R1–R4 notation), but these were classified as input requirements rather than derived testable properties under the strict definition. Phase 2 B outputs, with N=5 per case study, consistently produce mathematical proof-like properties (e.g., "map immutability," "propagation delay bound") that qualify as derived testable properties under Rubric v2. The discrepancy likely reflects both the small Phase 1 sample (N=2) and the rubric clarification between phases. **Exploratory indicator.** Constraints disclosed were present at baseline (A: 1.5, B: 1.5) and increased under C (4.0), but this indicator was reclassified as exploratory due to low measurement reliability (30% inter-rater agreement; see §5.6). Among secondary indicators, formal invariants showed no condition-dependent variation (0.5 across all conditions).

**Secondary observations.** Existing approaches analyzed increased modestly from A (1.5) to B (2.0) and substantially under C (4.0). All three conditions reached the same correct design conclusion for both problems—the difference was in justification and verifiability, not in the answer itself.

**Qualitative notes.** Condition B spontaneously produced academic conventions (abstract, keywords, references in CS2; a mathematical proof of prefix-determinability in CS1) that were absent in both A and C. This suggests that paper-format framing activates distinct output behaviors, though these did not include the co-primary indicators.

### C.2 B-Variant Comparison (B1/B2/B3)

To investigate whether framing variations could close the gap with condition C, three B-variant phrasings were tested: B1 ("学術論文の形式で書いてください" — write in academic paper format), B2 ("論文を書いてください" — write a paper), and B3 ("学術論文を書いてください" — write an academic paper).

| Metric | B1 (avg) | B2 (avg) | B3 (avg) | C (avg, ref) |
| --- | ---: | ---: | ---: | ---: |
| Total lines | 90 | 102 | 104 | 129 |
| Existing approaches analyzed | 2.0 | 2.5 | 3.5 | 4.0 |
| Conflicting requirements | 0 | 0 | 0 | 2.5 |
| Testable properties | 0 | 0 | 0 | 6.5 |
| Constraints disclosed | 1.5 | 1.5 | 1.5 | 4.0 |

**Framing effect.** Output length and exploration breadth (existing approaches analyzed) increased progressively from B1 to B3. B3 also exhibited stronger academic conventions: keywords, references, and formalized requirement definitions (R1–R4 notation). In CS1, B3 independently generated an "evaluation metrics and experimental plan" section with four measurable criteria—a behavior absent in B1 and B2.

**Framing effect ceiling.** Despite these progressive improvements, the two co-primary indicators—conflicting requirements and testable properties—remained at zero across all B variants. The exploratory indicator (constraints disclosed) also showed no increase beyond the A/B baseline (1.5). The framing effect was associated with changes in output characteristics (exploration breadth, formality, academic conventions) but not with the appearance of the co-primary indicators. This framing effect ceiling—together with the observation that co-primary indicators appeared only under the template condition (C)—motivated the Phase 2 hypothesis that explicit analysis step requirements, rather than framing alone, drive co-primary indicator appearance.

### C.3 Cross-Model Observation

A separate two-condition comparison (conventional vs. PDD) was conducted with OpenAI o3 on the same two problems (see `comparison-data.md`, supplementary section). Although experimental conditions differed (model, number of conditions), o3 exhibited a similar pattern: co-primary indicators appeared only under the PDD template condition. This does not constitute a controlled multi-model comparison, but provides preliminary evidence that the observed pattern is not unique to a single model family.
