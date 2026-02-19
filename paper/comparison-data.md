# Quantitative Comparison Data: Three-Condition Experiment

> **実験条件**: Model: GPT-5.2 (via Codex) | N: 2 (CS1: citation rendering, CS2: session management) | Date: 2026-02 | Evaluator: 著者

## Methodology

- **Model**: GPT-5.2 (via Codex), February 2026
- **Prompt language**: Japanese
- **Three conditions**:
  - **A: Conventional** — 「この問題の設計分析と解決策を提案してください」
  - **B: Paper-format** — 「この問題について学術論文の形式で書いてください」（テンプレートなし）
  - **C: PDD template** — 「この問題について学術論文の形式で書いてください」+ §1–§7 テンプレートガイドライン
- **Measurement**: Manual counting by authors (automated metrics are future work)

### Experimental Design Rationale

3条件の比較により、以下の2つの効果を分離する:
- **B vs A**: 「論文形式で書いてください」という指示だけで出力品質が変わるか（論文形式の効果）
- **C vs B**: §1–§7 テンプレートがさらに品質を高めるか（テンプレートの追加効果）

詳細: `.internal/docs/discussion-2026-02-19-experiment-design.md`

### Line Counting Rules

- **Total lines**: LLM 出力部分の行数。メタデータヘッダーを除く。空行を含む。
- **空行の扱い**: 空行はセクション区切りとして存在するため Total lines に含めるが、「内容のある行」として個別にカウントする指標（e.g., existing approaches analyzed）には含めない。
- **プロンプト行の除外**: ユーザーの入力プロンプト自体はカウント対象外。LLM の出力のみをカウントする。
- **コードブロック**: コードブロック内の行も Total lines に含める。
- **再現性**: 各出力の原文は `docs/examples/cs{1,2}-{conventional,paper-format,pdd-template}.md` に保存されており、カウントの再現が可能。

> **注意**: 条件 A（Conventional）プロンプトは最適化していない。CoT やペルソナプロンプティング等を組み合わせた強化版プロンプトとの比較は将来課題である。

## Case Study 1: RAG Citation Renumbering

| Metric | A: Conventional | B: Paper-format | C: PDD Template |
| --- | ---: | ---: | ---: |
| **Total lines** | 58 | 96 | 137 |
| **Sections** | 5 (unstructured) | 7 (structured) | 7 (structured §1–§7) |
| **Existing approaches analyzed** | 0 | 0 | 4 |
| **Limitations per approach** | — | — | 1–2 each |
| **Conflicting requirements identified** | 0 (implicit) | 0 (implicit) | 2 (formal) |
| **Formal invariants/proofs** | 0 | 1 (prefix-determinability proof) | 1 (逐次確定可能性) |
| **Testable properties** | 0 | 0 | 6 |
| **Constraints/limitations disclosed** | 2 | 2 | 3 + 3 future work |
| **Code examples** | 0 | 0 | 0 |

### Correct conclusion reached?

All three: **Yes** — all identified first-occurrence body-order renumbering as the solution.

### Notable qualitative differences

- **B（Paper-format）** は独自に §4「正当性」セクションを生成し、prefix-determinability の数学的証明を含めた。これは A にも C にもない特徴。
- **C（PDD Template）** は §3 で4つの既存アプローチを体系的に列挙・評価し、§6 で6つの Given/When/Then 形式のテスト条件を定義した。

## Case Study 2: Multi-Tenant Session Management

| Metric | A: Conventional | B: Paper-format | C: PDD Template |
| --- | ---: | ---: | ---: |
| **Total lines** | 65 | 83 | 121 |
| **Sections** | 5 (unstructured) | 8 (structured) | 7 (structured §1–§7) |
| **Existing approaches analyzed** | 3 | 4 | 4 |
| **Limitations per approach** | 1 sentence each | 1 sentence each (table) | 1–2 sentences each |
| **Conflicting requirements identified** | 0 (implicit) | 0 (implicit) | 3 (formal) |
| **Formal invariants/proofs** | 0 | 0 | 0 |
| **Testable properties** | 0 | 0 | 7 |
| **Constraints/limitations disclosed** | 1 | 1 | 5 |
| **Code examples** | 0 | 0 | 0 |
| **Scope definition** | 0 | 0 | 1 (§1.3) |

