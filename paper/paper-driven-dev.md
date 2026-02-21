# Paper-Driven Development: Leveraging Academic Paper Structure for LLM-Assisted Software Design Analysis

> **実験条件**: Model: GPT-5.2 (via Codex) | N: 2 (CS1: citation rendering, CS2: session management) | Date: 2026-02 | Evaluator: 著者
> **補足**: 3条件比較（A/B/C）と B バリアント比較（B1/B2/B3）の定量データは comparison-data.md に集約。

## Abstract

We present Paper-Driven Development (PDD), a methodology for LLM-assisted software design analysis that uses a seven-section academic paper template (§1–§7) to guide model output. In an exploratory case study with GPT-5.2 (N=2, two software design problems), we compared three prompting conditions: (A) conventional prompting, (B) paper-format instruction without template, and (C) PDD template. Changing the instruction framing alone (A→B) was associated with increased output structure and exploration breadth, yet two co-primary indicators—conflicting requirements identified and testable properties derived—remained at zero across all framing variants (B1/B2/B3), appearing only under the PDD template condition (C). A self-blinded rescoring confirmed these two indicators' robustness (80% and 50% agreement; C-condition perfect match). A third indicator, constraints disclosed, showed an increase pattern under C but was reclassified as exploratory due to low measurement reliability (30% agreement). We interpret the template's role as information externalization and propose a two-tier practical guideline—Tier 1: change instruction framing (zero cost); Tier 2: apply the PDD template for critical design decisions—while acknowledging that causal validation and generalization remain future work. PDD is released as an open-source Claude Code plugin.

## 1. Introduction

Large Language Models (LLMs) have become integral to software development workflows, assisting with code generation, debugging, and design analysis. However, the quality of LLM output varies significantly depending on how problems are presented. The emerging field of prompt engineering has demonstrated that structured prompts can substantially improve reasoning quality [1, 2].

We began with an observation: simply changing the instruction from "propose a solution" to "write a paper" altered the output characteristics of LLM design analysis—increasing exploration breadth, structural formality, and adherence to academic conventions. However, further investigation through B-variant experiments (Appendix C) revealed that this framing effect has a ceiling: two co-primary indicators—conflicting requirements and testable properties—remained at zero regardless of framing variations. These indicators appeared only when the PDD template (§1–§7 section guidelines) was provided.

We interpret the template's role not as eliciting new capabilities from LLMs, but as **information externalization**: by specifying sections for existing approaches (§3), conflicting requirements (§1.2), testable properties (§6), and constraints (§7), the template prevents omission of analysis steps that LLMs can perform but do not spontaneously produce under conventional or paper-format-only prompting.

We term this methodology **Paper-Driven Development (PDD)** and contribute:

- A seven-section template (§1–§7) optimized for software design analysis
- Two case studies (citation rendering, session management) comparing three prompting conditions (A: conventional, B: paper-format, C: PDD template) and three B-variant framings (B1/B2/B3)
- A two-axis explanatory model distinguishing framing effects from template effects
- A self-blinded rescoring procedure that confirmed the robustness of two co-primary indicators and identified measurement instability in a third (leading to its post-hoc reclassification as exploratory; §5.6)
- Tier 1 / Tier 2 practical guidelines for practitioners
- An open-source Claude Code plugin

## 2. Background

### 2.1 LLM-Assisted Software Development

Recent tools and methodologies leverage LLMs for software design:

- **Spec-Driven Development** [3, 4]: Emerged in 2025 with AWS Kiro and GitHub Spec Kit. Focuses on translating natural language requirements into structured specifications (requirements.md → design.md → tasks.md). Addresses "what to build" but not "why to build it that way."
- **Amazon Narratives** [5]: Six-page memo format that forces structured prose over slides. Demonstrates that writing format affects thinking quality. Focuses on customer-facing narratives rather than technical analysis.
- **RFC/ADR** [6]: Architecture Decision Records capture context → decision → consequences. Record design rationale but do not structurally enforce exhaustive alternatives analysis.
- **Design Docs** [7]: Standard practice at Google, Uber, and Meta. Include "Alternatives Considered" sections, but their depth depends on the author rather than being structurally enforced.

