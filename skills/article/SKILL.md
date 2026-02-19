---
description: Generate a design analysis document in academic paper format
disable-model-invocation: true
---

# Paper-Driven Development: Design Analysis

You are a senior software engineer writing a **design analysis document in academic paper format**. This format elicits systematic, high-quality analysis by structuring your reasoning as a research paper.

## Problem

$ARGUMENTS

## Instructions

1. If a `research.md` file exists in the current directory or `.claude/plans/`, read it first and use it as input context.
2. Write the analysis following the template structure below.
3. Save the output as `article.md` in the current directory.

## Template Structure

Write the document using the following structure. Each section is mandatory.

```
## 1. 問題定義
  ### 1.1 背景
  ### 1.2 矛盾する要求（対立するトレードオフ）
  ### 1.3 本文書の範囲

## 2. 現状のアーキテクチャと制約

## 3. 既存アプローチとその限界
  ### 3.N アプローチ N: [名前]
    手法 / 利点 / 限界

## 4. 問題の本質

## 5. 提案手法
  ### 5.1 基本原理
  ### 5.2 実装アーキテクチャ

## 6. 検証可能な性質

## 7. 制約と今後の課題
```

## Section Guidelines

### §1 問題定義
- §1.2 must identify **at least two conflicting requirements** (trade-offs). If only one side exists, the problem is trivial and does not need this analysis.

### §2 現状のアーキテクチャと制約
- Describe the current system architecture based on **actual code and configuration in the codebase**. Do not invent or assume architecture that does not exist.

### §3 既存アプローチとその限界
- List **at least 3 approaches** from established techniques, libraries, or patterns.
- For each approach: describe the method, its advantages, and its **specific limitations** for this problem.
- Base analysis on **known technologies and facts**. Do not fabricate approaches or citations.

### §4 問題の本質
- Distill the core difficulty. Why do existing approaches fall short? What fundamental constraint makes this problem hard?

### §5 提案手法
- The proposal must address the trade-offs identified in §1.2.
- §5.2 should be concrete enough to implement (data structures, algorithms, component interactions).

### §6 検証可能な性質
- Define **testable properties** as concrete test conditions, not vague quality attributes.
- Each property should be expressible as: "Given [precondition], when [action], then [expected result]."
- These properties will be used to derive test cases in the implementation phase.

### §7 制約と今後の課題
- Be honest about limitations, assumptions, and unresolved questions.

## Quality Checklist

Before finalizing, verify:
- [ ] §1.2 contains genuinely conflicting requirements (not just a wish list)
- [ ] §3 approaches are based on real, verifiable technologies
- [ ] §5 proposal addresses the trade-offs from §1.2
- [ ] §6 properties are concrete and testable (Given/When/Then format)
- [ ] No section is left as a placeholder or single sentence
