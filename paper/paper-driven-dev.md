# Paper-Driven Development: Leveraging Academic Paper Structure for LLM-Assisted Software Design Analysis

> **実験条件**: Model: GPT-5.2 (via Codex) | N: 2 (CS1: citation rendering, CS2: session management) | Date: 2026-02 | Evaluator: 著者
> **補足**: 3条件比較（A/B/C）と B バリアント比較（B1/B2/B3）の定量データは comparison-data.md に集約。

## Abstract

We present Paper-Driven Development (PDD), a methodology for LLM-assisted software design analysis that uses a seven-section academic paper template (§1–§7) to guide model output. In an exploratory case study with GPT-5.2 (N=2, two software design problems), we compared three prompting conditions: (A) conventional prompting, (B) paper-format instruction without template, and (C) PDD template. Changing the instruction framing alone (A→B) was associated with increased output structure and exploration breadth, yet two co-primary indicators—conflicting requirements identified and testable properties derived—remained at zero across all framing variants (B1/B2/B3), and a third—constraints disclosed—showed no increase beyond baseline levels (1.5 avg). All three indicators increased substantially only under the PDD template condition (C). We interpret the template's role as information externalization: by specifying what sections to write, the template prevents omission of analysis steps that LLMs can perform but do not spontaneously produce. We propose a two-tier practical guideline—Tier 1: change instruction framing (zero cost) to increase exploration breadth; Tier 2: apply the PDD template for critical design decisions where verifiability matters—while acknowledging that causal validation and generalization remain future work. PDD is released as an open-source Claude Code plugin.

## 1. Introduction

Large Language Models (LLMs) have become integral to software development workflows, assisting with code generation, debugging, and design analysis. However, the quality of LLM output varies significantly depending on how problems are presented. The emerging field of prompt engineering has demonstrated that structured prompts can substantially improve reasoning quality [1, 2].

We began with an observation: simply changing the instruction from "propose a solution" to "write a paper" altered the output characteristics of LLM design analysis—increasing exploration breadth, structural formality, and adherence to academic conventions. However, further investigation through B-variant experiments (§4.3) revealed that this framing effect has a ceiling: conflicting requirements and testable properties remained at zero regardless of framing variations, and constraints disclosed showed no increase beyond baseline. These indicators increased substantially only when the PDD template (§1–§7 section guidelines) was provided.

We interpret the template's role not as eliciting new capabilities from LLMs, but as **information externalization**: by specifying sections for existing approaches (§3), conflicting requirements (§1.2), testable properties (§6), and constraints (§7), the template prevents omission of analysis steps that LLMs can perform but do not spontaneously produce under conventional or paper-format-only prompting.

We term this methodology **Paper-Driven Development (PDD)** and contribute:

- A seven-section template (§1–§7) optimized for software design analysis
- Two case studies (citation rendering, session management) comparing three prompting conditions (A: conventional, B: paper-format, C: PDD template) and three B-variant framings (B1/B2/B3)
- A two-axis explanatory model distinguishing framing effects from template effects
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

## 3. Paper-Driven Development

### 3.1 Template Structure

PDD uses a seven-section template modeled after academic paper conventions:

```
§1. Problem Definition
  §1.1 Background
  §1.2 Conflicting Requirements (opposing trade-offs)
  §1.3 Scope of This Document

§2. Current Architecture and Constraints

§3. Existing Approaches and Their Limitations
  §3.N Approach N: [Name] — Method / Advantages / Limitations

§4. Essence of the Problem

§5. Proposed Method
  §5.1 Fundamental Principle
  §5.2 Implementation Architecture

§6. Testable Properties

§7. Constraints and Future Work
```

Key design decisions in the template:

- **§1.2 requires identifying at least two conflicting requirements.** If only one requirement exists, the problem is trivial and does not warrant this analysis. This forces the model to identify genuine trade-offs.
- **§3 requires explicit "Limitations" for each approach.** This prevents the common failure mode of listing only advantages before recommending a solution.
- **§6 requires testable properties in Given/When/Then format.** This bridges the gap between design analysis and test-driven development.
- **§7 requires honest disclosure of constraints.** This counteracts LLMs' tendency to present proposals as universally applicable.

### 3.2 Evaluation Framework

To assess whether template-guided output differs from conventional or paper-format-only output, we define the following indicator hierarchy.