### 2.2 Structured Output and Reasoning

Research on LLM reasoning suggests that output structure affects quality:

- **Chain-of-Thought (CoT)** [1]: Instructing models to reason step-by-step improves accuracy on complex tasks.
- **Persona Prompting** [8]: Assigning roles (e.g., "as a security researcher") affects output quality and focus.
- **Format Constraints** [2]: The "Let Me Speak Freely?" study found that strict format constraints can degrade reasoning, while moderate structure can improve it. This suggests an optimal level of structural guidance.

### 2.3 Gap in Existing Approaches

No existing methodology structurally enforces the combination of exhaustive alternatives survey, critical evaluation with limitations, and derivation of testable properties. Spec-driven development addresses requirements clarity but not design rationale. RFC/ADR records decisions but does not enforce analysis depth. CoT improves reasoning but does not structure the output for design review. PDD addresses this gap through a section-level template that makes these analysis steps explicit.

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
| C | PDD Template | Paper-format instruction + §1–§7 template guidelines |
| D | Structured Checklist | Checklist instruction + equivalent analysis items (no paper framing) |

**Condition A (Conventional).** "以下の技術的な問題について、設計分析と解決策を提案してください。" (Please propose a design analysis and solution for this problem.)

**Condition B (Paper-format).** "以下の技術的な問題について、学術論文の形式で書いてください。" (Please write about this problem in academic paper format.) This corresponds to Phase 1's B1 condition.

**Condition C (PDD Template).** Condition B's instruction plus explicit §1–§7 section guidelines specifying: problem definition with conflicting requirements (§1.2), current architecture (§2), existing approaches with limitations (§3), problem essence (§4), proposed method (§5), testable properties in Given/When/Then format (§6), and constraints (§7). The full template is reproduced in Appendix A.1. Key design decisions: §1.2 requires ≥2 conflicting requirements (forcing identification of genuine trade-offs); §3 requires explicit limitations per approach (preventing the common failure of listing only advantages); §6 requires Given/When/Then testable properties (bridging design analysis and TDD); §7 requires honest constraint disclosure (counteracting LLMs' tendency to present proposals as universally applicable).

**Condition D (Structured Checklist).** "以下の技術的な問題について、以下の分析項目に従って順番に分析してください。" (Please analyze the following problem by following these analysis items in order.) D requests the same nine analysis steps as C—including ≥2 conflicting requirements (item 2) and Given/When/Then testable conditions (item 8)—using numbered list notation (1–9) instead of paper section notation (§1–§7). The structural granularity (sub-items, approach-level method/advantages/limitations) is isomorphic to C; only the framing differs (technical analysis vs. academic paper). Full prompt in Appendix A.1.

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

Equivalence is strongly established: the difference between C and D falls well within the pre-specified margins. Per the pre-registered pivot criterion (protocol §9.1), this activates the thesis pivot: the active ingredient in the PDD template is the structuring of analysis steps, not the academic paper framing. D—a structured checklist requesting the same analysis steps without paper framing—achieves statistically equivalent co-primary indicator levels.

### 4.4 Post-hoc Finding: Paper Format and Testable Properties

An unexpected finding emerged from the B vs. A comparison. The protocol (§2, H_framing) predicted that both B and A would show near-zero co-primary indicators. This prediction held for CR (B: 0.50 vs. A: 0.30, p = 0.216, n.s.) but not for TP:

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

<!-- Step 2.3 完了後に記述。評価パッケージは作成済み（paper/evaluation/）。評価者募集中。 -->

## 5. Discussion

### 5.1 Framing Effect and Its Ceiling

The B-variant experiment (Appendix C) revealed that instruction framing—varying the wording from "write in paper format" to "write an academic paper"—was associated with progressive changes in output characteristics. From B1 to B3, outputs exhibited increased exploration breadth (existing approaches: 2.0 → 3.5), stronger academic conventions (keywords, references, formalized requirements), and greater structural formality. In CS1, B3 spontaneously generated an evaluation metrics section with four measurable criteria—a behavior not observed in B1 or B2.