### Correct conclusion reached?

All three: **Yes** — all recommended short-lived JWT + Redis session store + event-driven revocation.

### Notable qualitative differences

- **B（Paper-format）** は独自に要旨（Abstract）・キーワード・参考文献を生成。方式比較を表形式で整理。
- **C（PDD Template）** は §1.2 で3つの矛盾する要求を明示的に定義し、§6 で7つの検証可能な性質を Given/When/Then 形式で定義。§7 で5つの制約を詳述。

## Aggregate Summary (N=2)

| Metric | A: Conventional (avg) | B: Paper-format (avg) | C: PDD Template (avg) |
| --- | ---: | ---: | ---: |
| Total lines | 62 | 90 | 129 |
| Existing approaches analyzed | 1.5 | 2.0 | 4.0 |
| Conflicting requirements | 0 | 0 | 2.5 |
| Formal invariants/proofs | 0 | 0.5 | 0.5 |
| Testable properties | 0 | 0 | 6.5 |
| Constraints disclosed | 1.5 | 1.5 | 4.0 |

### Effect decomposition

| 効果 | 比較 | 観察 |
| --- | --- | --- |
| **論文形式の効果** | B vs A | 構造化（7-8セクション）、出力量 +45%、CS2 ではアプローチ分析が充実。ただし testable properties と conflicting requirements は A と同じ 0。 |
| **テンプレートの追加効果** | C vs B | testable properties（0 → 6.5）、conflicting requirements（0 → 2.5）、constraints（1.5 → 4.0）、既存アプローチ（2.0 → 4.0）が顕著に増加。 |

## Qualitative Observations

### 1. All three conditions reach the same conclusion

全3条件で、両ケーススタディとも本質的に同じ推奨解に到達した。条件間の差は「答えの正しさ」ではなく「答えの正当化と検証可能性」にある。

### 2. Paper format (B) adds structure but not systematic analysis

論文形式の指示だけで、出力は構造化（セクション分け、要旨、結論）される。CS1 では数学的証明が自発的に出現するなど、形式性が向上する場面もある。しかし、既存アプローチの体系的分析・矛盾する要求の形式的定義・テスト条件の定義は、テンプレートなしでは一貫して出現しない。

### 3. Template (C) uniquely elicits three behaviors

テンプレートによって一貫して引き出される3つの行動:
1. **矛盾する要求の形式的定義**（§1.2）: B では 0、C では 2.5（平均）
2. **検証可能な性質**（§6）: B では 0、C では 6.5（平均）
3. **制約の誠実な開示**（§7）: B では 1.5、C では 4.0（平均）

### 4. Paper format has its own unique contributions

論文形式（B）は、テンプレート（C）にはない独自の貢献も見せた:
- CS1: 数学的正当性の証明（§4 正当性）
- CS2: 要旨・キーワード・参考文献の自発的生成

### 5. Output length scales with structure: A < B < C

出力量は A（62行）< B（90行, 1.5x）< C（129行, 2.1x）。追加の長さは主に §3（既存アプローチ分析）、§6（テスト条件）、§7（制約）に集中しており、実用的価値の高いセクションである。

## Threats to Validity

1. **Small sample (N=2)**: Two case studies are insufficient for statistical conclusions
2. **Single model**: All outputs were generated by GPT-5.2. Results may differ across models
3. **Author evaluation**: All metrics were counted by the authors, not independent evaluators
4. **Problem selection bias**: Both problems were non-trivial design challenges where PDD is expected to perform well. Performance on simpler problems is untested
5. **Prompt optimization**: The conventional prompt (A) was not optimized (e.g., no CoT, no persona). A well-engineered conventional prompt might narrow the gap
6. **Language**: All prompts were in Japanese. Results may vary in English or other languages
7. **Single run**: Each condition was run once (no repetition). LLM output is non-deterministic; different runs might produce different results

---

## Supplementary: B-Variant Prompt Wording Experiment

> **実験条件**: Model: GPT-5.2 (via Codex) | N: 2 | Date: 2026-02 | Evaluator: 著者
> **注意**: CS2-B3 の原文はコンテキスト圧縮により失われたため、同一 Codex スレッドの継続で復元した。厳密には再生成の可能性がある。

### 目的