**Co-primary indicators** (main outcome measures):
- **Conflicting requirements identified**: Explicitly stated trade-offs or opposing requirements (e.g., "real-time display vs. correct sequential numbering")
- **Testable properties derived**: Concrete conditions that can be translated to test cases (e.g., Given/When/Then specifications)
- **Constraints disclosed**: Honest limitations of the proposed approach and conditions under which it does not apply

**Secondary indicators**:
- **Existing approaches analyzed**: Number of alternative approaches enumerated and evaluated
- **Formal invariants/proofs**: Mathematical or logical properties formally stated
- **Total output length**: Line count of LLM output

We adopt a two-axis explanatory model to describe the data:
- **Framing axis** (A → B1 → B2 → B3): Variation in instruction wording without template structure
- **Template axis** (B → C): Addition of §1–§7 section guidelines to a paper-format instruction

This two-axis model is a descriptive framework for organizing the observed data, not a claim of independence or orthogonality. A factorial design testing independence was not conducted.

### 3.3 Integration with Development Workflow

PDD is designed as an optional step in the design phase, not a replacement for existing practices:

```
Phase 1: Research
  Step 1. Investigation (research.md)
  Step 2. Design Analysis [Optional] (article.md via PDD)
           Applied only when multiple approaches are viable
           Uses research.md as input context

Phase 2: Planning
  Step 3. Implementation plan (plan.md)
           Uses article.md §5 (Proposed Method) as starting point
           Derives test plan from §6 (Testable Properties)

Phase 3: Implementation (TDD)
  Step 4. Test-first development
           §6 properties → test cases
```

### 3.4 Application Criteria

PDD is effective when:
- Multiple design approaches are viable and trade-off analysis is needed
- The problem involves fundamentally conflicting requirements
- Existing implementation requires architectural redesign
- Performance optimization requires trade-off analysis

PDD is unnecessary when:
- The solution is obvious (single viable approach)
- The task is a straightforward bug fix or small feature addition
- The design decision has already been made and only implementation remains

## 4. Case Study

We applied PDD to two software design problems using GPT-5.2 (via Codex), comparing three prompting conditions and three B-variant framings. All outputs and raw measurements are available in the companion document `comparison-data.md`.

### 4.1 Problem Descriptions

**CS1: Real-Time Citation Rendering in RAG Streaming.** Citations must be displayed as sequential numbers ([1], [2], [3]) without gaps during LLM streaming output, but renumbering requires knowing all citations—which is impossible when the full text has not yet been generated.

**CS2: Multi-Tenant SaaS Session Management.** A session management system must simultaneously support multi-device login, administrator-initiated immediate session revocation, horizontal scaling, and low latency—requirements that create tension between stateless and stateful architectures.

### 4.2 Three-Condition Comparison (A/B/C)

Three conditions were compared: (A) conventional prompting, (B) paper-format instruction without template, and (C) PDD template with §1–§7 guidelines. Each condition was run once per case study (N=2 total).

| Metric | A: Conventional (avg) | B: Paper-format (avg) | C: PDD Template (avg) |
| --- | ---: | ---: | ---: |
| Total lines | 62 | 90 | 129 |
| Existing approaches analyzed | 1.5 | 2.0 | 4.0 |
| Conflicting requirements | 0 | 0 | 2.5 |
| Testable properties | 0 | 0 | 6.5 |
| Constraints disclosed | 1.5 | 1.5 | 4.0 |

**Co-primary indicators.** Conflicting requirements and testable properties were observed only under condition C, remaining at zero for both A and B. Constraints disclosed were present at baseline (A: 1.5, B: 1.5) but increased substantially only under C (4.0). Among secondary indicators, formal invariants showed no condition-dependent variation (0.5 across all conditions).

**Secondary observations.** Existing approaches analyzed increased modestly from A (1.5) to B (2.0) and substantially under C (4.0). All three conditions reached the same correct design conclusion for both problems—the difference was in justification and verifiability, not in the answer itself.

**Qualitative notes.** Condition B spontaneously produced academic conventions (abstract, keywords, references in CS2; a mathematical proof of prefix-determinability in CS1) that were absent in both A and C. This suggests that paper-format framing activates distinct output behaviors, though these did not include the co-primary indicators.

### 4.3 B-Variant Comparison (B1/B2/B3)

To investigate whether framing variations could close the gap with condition C, we tested three B-variant phrasings: B1 ("学術論文の形式で書いてください" — write in academic paper format), B2 ("論文を書いてください" — write a paper), and B3 ("学術論文を書いてください" — write an academic paper).