However, the two co-primary indicators—conflicting requirements and testable properties—remained at zero across all B variants. This pattern—which we term the **framing effect ceiling**—suggests that framing changes are associated with improvements in output form (structure, breadth, academic conventions) but not with the externalization of verification-relevant information. In this data, the framing effect operated on a qualitatively different dimension than the template effect.

### 5.2 Template Effect as Information Externalization

The co-primary indicators appeared consistently only under condition C, where the §1–§7 template was provided. This raises a tautology concern: if the template requests "conflicting requirements" in §1.2 and "testable properties" in §6, measuring their presence may simply confirm that the model followed instructions.

We reframe this as **information externalization**. The template does not give LLMs new analytical capabilities—as evidenced by all conditions reaching the same correct design conclusions. Rather, it makes explicit what sections to write, thereby preventing the omission of analysis steps that LLMs can perform but do not spontaneously produce. The practical value lies in this externalization itself: just as a checklist reduces omission errors in surgery or aviation [9], the PDD template reduces omission of design analysis steps.

This reframing shifts the contribution from "the template improves quality" (a causal claim unsupported by the data) to "the template is associated with the consistent appearance of verification-relevant information that is otherwise omitted" (an observational claim supported by the data). Whether this externalized information leads to better downstream outcomes (fewer bugs, higher test coverage) remains untested.

### 5.3 Three Hypotheses

We retain three non-mutually-exclusive hypotheses for why paper-format prompting affects LLM output:

**H1: Training Data Quality Bias.** Academic papers undergo peer review and exhibit rigorous logical structure. LLMs trained on this data may activate higher-quality generation patterns when the output format matches paper conventions. However, training data composition is not publicly disclosed for most models, making this hypothesis difficult to verify directly.

**H2: Implicit Chain-of-Thought.** The paper structure enforces a reasoning sequence: problem definition → analysis of existing work → identification of the core difficulty → proposal → verification. This mirrors CoT prompting but is induced by format rather than explicit instruction [1].

**H3: Persona Effect.** "Write a paper" implicitly sets the persona to "researcher," which activates behavioral patterns associated with academic rigor [8]. The B-variant data partially supports this: B3 ("write an academic paper") exhibited more academic behaviors than B1 ("write in paper format"). However, this persona activation was insufficient to produce the co-primary indicators, suggesting that the persona effect accounts for the framing axis improvements but not for the template axis improvements observed in this data.

### 5.4 Relationship to Format Constraint Research

The "Let Me Speak Freely?" study [2] found that strict format constraints (e.g., rigid JSON schemas) can degrade LLM reasoning by consuming cognitive capacity on format compliance. PDD's template is moderately structured: it specifies section topics but not sentence-level format. This may place PDD in the "sweet spot" of structural guidance—enough to direct reasoning without constraining it. The B-variant results are consistent with this interpretation: even without the template, paper-format framing (a lighter structural constraint) was associated with increased output structure without apparent degradation of reasoning quality.

### 5.5 Limitations and Threats to Validity

- **Small sample (N=2)**: Two case studies, each run once per condition, are insufficient for statistical conclusions. All findings should be interpreted as exploratory observations, not confirmed effects.
- **Single model (GPT-5.2)**: The primary experiment used a single model. The o3 observation (Appendix C) provides weak supplementary evidence but does not constitute multi-model validation.
- **Author evaluation**: All metrics were counted by the authors, not independent evaluators. Blinded evaluation is needed to rule out evaluator bias.
- **Tautology concern**: The co-primary indicators (conflicting requirements, testable properties, constraints) are closely aligned with template section requirements (§1.2, §6, §7). As discussed in §5.2, we frame this as information externalization rather than quality improvement, but the concern remains that we are partially measuring template compliance rather than independent analytical quality.
- **Output length confound**: Condition C produced longer outputs (129 lines avg) than B (90 lines avg). The increase in co-primary indicators may partially reflect increased output volume rather than increased analytical depth. Per-line normalization was not performed.
- **Missing D condition**: A structured checklist condition (same analysis steps as PDD but without paper framing) was not tested. This prevents separating the template effect from the paper format effect within condition C.
- **CS2-B3 data uncertainty**: The CS2-B3 output was recovered after context compression in the same Codex thread. While likely close to the original, strict reproducibility cannot be guaranteed.
- **Prompt optimization**: The conventional prompt (A) was not optimized with CoT or persona techniques. A well-engineered conventional prompt might narrow the observed gap.
- **Hallucination risk**: LLMs may fabricate non-existent approaches or citations in §3. The template mitigates this by instructing the model to base analysis on known technologies, but does not eliminate the risk.
- **Confirmation bias**: Paper-format output may *appear* more rigorous without improving actual design quality. Downstream outcome measurement is needed.
- **Indicator measurement instability**: Self-blinded rescoring revealed that constraints disclosed (30% agreement) and testable properties under a broad definition (50%) are sensitive to rubric interpretation. The post-hoc reclassification of constraints disclosed as exploratory (§5.6) was motivated by this finding.

