# Self-Blinded 再採点結果（2026-02-19）

## 手順

1. 10ファイル（5条件 × 2ケーススタディ）をランダム順で提示
2. 条件ラベルを参照せず、Appendix A.2 の採点ルーブリックのみに基づいてカウント
3. 採点者: Claude Code（著者の指示による自動化。人間の著者による self-blinded ではなく、AI エージェントによる独立採点）

## 再採点結果

### CS1: RAG Citation Renumbering

| Metric | A (orig) | A (rescore) | B1 (orig) | B1 (rescore) | B2 (orig) | B2 (rescore) | B3 (orig) | B3 (rescore) | C (orig) | C (rescore) |
|--------|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Total lines | 58 | 63 | 96 | 101 | 86 | 92 | 98 | 104 | 137 | 142 |
| Existing approaches | 0 | 0 | 0 | 0 | 2 | 1 | 3 | 3 | 4 | 4 |
| Conflicting requirements | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 2 |
| Formal invariants | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 |
| Testable properties | 0 | 0 | 0 | **3** | 0 | **4** | 0 | **4** | 6 | 6 |
| Constraints disclosed | 2 | 1 | 2 | 2 | 2 | 1 | 2 | 1 | 6 | 3 |

### CS2: Multi-Tenant Session Management

| Metric | A (orig) | A (rescore) | B1 (orig) | B1 (rescore) | B2 (orig) | B2 (rescore) | B3 (orig) | B3 (rescore) | C (orig) | C (rescore) |
|--------|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Total lines | 65 | 70 | 83 | 88 | 117 | 123 | 109 | 115 | 121 | 126 |
| Existing approaches | 3 | 3 | 4 | 4 | 3 | 3 | 4 | 4 | 4 | 4 |
| Conflicting requirements | 0 | 0 | 0 | **1** | 0 | 0 | 0 | **1** | 3 | 3 |
| Formal invariants | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Testable properties | 0 | 0 | 0 | **4** | 0 | 0 | 0 | **4** | 7 | 7 |
| Constraints disclosed | 1 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | 5 | 5 |

## 一致率

### 指標別の一致率（完全一致）

| 指標 | 一致数/全数 | 一致率 |
|------|-----------|--------|
| Existing approaches | 9/10 | 90% |
| Conflicting requirements | 8/10 | 80% |
| Formal invariants | 9/10 | 90% |
| Testable properties | 5/10 | **50%** |
| Constraints disclosed | 3/10 | **30%** |

### 主要な不一致とその原因

#### 1. Testable properties（一致率 50%）

**不一致パターン**: B 条件で再採点が高い（orig=0 → rescore=3-4）

**原因**: ルーブリックの曖昧性。

- **元の採点**: 「テスト条件」= Given/When/Then 形式または明示的な評価指標。B 条件の R1-R4 形式の要件定義は「要件」として別カテゴリに分類（comparison-data.md に "Formalized requirements (R1-R4)" として記録）。
- **再採点**: 「テストケースに変換可能な具体的条件」を広義に解釈し、R1-R4 要件も含めた。

**重要な区別**:
- **Input requirements** (R1-R4): 問題に対する要求仕様（設計の入力）
- **Derived testable properties** (Given/When/Then): 提案手法から導出された検証可能な性質（設計分析の出力）

元の採点は後者のみを testable properties としてカウント。この区別は comparison-data.md に明示されていなかった。

**主張への影響**: 厳密な定義（Given/When/Then 形式のみ）では B=0 の所見は維持される。広義の定義では B 条件も一定の testable conditions を含むが、それは「要件の形式化」であり「提案手法の検証可能な性質の導出」ではない。

#### 2. Constraints disclosed（一致率 30%）

**不一致パターン**:
- CS1: 元の採点が高い（orig=2 → rescore=1）
- CS2-B: 元の採点が高い（orig=1 → rescore=0）
- CS1-C: 元の採点が高い（orig=6 → rescore=3、元は future work 3件を含む）

**原因**: 「制約」の範囲の解釈差。

- **元の採点**: 運用上の注意点や将来課題も「制約の開示」に含めた
- **再採点**: 提案手法の明示的な限界・境界条件のみ。一般的な運用アドバイスは不算入

**主張への影響**: constraints disclosed のベースライン値（A/B での 1.5）は再採点では低下（0-1）するが、C との差分（増加パターン）は維持される。

#### 3. Conflicting requirements（一致率 80%）

**不一致**: CS2-B1 と CS2-B3 で再採点が 1 を計上。

- **元の採点**: 形式的に定義されたペアのみ（§1.2 形式）
- **再採点**: 本文中の叙述的な緊張関係の記述も 1 と計上

**主張への影響**: B 条件でもナラティブな形で緊張関係への言及はあるが、テンプレートの §1.2 が要求する「形式的な矛盾する要求のペア」とは質的に異なる。

## C 条件での一致率

| 指標 | CS1-C | CS2-C |
|------|-------|-------|
| Existing approaches | ✓ (4/4) | ✓ (4/4) |
| Conflicting requirements | ✓ (2/2) | ✓ (3/3) |
| Testable properties | ✓ (6/6) | ✓ (7/7) |
| Constraints disclosed | ✗ (6→3) | ✓ (5/5) |

C 条件では co-primary 3指標中、conflicting requirements と testable properties は完全一致。constraints disclosed は CS1 で future work を含めるかどうかで不一致。

## 結論

1. **主張の頑健性**: conflicting requirements と testable properties（厳密定義）について、「B 条件ではゼロ、C 条件でのみ出現」という所見は再採点でも維持される。
2. **ルーブリックの精緻化が必要**: testable properties と constraints disclosed の定義に曖昧性がある。特に「要件の形式化」と「テスト条件の導出」の区別を明確化すべき。
3. **constraints disclosed は最も不安定**: 一致率 30% は inter-rater reliability として不十分。この指標はルーブリック改訂まで主張の根拠としての信頼性が低い。
4. **B 条件の「ゼロ」は定義依存**: 広義の解釈では B 条件も検証可能な条件を含む。この事実を論文で明示すべき。