| Metric | B1 (avg) | B2 (avg) | B3 (avg) | C (avg, ref) |
| --- | ---: | ---: | ---: | ---: |
| Total lines | 90 | 102 | 104 | 129 |
| Existing approaches analyzed | 2.0 | 2.5 | 3.5 | 4.0 |
| Conflicting requirements | 0 | 0 | 0 | 2.5 |
| Testable properties | 0 | 0 | 0 | 6.5 |
| Constraints disclosed | 1.5 | 1.5 | 1.5 | 4.0 |

**Framing effect.** Output length and exploration breadth (existing approaches analyzed) increased progressively from B1 to B3. B3 also exhibited stronger academic conventions: keywords, references, and formalized requirement definitions (R1–R4 notation). In CS1, B3 independently generated an "evaluation metrics and experimental plan" section with four measurable criteria—a behavior absent in B1 and B2.

**Framing effect ceiling.** Despite these progressive improvements, conflicting requirements and testable properties remained at zero across all B variants, and constraints disclosed showed no increase beyond the A/B baseline (1.5). The framing effect was associated with changes in output characteristics (exploration breadth, formality, academic conventions) but not with the appearance of conflicting requirements, testable properties, or increased constraint disclosure. We term this the **framing effect ceiling**: framing alone was insufficient, in this data, to elicit the information externalization observed under the template condition.

### 4.4 Cross-Model Observation

A separate two-condition comparison (conventional vs. PDD) was conducted with OpenAI o3 on the same two problems (see `comparison-data.md`, supplementary section). Although experimental conditions differed (model, number of conditions), o3 exhibited a similar pattern: co-primary indicators appeared only under the PDD template condition. This does not constitute a controlled multi-model comparison, but provides preliminary evidence that the observed pattern is not unique to a single model family.

## 5. Discussion

### 5.1 Framing Effect and Its Ceiling

The B-variant experiment (§4.3) revealed that instruction framing—varying the wording from "write in paper format" to "write an academic paper"—was associated with progressive changes in output characteristics. From B1 to B3, outputs exhibited increased exploration breadth (existing approaches: 2.0 → 3.5), stronger academic conventions (keywords, references, formalized requirements), and greater structural formality. In CS1, B3 spontaneously generated an evaluation metrics section with four measurable criteria—a behavior not observed in B1 or B2.

However, conflicting requirements and testable properties remained at zero across all B variants, and constraints disclosed showed no increase beyond baseline (1.5). This pattern—which we term the **framing effect ceiling**—suggests that framing changes are associated with improvements in output form (structure, breadth, academic conventions) but not with the externalization of verification-relevant information (conflicting requirements, testable properties, constraint disclosure). In this data, the framing effect operated on a qualitatively different dimension than the template effect.

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
- **Single model (GPT-5.2)**: The primary experiment used a single model. The o3 observation (§4.4) provides weak supplementary evidence but does not constitute multi-model validation.
- **Author evaluation**: All metrics were counted by the authors, not independent evaluators. Blinded evaluation is needed to rule out evaluator bias.
- **Tautology concern**: The co-primary indicators (conflicting requirements, testable properties, constraints) are closely aligned with template section requirements (§1.2, §6, §7). As discussed in §5.2, we frame this as information externalization rather than quality improvement, but the concern remains that we are partially measuring template compliance rather than independent analytical quality.
- **Output length confound**: Condition C produced longer outputs (129 lines avg) than B (90 lines avg). The increase in co-primary indicators may partially reflect increased output volume rather than increased analytical depth. Per-line normalization was not performed.
- **Missing D condition**: A structured checklist condition (same analysis steps as PDD but without paper framing) was not tested. This prevents separating the template effect from the paper format effect within condition C.
- **CS2-B3 data uncertainty**: The CS2-B3 output was recovered after context compression in the same Codex thread. While likely close to the original, strict reproducibility cannot be guaranteed.
- **Prompt optimization**: The conventional prompt (A) was not optimized with CoT or persona techniques. A well-engineered conventional prompt might narrow the observed gap.
- **Hallucination risk**: LLMs may fabricate non-existent approaches or citations in §3. The template mitigates this by instructing the model to base analysis on known technologies, but does not eliminate the risk.
- **Confirmation bias**: Paper-format output may *appear* more rigorous without improving actual design quality. Downstream outcome measurement is needed.