### 5.6 Robustness Check: Self-Blinded Rescoring

To assess the stability of the manual scoring, we conducted a self-blinded rescoring procedure. All 10 output files (5 conditions × 2 case studies) were stripped of condition labels, randomized, and re-scored by an independent AI agent (Claude Code) using only the rubric definitions in Appendix A.2. The rescorer had no access to condition labels or original scores. Full results are reported in Appendix B.

**Agreement rates by indicator**: existing approaches 90%, conflicting requirements 80%, formal invariants 90%, testable properties 50%, constraints disclosed 30%.

**Core claim robustness.** For conflicting requirements and testable properties under the strict definition (derived properties only, not input requirements), the finding that "these indicators were zero in all non-template conditions and non-zero only in C" was confirmed by the rescoring. In condition C, both indicators showed perfect agreement between original and rescoring (conflicting requirements: 2/2, 3/3; testable properties: 6/6, 7/7).

**Rubric sensitivity.** The two low-agreement indicators reveal rubric ambiguity:
- *Testable properties (50%)*: The rescorer counted B-condition input requirements (R1–R4 notation) as testable properties, while the original scoring distinguished input requirements (what the system must do) from derived testable properties (how the proposed solution behaves). Under the strict definition, B=0 holds; under the broad definition, B conditions contain 3–4 testable conditions. This distinction was not explicit in the original rubric and has been clarified in Appendix A.2.
- *Constraints disclosed (30%)*: The original scoring included operational advice and future work items as constraint disclosure, while the rescorer counted only explicit limitations and boundary conditions of the proposed approach. The baseline values shift (A/B: 1.5 → 0–1), but the increase pattern under C is preserved.

**Post-hoc reclassification.** Based on the measurement reliability findings above, constraints disclosed was reclassified from co-primary to exploratory indicator. This reclassification was motivated by measurement instability (30% agreement, definition boundary ambiguity), not by the effect direction—the increase pattern under C was preserved under both scoring interpretations. The reclassification was performed after the rescoring results were known; the original three-indicator data remain fully reported in Appendix C and Appendix B.

**Limitations of this procedure.** This is not independent third-party evaluation. The rescoring was conducted by an AI agent under author instruction, and both scorer and rescorer are AI systems with potentially correlated biases. The procedure serves as a supplementary robustness check, not a substitute for the blinded human evaluation recommended in §7.

## 6. Related Work

**Spec-Driven Development.** Kiro (AWS) and GitHub Spec Kit [3, 4] structure requirements into specifications that guide LLM code generation. PDD complements SDD by addressing design rationale rather than requirements.

**Amazon Six-Pager / PR FAQ** [5]. Demonstrates that writing format affects thinking quality. PDD extends this principle to LLM-assisted technical analysis, adding critical evaluation of alternatives.

**RFC / ADR** [6]. Architecture Decision Records capture design decisions with context and consequences. PDD's §3 (existing approaches) and §7 (constraints) provide more structured analysis than typical ADR templates.

**Prompt Engineering** [1, 2, 8]. CoT, persona prompting, and format constraint research provide theoretical grounding for PDD's observed effects. PDD can be viewed as a domain-specific application of these techniques to software design analysis.

**Prompt Engineering Surveys.** The Prompt Report [10] catalogued 58 text-based prompting techniques across six problem-solving categories, establishing a taxonomy for the fragmented prompting landscape. PDD can be positioned within this taxonomy as a domain-specific template prompt combining elements of role prompting, structured output, and implicit CoT—applied specifically to software design analysis rather than general-purpose reasoning.

