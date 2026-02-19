# Paper-Driven Development: Leveraging Academic Paper Structure for LLM-Assisted Software Design Analysis

## Abstract

We present Paper-Driven Development (PDD), a methodology that improves the quality of LLM-assisted software design analysis by instructing the model to produce output in academic paper format. When asked to write a "paper" rather than simply "propose a solution," the template structurally elicits four behaviors that are absent or shallow in conventional prompting: (1) exhaustive survey of existing approaches, (2) critical evaluation with explicit limitations, (3) formal justification of proposals through invariants, and (4) derivation of testable properties. We describe the methodology, demonstrate it through a case study on real-time citation rendering in RAG streaming systems, and compare the output quality against conventional prompting on the same problem. We propose three hypotheses for why paper format elicits higher-quality output—training data quality bias, implicit chain-of-thought, and persona effect—while acknowledging that causal validation remains future work. PDD is released as an open-source Claude Code plugin.

## 1. Introduction

Large Language Models (LLMs) have become integral to software development workflows, assisting with code generation, debugging, and design analysis. However, the quality of LLM output varies significantly depending on how problems are presented. The emerging field of prompt engineering has demonstrated that structured prompts can substantially improve reasoning quality [1, 2].

We observed an unexpected phenomenon: when instructed to produce a design analysis in academic paper format—with sections for problem definition, related work, proposed method, and evaluation—LLMs generated more thorough and rigorous analysis compared to conventional prompting in our case studies. Specifically, the template structurally elicits four behaviors:

1. **Exhaustive prior art survey**: The model enumerates multiple existing approaches, not just the one it recommends.
2. **Critical evaluation**: Each approach is analyzed for limitations, not just advantages.
3. **Formal justification**: Proposals include invariants and formal properties.
4. **Testable properties**: The model derives concrete test conditions that can be directly translated to test cases.

We term this methodology **Paper-Driven Development (PDD)** and contribute:

- A seven-section template (§1–§7) optimized for software design analysis
- A case study comparing PDD output against conventional prompting on the same problem
- Three hypotheses explaining the observed quality improvement
- An open-source Claude Code plugin for practitioners

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

No existing methodology combines all four properties that PDD elicits: (1) exhaustive alternatives survey, (2) critical evaluation with limitations, (3) formal invariants, and (4) testable properties. Spec-driven development addresses requirements clarity but not design rationale. RFC/ADR records decisions but does not enforce analysis depth. CoT improves reasoning but does not structure the output for design review.

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

### 3.2 Integration with Development Workflow

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

### 3.3 Application Criteria

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

### 4.1 Problem: Real-Time Citation Rendering in RAG Streaming

We applied PDD to a real design problem: rendering citation references in real-time during LLM streaming output in a RAG (Retrieval-Augmented Generation) system.

The core conflict: citations must be displayed as sequential numbers ([1], [2], [3]) without gaps, but renumbering requires knowing all citations—which is impossible during streaming when the full text has not yet been generated.

### 4.2 PDD Output Analysis

The paper-format output (270 lines) produced:

- **§1.2**: Formally identified two conflicting requirements (real-time display vs. correct sequential numbering)
- **§3**: Analyzed five existing approaches (spinner wait, manual JSON parser, LLM direct numbering, gap tolerance, temporary numbers with replacement), each with specific limitations
- **§4**: Identified the root cause as "non-deterministic numbering order"—client-side and server-side use different ordering sources
- **§5**: Proposed "body-order unification with append-only invariant," formally defined as: for any prefix P of complete text T, all (source_ID, display_ID) pairs assigned by renumber(P) remain identical in renumber(T)
- **§6**: Defined four testable properties (consistency, append-only, sequential, graceful degradation)
- **§7**: Identified three specific constraints (summary citation timing, JSON field order dependency, mid-token citation appearance)

### 4.3 Comparison with Conventional Prompting

We prompted the same problem using a conventional format ("Please propose a design analysis and solution for this problem"). The output (40 lines) correctly identified the same core algorithm (first-occurrence ordering with incremental mapping) but differed significantly:

| Aspect | Conventional | PDD |
| --- | --- | --- |
| Existing approaches analyzed | 0 | 5 |
| Trade-off definition | Implicit | Formal (two conflicting requirements) |
| Proposal justification | "This is optimal" (assertion) | Elimination of 5 alternatives + invariant proof |
| Testable properties | 0 | 4 |
| Constraints disclosed | 1 | 3 |

Both approaches arrived at the same correct conclusion. The difference lies in the **verifiability and justification** of that conclusion.

## 5. Discussion

### 5.1 Why Paper Format Works: Three Hypotheses

We propose three non-mutually-exclusive hypotheses:

**H1: Training Data Quality Bias.** Academic papers undergo peer review and exhibit rigorous logical structure. LLMs trained on this data may activate higher-quality generation patterns when the output format matches paper conventions. However, training data composition is not publicly disclosed for most models, making this hypothesis difficult to verify directly.