### 5.6 Robustness Check: Self-Blinded Rescoring

To assess the stability of the manual scoring, we conducted a self-blinded rescoring procedure. All 10 output files (5 conditions × 2 case studies) were stripped of condition labels, randomized, and re-scored by an independent AI agent (Claude Code) using only the rubric definitions in Appendix A.2. The rescorer had no access to condition labels or original scores. Full results are reported in Appendix B.

**Agreement rates by indicator**: existing approaches 90%, conflicting requirements 80%, formal invariants 90%, testable properties 50%, constraints disclosed 30%.

**Core claim robustness.** For conflicting requirements and testable properties under the strict definition (derived properties only, not input requirements), the finding that "these indicators were zero in all non-template conditions and non-zero only in C" was confirmed by the rescoring. In condition C, both indicators showed perfect agreement between original and rescoring (conflicting requirements: 2/2, 3/3; testable properties: 6/6, 7/7).

**Rubric sensitivity.** The two low-agreement indicators reveal rubric ambiguity:
- *Testable properties (50%)*: The rescorer counted B-condition input requirements (R1–R4 notation) as testable properties, while the original scoring distinguished input requirements (what the system must do) from derived testable properties (how the proposed solution behaves). Under the strict definition, B=0 holds; under the broad definition, B conditions contain 3–4 testable conditions. This distinction was not explicit in the original rubric and has been clarified in Appendix A.2.
- *Constraints disclosed (30%)*: The original scoring included operational advice and future work items as constraint disclosure, while the rescorer counted only explicit limitations and boundary conditions of the proposed approach. The baseline values shift (A/B: 1.5 → 0–1), but the increase pattern under C is preserved.

**Limitations of this procedure.** This is not independent third-party evaluation. The rescoring was conducted by an AI agent under author instruction, and both scorer and rescorer are AI systems with potentially correlated biases. The procedure serves as a supplementary robustness check, not a substitute for the blinded human evaluation recommended in §7.

## 6. Related Work

**Spec-Driven Development.** Kiro (AWS) and GitHub Spec Kit [3, 4] structure requirements into specifications that guide LLM code generation. PDD complements SDD by addressing design rationale rather than requirements.

**Amazon Six-Pager / PR FAQ** [5]. Demonstrates that writing format affects thinking quality. PDD extends this principle to LLM-assisted technical analysis, adding critical evaluation of alternatives.

**RFC / ADR** [6]. Architecture Decision Records capture design decisions with context and consequences. PDD's §3 (existing approaches) and §7 (constraints) provide more structured analysis than typical ADR templates.

**Prompt Engineering** [1, 2, 8]. CoT, persona prompting, and format constraint research provide theoretical grounding for PDD's observed effects. PDD can be viewed as a domain-specific application of these techniques to software design analysis.

## 7. Future Work

1. **D condition (structured checklist without paper framing)**: Test a condition where the same analysis steps (conflicting requirements, existing approaches, testable properties, constraints) are requested as a checklist without academic paper framing. This would separate the template effect from the paper format effect within condition C.
2. **Repeated trials (N≥5)**: Run each condition multiple times on the same problems to assess within-condition variability and establish confidence intervals for the observed differences.
3. **Blinded evaluation**: Have independent evaluators (not the authors) count the indicators without knowing which condition produced each output.
4. **Per-line normalization**: Normalize co-primary indicator counts by output length to control for the output volume confound identified in §5.5.
5. **Multi-model validation**: Test PDD with Claude, Gemini, and other LLMs to assess whether the observed pattern generalizes beyond GPT-5.2 and o3.
6. **Multi-domain validation**: Apply PDD to authentication design, performance optimization, data modeling, and other problem domains.
7. **Downstream impact measurement**: Measure whether PDD-analyzed designs lead to fewer bugs, higher test coverage, or faster implementation compared to conventionally designed features.

## 8. Conclusion

In an exploratory case study with GPT-5.2 (N=2, two software design problems), changing the instruction framing from conventional prompting to paper-format prompting was associated with increased output structure and exploration breadth. However, conflicting requirements and testable properties were absent in all non-template conditions, and constraints disclosed showed no increase beyond baseline levels. All three co-primary indicators increased substantially only under the PDD template condition. We term this the framing effect ceiling.

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

The §1–§7 template guidelines used in condition C are defined in §3.1 of this paper.

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