「論文形式で書いてください」（B1）と「論文を書いてください」（B2）・「学術論文を書いてください」（B3）のプロンプト文言の違いが出力品質に与える影響を調べる。仮説: 「論文を書く」という表現が LLM の研究者ペルソナを活性化し、「形式で書く」（フォーマット指示）より深い分析を引き出す可能性。

### 3条件の定義

| 条件 | プロンプト冒頭 | 仮説上の位置づけ |
|------|---------------|-----------------|
| **B1: Paper-format** | 「学術論文の**形式で**書いてください」 | フォーマット指示（企業人ペルソナ維持？） |
| **B2: Paper-write** | 「**論文を**書いてください」 | 論文執筆指示（研究者ペルソナ活性化？） |
| **B3: Academic-paper** | 「**学術論文を**書いてください」 | 学術論文執筆指示（最も強い研究者ペルソナ？） |

### CS1: RAG Citation Renumbering (B-variants)

| Metric | B1: Paper-format | B2: Paper-write | B3: Academic-paper |
| --- | ---: | ---: | ---: |
| **Total lines** | 96 | 86 | 98 |
| **Sections** | 7 (structured) | 7 (structured) | 8 (structured, w/ Keywords) |
| **Existing approaches analyzed** | 0 | 2 | 3 |
| **Conflicting requirements identified** | 0 (implicit) | 0 (implicit) | 0 (implicit) |
| **Formal invariants/proofs** | 1 (prefix-determinability) | 1 (prefix安定性) | 1 (Prefix安定性, formal def.) |
| **Testable properties** | 0 | 0 | 0 |
| **Evaluation metrics defined** | 0 | 0 | 4 (§7) |
| **Constraints/limitations disclosed** | 2 | 2 | 2 |
| **Keywords** | No | No | Yes |
| **References** | No | No | No |

#### Notable qualitative differences (CS1)

- **B2** は R1–R4 の形式的要件定義を自発的に生成。B1 にはない特徴。
- **B3** は Prefix安定性の数学的定義（時刻 t、プレフィックス B_≤t の記法）を導入。さらに §7「評価指標と実験計画」で4つの計測可能な指標を定義。これは B1・B2 にない独自の貢献。
- **B3** は3つの代替方式（プレースホルダ＋再描画、二段階生成、構造化セグメント列）を分析。B2 は2つ、B1 は0。

### CS2: Multi-Tenant Session Management (B-variants)

| Metric | B1: Paper-format | B2: Paper-write | B3: Academic-paper |
| --- | ---: | ---: | ---: |
| **Total lines** | 83 | 117 | 109 |
| **Sections** | 8 (structured) | 8 (structured) | 9 (structured, w/ Keywords/Refs) |
| **Existing approaches analyzed** | 4 | 3 | 4 |
| **Conflicting requirements identified** | 0 (implicit) | 0 (implicit) | 0 (implicit) |
| **Formal invariants/proofs** | 0 | 0 | 0 |
| **Testable properties** | 0 | 0 | 0 |
| **Constraints/limitations disclosed** | 1 | 1 | 1 |
| **Formalized requirements (R1-R4)** | No | Yes (§2) | Yes (§2, R1-R4) |
| **Comparison table** | Yes (§3) | No | Yes (§4) |
| **Keywords** | Yes | No | Yes |
| **References** | Yes (3) | No | Yes (4) |

#### Notable qualitative differences (CS2)

- **B2** は B1 より 41% 長い出力（117 vs 83行）。推奨方式を5つのサブセクション（4.1–4.5）で詳述し、マルチテナント固有の注意点を独立セクション化。
- **B3** は要件を R1–R4 として形式化し、4方式の比較評価表を生成。参考文献4件（RFC 3件 + OWASP）を含む。
- **B2** は3方式のみ比較（B1・B3 は4方式）。ただし各方式の分析深度は B2 が最も詳細。

### Aggregate B-Variant Summary (N=2)

| Metric | B1 (avg) | B2 (avg) | B3 (avg) | C (avg, ref) |
| --- | ---: | ---: | ---: | ---: |
| Total lines | 90 | 102 | 104 | 129 |
| Existing approaches analyzed | 2.0 | 2.5 | 3.5 | 4.0 |
| Conflicting requirements | 0 | 0 | 0 | **2.5** |
| Formal invariants/proofs | 0.5 | 0.5 | 0.5 | 0.5 |
| Testable properties | 0 | 0 | 0 | **6.5** |
| Constraints disclosed | 1.5 | 1.5 | 1.5 | 4.0 |