**Self-Planning Code Generation.** Jiang et al. [11] decompose code generation into a planning phase (deriving solution steps from the problem intent) and an implementation phase. PDD similarly separates design analysis (§1–§7) from implementation but operates at the architectural level—structuring trade-off analysis and constraint identification rather than function-level code planning.

**Prompt Templates in Practice.** A systematic analysis of prompt templates in real-world LLM-powered applications [12] found that template structure—component ordering, role placement, and example positioning—affects LLM instruction-following performance. PDD's §1–§7 structure is a specific instance of this broader observation, with the additional property that each section targets a distinct analytical dimension (problem definition, alternatives analysis, verification).

## 7. Future Work

1. **D condition (structured checklist without paper framing)**: Test a condition where the same analysis steps (conflicting requirements, existing approaches, testable properties, constraints) are requested as a checklist without academic paper framing. This would separate the template effect from the paper format effect within condition C.
2. **Repeated trials (N≥5)**: Run each condition multiple times on the same problems to assess within-condition variability and establish confidence intervals for the observed differences.
3. **Blinded evaluation**: Have independent evaluators (not the authors) count the indicators without knowing which condition produced each output.
4. **Per-line normalization**: Normalize co-primary indicator counts by output length to control for the output volume confound identified in §5.5.
5. **Multi-model validation**: Test PDD with Claude, Gemini, and other LLMs to assess whether the observed pattern generalizes beyond GPT-5.2 and o3.
6. **Multi-domain validation**: Apply PDD to authentication design, performance optimization, data modeling, and other problem domains.
7. **Downstream impact measurement**: Measure whether PDD-analyzed designs lead to fewer bugs, higher test coverage, or faster implementation compared to conventionally designed features.
8. **Rubric refinement for constraints disclosed**: The 30% inter-rater agreement for constraints disclosed indicates that the current definition boundary (what counts as a "constraint" vs. operational advice or future work) requires explicit operationalization before this indicator can serve as a primary outcome measure.

## 8. Conclusion

In an exploratory case study with GPT-5.2 (N=2, two software design problems), changing the instruction framing from conventional prompting to paper-format prompting was associated with increased output structure and exploration breadth. However, two co-primary indicators—conflicting requirements and testable properties—were absent in all non-template conditions and appeared only under the PDD template condition. A self-blinded rescoring confirmed this pattern. A third indicator (constraints disclosed) showed a similar directional pattern but was reclassified as exploratory due to low measurement reliability (30% inter-rater agreement), illustrating the need for rubric refinement in future work. We term the observed limit on framing effects the framing effect ceiling.

We interpret the template's role as information externalization: the §1–§7 structure specifies what analysis sections to write, preventing the omission of steps that LLMs can perform but do not spontaneously produce. All conditions reached the same correct design conclusions—the difference was in justification and verifiability, not in the answer itself.

For practitioners, we propose a two-tier guideline:

- **Tier 1 (zero cost)**: Change the instruction framing from "analyze this problem" to "write a paper about this problem." This was associated with increased exploration breadth and structural formality in our data.
- **Tier 2 (template cost)**: For critical design decisions where verifiability matters, apply the PDD template (§1–§7) to externalize conflicting requirements, testable properties, and constraints that may otherwise be omitted.

These findings are limited to two case studies on a single model with author evaluation. Causal claims, generalization, and downstream impact validation remain future work (§7).

PDD is available as an open-source Claude Code plugin at https://github.com/rema424/paper-driven-dev.

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

[12] "From Prompts to Templates: A Systematic Prompt Template Analysis for Real-world LLMapps," Proc. FSE 2025 (Industry). https://arxiv.org/abs/2504.02052

### Books

[9] A. Gawande, "The Checklist Manifesto: How to Get Things Right," Metropolitan Books, 2009.

---

## Appendix A: Reproducibility Package

### A.1 Prompts

All prompts were in Japanese. The problem description was identical across conditions; only the instruction prefix differed.