**H2: Implicit Chain-of-Thought.** The paper structure enforces a reasoning sequence: problem definition → analysis of existing work → identification of the core difficulty → proposal → verification. This mirrors CoT prompting but is induced by format rather than explicit instruction. Wei et al. [1] demonstrated that such structured reasoning improves accuracy.

**H3: Persona Effect.** "Write a paper" implicitly sets the persona to "researcher," which activates behavioral patterns associated with academic rigor: systematic literature review, critical evaluation, formal definitions, and honest disclosure of limitations. This aligns with findings on role prompting [8].

The practical conclusion is the same regardless of which hypothesis is correct: in our case studies, the paper-format template was associated with higher-quality design analysis from LLMs.

### 5.2 Relationship to Format Constraint Research

The "Let Me Speak Freely?" study [2] found that strict format constraints (e.g., rigid JSON schemas) can degrade LLM reasoning by consuming cognitive capacity on format compliance. PDD's template is moderately structured: it specifies section topics but not sentence-level format. This may place PDD in the "sweet spot" of structural guidance—enough to direct reasoning without constraining it.

### 5.3 Limitations and Threats to Validity

- **Sample size (N=1)**: We demonstrate PDD on a single problem. Generalizability across domains is not yet established.
- **Hallucination risk**: LLMs may fabricate non-existent approaches or citations in §3. The template mitigates this by instructing the model to base analysis on known technologies and codebase facts, but does not eliminate the risk.
- **Confirmation bias**: The paper format may produce output that *appears* more rigorous without actually improving design quality. Controlled experiments measuring downstream implementation quality (bug rates, test coverage) are needed.
- **Model dependency**: Results may vary across LLMs. This study used Claude; reproducibility on GPT and Gemini is untested.
- **Evaluator bias**: The quality comparison in §4.3 was performed by the authors, not independent evaluators.

## 6. Related Work

**Spec-Driven Development.** Kiro (AWS) and GitHub Spec Kit [3, 4] structure requirements into specifications that guide LLM code generation. PDD complements SDD by addressing design rationale rather than requirements.

**Amazon Six-Pager / PR FAQ** [5]. Demonstrates that writing format affects thinking quality. PDD extends this principle to LLM-assisted technical analysis, adding critical evaluation of alternatives.

**RFC / ADR** [6]. Architecture Decision Records capture design decisions with context and consequences. PDD's §3 (existing approaches) and §7 (constraints) provide more structured analysis than typical ADR templates.

**Prompt Engineering** [1, 2, 8]. CoT, persona prompting, and format constraint research provide theoretical grounding for PDD's observed effects. PDD can be viewed as a domain-specific application of these techniques to software design analysis.

## 7. Future Work

1. **Controlled comparison experiments**: Compare output quality across (a) conventional prompting, (b) spec-driven format, and (c) paper format, using independent evaluators and defined quality metrics.
2. **Multi-domain validation**: Apply PDD to authentication design, performance optimization, data modeling, and other problem domains.
3. **Multi-model reproducibility**: Test PDD with GPT, Gemini, and other LLMs.
4. **Automated quality metrics**: Develop quantitative measures for design analysis quality (e.g., number of alternatives considered, specificity of limitations, testability of properties).
5. **Downstream impact**: Measure whether PDD-analyzed features exhibit lower bug rates or higher test coverage compared to conventionally designed features.

## 8. Conclusion

Paper-Driven Development suggests that instructing LLMs to produce design analysis in academic paper format is associated with improved output quality along four dimensions: exhaustiveness of alternatives, criticality of evaluation, formality of justification, and testability of properties. The methodology requires no model fine-tuning or special tooling—only a structured prompt template.

The key insight is that paper format does not help LLMs find better answers (both conventional and PDD prompting reached the same solution in our case study). Rather, it helps LLMs **justify and verify** their answers, producing analysis that is more reviewable, more testable, and more honest about its limitations.

PDD is available as an open-source Claude Code plugin at https://github.com/rema424/paper-driven-dev.

## References

[1] J. Wei et al., "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models," NeurIPS 2022. https://arxiv.org/abs/2201.11903

[2] Y. Tam et al., "Let Me Speak Freely? A Study on the Impact of Format Restrictions on Performance of Large Language Models," 2024. https://arxiv.org/abs/2408.02442

[3] Thoughtworks, "Spec-driven development: unpacking 2025's new engineering practices," 2025. https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices

[4] M. Fowler, "Spec-Driven Development Tools," 2025. https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html

[5] Six Pager Memo, "What Is an Amazon Six-Pager?" https://www.sixpagermemo.com/blog/what-is-an-amazon-six-pager

[6] M. Nygard, "Documenting Architecture Decisions," 2011. https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions

[7] Google Engineering Practices, "Design Documents." https://google.github.io/eng-practices/

[8] Learn Prompting, "Role Prompting." https://learnprompting.org/docs/advanced/zero_shot/role_prompting