### Key findings

1. **Conflicting requirements と testable properties は全 B バリアントで 0**。プロンプト文言を「形式で書いて」から「論文を書いて」「学術論文を書いて」に変えても、これらの行動は引き出されなかった。C（PDD テンプレート）のみがこれらを一貫して引き出す。

2. **プロンプト文言による段階的改善は存在する**。B1 → B2 → B3 の順で以下の傾向:
   - 出力量: B1(90) < B2(102) < B3(104)
   - 既存アプローチ分析: B1(2.0) < B2(2.5) < B3(3.5)
   - 学術的慣行（Keywords, References, 要件形式化）: B3 が最も充実

3. **B3 固有の貢献**: CS1 で「評価指標と実験計画」セクション（4つの計測指標）を自発生成。これは Given/When/Then 形式ではないが、検証可能な基準を定義している点で注目に値する。

4. **2種類の効果の分離**:
   - **ペルソナ/フレーミング効果**（B1→B3）: 形式性・分析深度・学術的慣行が段階的に向上
   - **テンプレート/チェックリスト効果**（B→C）: conflicting requirements と testable properties が質的に飛躍
   - 両効果は異なる次元で作用しており、ペルソナ効果だけでは C の行動を引き出せない

5. **ペルソナ仮説への含意**: 「論文を書いて」がLLMの研究者ペルソナを部分的に活性化する証拠はある（より学術的な出力）。しかし、研究者ペルソナだけでは「矛盾する要求の明示的定義」「検証可能な性質の列挙」には至らない。これらは研究者の「態度」ではなく、テンプレートによる「行動の具体的指示」によって引き出される。

原文: `docs/examples/cs{1,2}-{paper-format,paper-write,academic-paper}.md`

---

## Supplementary: o3 Two-Condition Comparison (Historical)

> **実験条件**: Model: OpenAI o3 (via Codex) | N: 2 | Date: 2026-02 | Evaluator: 著者
> **注意**: 以下は GPT-5.2 3条件比較以前の2条件比較データ。参考として残す。

### CS1: RAG Citation Renumbering (o3)

| Metric | Conventional | PDD | Delta |
| --- | ---: | ---: | ---: |
| **Total lines** | 40 | 269 | +229 (5.7x) |
| **Sections** | 4 (unstructured) | 7 (structured §1–§7) | +3 |
| **Existing approaches analyzed** | 0 | 5 | +5 |
| **Limitations per approach** | — | 1–2 each | — |
| **Conflicting requirements identified** | 0 (implicit) | 2 (formal) | +2 |
| **Formal invariants defined** | 0 | 1 (Append-Only) | +1 |
| **Testable properties** | 0 | 4 | +4 |
| **Constraints/limitations disclosed** | 1 | 3 | +2 |
| **Code examples** | 1 (algorithm) | 2 (algorithm + usage) | +1 |

### CS2: Multi-Tenant Session Management (o3)

| Metric | Conventional | PDD | Delta |
| --- | ---: | ---: | ---: |
| **Total lines** | 38 | 142 | +104 (3.7x) |
| **Sections** | 4 (unstructured) | 7 (structured §1–§7) | +3 |
| **Existing approaches analyzed** | 3 (comparison table) | 4 (detailed analysis) | +1 |
| **Limitations per approach** | 1 sentence each | 1–2 sentences each | deeper |
| **Conflicting requirements identified** | 0 (implicit) | 3 (formal) | +3 |
| **Formal invariants defined** | 0 | 1 (Versioned Session Authority) | +1 |
| **Testable properties** | 0 | 7 | +7 |
| **Constraints/limitations disclosed** | 0 | 3 + future work | +3 |

### Cross-model observation

o3（2条件）と GPT-5.2（3条件）の結果は、以下の点で共通のパターンを示す:
- 全条件で同一の正しい結論に到達
- Conventional → PDD で testable properties が 0 から大幅増加
- Conventional → PDD で conflicting requirements が 0 から増加
- PDD 出力が Conventional の 2-6 倍の長さ

原文: `docs/examples/citation-rendering-before.md`, `citation-rendering.md`, `session-management-before.md`, `session-management.md`
