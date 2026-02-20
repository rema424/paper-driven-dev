# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Paper-Driven Development (PDD) is both a **research paper** and a **Claude Code plugin** in the same repository. The paper analyzes PDD methodology; the plugin implements it. This self-referential structure is intentional—do not separate them.

- **Paper**: `paper/paper-driven-dev.md` (main paper), `paper/comparison-data.md` (quantitative data), `paper/protocol-v1.md` (experimental protocol)
- **Plugin**: `skills/article/SKILL.md` (skill definition), `.claude-plugin/plugin.json` (plugin metadata)
- **Experiments**: `docs/examples/fullpaper/` (4 conditions × 2 case studies)
- **Audits**: `audits/` (pre-submission internal reviews by Claude Code and Codex)

## No Build System

This is a document-driven project. There is no package.json, Makefile, or test runner. Quality assurance is done through git history review, inter-rater agreement metrics, and audit documents.

## Git Commit Conventions

Commit message format: `type: 日本語説明`

| Type | Use |
|------|-----|
| `paper:` | Paper content changes |
| `data:` | Quantitative data/figures |
| `review:` | Reviewer comment responses |
| `audit:` | Internal audit artifacts |
| `docs:` | Non-paper documentation |
| `feat:` / `fix:` | Plugin code changes |
| `refactor:` | Structure-only changes (no behavior change) |
| `build:` / `chore:` | Config, tooling, housekeeping |

Section references use `S1`, `S3.2`. Reviewer comments use `R1-C3` (Reviewer 1, Comment 3).

**Tidy First**: Always separate structural changes (`refactor:`) from content changes (`paper:`, `data:`, etc.) into distinct commits. Never mix them.

## Branch Strategy

Work on `main` unless protecting a submitted version. Create `revision/vN` branches only after receiving reviewer feedback on a submitted paper. Use `--no-ff` merges to preserve revision boundaries in `git log --graph`.

## Tagging

- `vN-draft` — internal review milestone
- `vN-submitted` — paper submission (annotated tag with venue/date/authors)
- `vN-reviews` — reviewer feedback received (lightweight)
- `vN-accepted` — camera-ready version (annotated)

## Key Commands

```bash
# Paper-only history
git log --oneline --grep='^paper:\|^data:\|^review:'

# Plugin-only history
git log --oneline --grep='^feat:\|^fix:\|^build:'

# Track reviewer comment responses
git log --oneline --grep='R1-C1'

# Run the plugin locally
claude --plugin-dir ./paper-driven-dev
```

## Language

- Paper and documentation: 日本語
- Skill definitions and code: English
- Commit messages: English type prefix + Japanese description

## Current Phase

Phase 2 (フルペーパー化): expanding from workshop paper to full journal paper with additional experimental conditions and multi-model validation. See `.internal/roadmap.md` for detailed roadmap.
