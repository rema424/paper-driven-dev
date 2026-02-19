# 議論: 3条件比較実験の結果解釈と論文主張の再構成（2026-02-19）

## 発端

3条件比較実験（A: Conventional, B: Paper-format, C: PDD Template）の結果が出揃い、論文の主張をどう再構成すべきかを CC×Codex で構造化議論した。

## 問いの本質（Codex 定義）

> 3条件比較（A/B/C）で分離された「論文形式の指示」と「PDDテンプレート」の寄与を、観測された行動指標（例：testable properties、conflicting requirements 等）に整合し因果的に解釈可能な形で、論文の中心主張としてどう再定義すべきか。

## 実験結果（GPT-5.2, N=2）

### 集計（平均値）

| Metric | A: Conventional | B: Paper-format | C: PDD Template |
| --- | ---: | ---: | ---: |
| Total lines | 62 | 90 | 129 |
| Existing approaches | 1.5 | 2.0 | 4.0 |
| Conflicting requirements | 0 | 0 | 2.5 |
| Formal invariants/proofs | 0 | 0.5 | 0.5 |
| Testable properties | 0 | 0 | 6.5 |
| Constraints disclosed | 1.5 | 1.5 | 4.0 |

### 定性的観察

- 全3条件で同一の正しい結論に到達
- B は A より構造化されるが、testable properties と conflicting requirements は A と同じ 0
- C のみが testable properties (6.5) と conflicting requirements (2.5) を一貫して引き出す
- B は独自に数学的証明（CS1）や参考文献（CS2）を自発的に生成

## 初期立場

### CC の初期立場

論文の主張を「2層モデル」として再構成すべき。

- 第1層: 論文形式の効果（B vs A）— 構造化・形式性の向上。ただし testable properties/conflicting requirements は変化なし。
- 第2層: テンプレートの効果（C vs B）— 3つの行動を一貫して引き出す。
- 因果的主張は N=2 では不可能。「is associated with」レベルに留める。
- 懸念: B の定量的効果が A に近い指標が多く、「第1層」の定量的根拠が弱い。

### Codex の初期立場

効果の本体は「論文形式」ではなく「PDDテンプレート（行動チェックリスト）」にある。

- 4行動の再割当て: テンプレート起因 = exhaustive survey, critical evaluation, testable properties / 論文形式起因 = formal justification
- 3条件比較を「アブレーション（分解実験）」として前面に出す
- 限定主張に絞り、次段の検証を必須の追試として位置付ける

## 批評（Codex 主導）

### 合意点

- 3条件比較は2条件より交絡の分離が改善
- B は testable properties と conflicting requirements を増やさない（0 のまま）
- C のみがこれらを大きく押し上げている
- N=2 なので主張強度は抑えるべき

### 相違点

- 論文形式の位置づけ（CC: 独立した第1層 / Codex: 主要効果ではない）
- 4行動への態度（CC: 3つに絞り直す / Codex: 帰属を再配分）
- 主貢献の描き方（CC: 2層並立 / Codex: テンプレート効果の同定が主貢献）

### 批評の要点

- **CC の弱点**: 「論文形式は構造化を改善」は現メトリクスでは直接測れていない。定性的所見に依存。
- **Codex の弱点**: B の独自産物（証明・参考文献）を「価値なし」とみなす根拠が未提示。formal invariants/proofs が B と C で同程度（0.5）であり、帰属もデータ上は決め手に欠ける。
- **共通の弱点**: 指標が「プロンプトで要求された産物の有無」を強く反映し得る（構成概念妥当性が未確立）。

### 解決すべき論点

1. 何をアウトカムと呼ぶか
2. 指標の妥当性（テンプレートのセクション要求との直接対応 = トートロジー問題）
3. D条件の欠落（テンプレートのみ・論文形式なし）
4. 行数増加と項目数増加の交絡（正規化の必要性）
5. 評価信頼性（author evaluation のバイアス）

## CC の修正立場

Codex 案に寄せ、以下に修正:

- **主貢献**: テンプレートが testable properties・conflicting requirements・constraints を一貫して引き出す
- **副次的観察**: 論文形式指示のみでも構造化と一部の形式的行動が観察される
- **正直な限界**: 指標の多くはテンプレートのセクション要求と直接対応しており、「テンプレートの効果」と「指示に従っただけ」の区別は本実験では不可能

4行動を 3+1 に修正:
- 主要3行動: conflicting requirements, testable properties, constraints disclosure
- 関連指標1つ: exhaustive survey (approaches)

## 最終合意

### 論文の新しい中心主張（1文）

GPT-5.2・N=2 のケーススタディにおいて、PDD テンプレートの使用は（論文形式指示のみでは増えなかった）conflicting requirements・testable properties・constraints disclosure の出現と、関連指標としての approaches 増加に関連していた。

### 各セクションの改訂方針

| セクション | 方針 |
|-----------|------|
| **S1** | 主貢献 = テンプレートと主要3行動の「出現の関連」。論文形式は副次的観察。言い切りは "associated with" に統一 |
| **S4** | 3条件比較をアブレーションとして前面化。3+1 アウトカム定義と採点手続きを明示 |
| **S5** | (1) トートロジー/構成概念妥当性、(2) D条件欠落、(3) 小標本・single-run・author evaluation、(4) 出力量の交絡を明示。論文形式の効果は「観察」に留める |
| **S7** | Future Work に D条件（論文形式なしチェックリスト）、反復・盲検評価・正規化等を列挙 |
| **S8** | 限定主張に収束。一般化・因果・機序確定を避け、追試の必要性を強調 |

### 主張の上限（言い切ってはいけないこと）

- 「テンプレートが因果的に改善した／強制した」
- 「設計分析"品質"が向上した」
- N=2 で「有意差」「効果が実証された」
- 「4行動すべてがテンプレートで構造的に引き出される」

### 正直に認めるべき限界

- N=2、single-run、author evaluation（再現性・評価者バイアス）
- 指標がテンプレートのセクション要求と直結（構成概念妥当性の限界）
- D条件（論文形式なしのチェックリスト）の欠落
- 出力量（行数）増加の交絡、モデル依存（GPT-5.2 のみ）、生成された証明/参考文献の正確性未検証

### 表現ルール

- 「有意な差」は N=2 では統計検定を示唆するため使用しない
- 代わりに「明確な増加は観察されなかった」「定量差は小さかった」等を使用
- 主張の動詞は "was associated with" に統一（"elicits", "improves", "demonstrates" は不可）