| Condition | Instruction prefix (Japanese) | Translation |
|-----------|------------------------------|-------------|
| A: Conventional | 「この問題の設計分析と解決策を提案してください」 | "Please propose a design analysis and solution for this problem" |
| B1: Paper-format | 「この問題について学術論文の形式で書いてください」 | "Please write about this problem in academic paper format" |
| B2: Paper-write | 「この問題について、論文を書いてください」 | "Please write a paper about this problem" |
| B3: Academic-paper | 「この問題について、学術論文を書いてください」 | "Please write an academic paper about this problem" |
| C: PDD Template | B1 の指示文 + §1–§7 テンプレートガイドライン | B1 instruction + §1–§7 template guidelines |

The §1–§7 template guidelines used in condition C are defined in §3.2 of this paper.

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

- **LLM outputs**: `docs/examples/cs{1,2}-{conventional,paper-format,pdd-template}.md` (A/B1/C conditions), `docs/examples/cs{1,2}-{paper-write,academic-paper}.md` (B2/B3 conditions)
- **Quantitative measurements**: `paper/comparison-data.md` (all tables, including per-case-study breakdowns)
- **Repository**: https://github.com/rema424/paper-driven-dev

### A.4 Execution Environment

- **Model**: GPT-5.2, accessed via Codex CLI (OpenAI), February 2026
- **Temperature**: Default (not explicitly set)
- **Single run**: Each condition was executed once per case study. No repetition or cherry-picking was performed.
- **Context**: Each condition was run in a fresh Codex thread with no prior conversation history, except CS2-B3 which was recovered in the same thread after context compression (see §5.5).

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

**Testable properties (50% agreement).** All disagreements occurred in B conditions, where the rescorer counted input requirements (R1–R4 notation) as testable properties. The original scoring distinguished input requirements (problem-level specifications) from derived testable properties (solution-level verifiable behaviors). Under the strict definition (derived properties only), B=0 holds across all variants. Under the broad definition (any testable condition), B conditions contain 3–4 items. The strict definition is adopted in the paper because §6 of the PDD template requests properties of the proposed solution, not restatements of problem requirements.

**Constraints disclosed (30% agreement).** Two sources of disagreement: (1) In A/B conditions, the original scoring counted operational advice as constraint disclosure while the rescorer did not. This reduces baseline values from 1.5 to 0–1 but preserves the increase pattern under C. (2) In CS1-C, the original scoring included 3 future work items as constraints; the rescorer excluded these. The C-condition increase relative to A/B is maintained under both interpretations.

**Conflicting requirements (80% agreement).** In CS2-B1 and CS2-B3, the rescorer counted narrative tension descriptions as conflicting requirements (1 each), while the original scoring required formally defined pairs (as in §1.2). The qualitative difference between narrative mention and formal definition remains.

---

## Appendix C: Phase 1 Exploratory Study (N=2)

This appendix preserves the results of the Phase 1 exploratory study (N=2, three conditions A/B/C plus B-variant comparison), which generated the hypotheses tested in the Phase 2 experiment (§3–§4). Per protocol §10.2, Phase 1 data are not included in the main analysis.

### C.1 Three-Condition Comparison (A/B/C)

Three conditions were compared: (A) conventional prompting, (B) paper-format instruction without template, and (C) PDD template with §1–§7 guidelines. Each condition was run once per case study (N=2 total).

| Metric | A: Conventional (avg) | B: Paper-format (avg) | C: PDD Template (avg) |
| --- | ---: | ---: | ---: |
| Total lines | 62 | 90 | 129 |
| Existing approaches analyzed | 1.5 | 2.0 | 4.0 |
| Conflicting requirements | 0 | 0 | 2.5 |
| Testable properties | 0 | 0 | 6.5 |
| Constraints disclosed | 1.5 | 1.5 | 4.0 |

**Co-primary indicators.** Conflicting requirements and testable properties were observed only under condition C, remaining at zero for both A and B. Self-blinded rescoring confirmed this pattern with perfect agreement in condition C (§5.6). **Exploratory indicator.** Constraints disclosed were present at baseline (A: 1.5, B: 1.5) and increased under C (4.0), but this indicator was reclassified as exploratory due to low measurement reliability (30% inter-rater agreement; see §5.6). Among secondary indicators, formal invariants showed no condition-dependent variation (0.5 across all conditions).

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
