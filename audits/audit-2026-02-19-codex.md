# 論文成果物 監査ノート（2026-02-19）

## Round 1: 初回監査

### 監査対象
- `README.md`
- `docs/guide.md`
- `docs/note/article-draft.md`
- `docs/examples/citation-rendering.md`
- `docs/examples/citation-rendering-before.md`
- `docs/examples/citation-rendering-comparison.md`
- `docs/examples/session-management.md`
- `docs/examples/session-management-before.md`
- `paper/paper-driven-dev.md`
- `paper/comparison-data.md`
- `skills/article/SKILL.md`

### 初回所見（優先度順）
1. **高: 実験条件・サンプル数の記述が文書間で不整合**
   - `paper/paper-driven-dev.md` では N=1 / Claude 前提。
   - `paper/comparison-data.md` では N=2 / OpenAI o3 前提。
   - `docs/note/article-draft.md` も N=1 表記。
   - 再現性・信頼性の評価軸が揺れるため、対外説明で重大な混乱を招く。

2. **高: 主張の強さとエビデンスの強さが釣り合っていない**
   - `README.md` と `docs/guide.md` の冒頭は「劇的に上がる」「自然に出現」と強い断定。
   - 一方で `paper/paper-driven-dev.md` / `paper/comparison-data.md` では小標本・著者評価バイアスを認める。
   - 現状は「効果の示唆」より強いマーケティング表現が先行している。

3. **中: 定量比較の測定定義が不明瞭**
   - 「総行数」「セクション数」等のカウント基準（見出し・引用・プロンプト部分を含むか）が明示されていない。
   - 実ファイル行数との対応が読み手に追跡しづらい。

4. **中: テンプレート運用ルールとの整合に揺れ**
   - `skills/article/SKILL.md` は §6 を Given/When/Then 形式で要求。
   - `docs/examples/citation-rendering.md` の §6 は性質列挙中心で、形式遵守が不完全。
   - サンプルが「ルール準拠例」として弱い。

5. **中: 参考文献の強度にばらつき**
   - `paper/paper-driven-dev.md` の関連研究で、査読論文とブログ系ソースが混在。
   - 主張の性質に対して一次文献が不足する箇所がある。

6. **中: ロードマップの鮮度低下**
   - `README.md` の「今後の計画」に、すでに実施済みに見える項目が残っている。
   - 現状とのギャップが運用成熟度の印象を下げる。

### Round 2での深掘り予定
- 各不整合の「具体的な行番号根拠」を付与する。
- 各指摘がどの監査観点（論旨・根拠対応・用語統一・引用整合・文書間整合）に該当するかを明示する。
- 改善優先度（即時修正 / 次版修正 / 将来課題）を再分類する。

## Round 2: 深掘り

### 指摘1（高）実験条件・サンプル数の不整合
- 監査観点: **文書間整合性 / 主張と根拠の対応**
- 根拠:
  - `paper/paper-driven-dev.md:170` に「Sample size (N=1)」
  - `paper/paper-driven-dev.md:173` に「This study used Claude」
  - `paper/comparison-data.md:5` に「Model: OpenAI o3 (via Codex)」
  - `paper/comparison-data.md:50` に「Aggregate Summary (N=2)」
  - `docs/note/article-draft.md:128` と `docs/note/article-draft.md:139` に N=1 記述
- 深掘り評価:
  - 同一プロジェクトで「研究本文」「比較データ」「解説記事」が同時公開される構成のため、読み手は単一の実証セットと解釈しやすい。
  - 実験条件（モデル・標本数）が不一致だと、結論の適用範囲を誤認させるリスクが高い。
- 仮優先度: **即時修正**

### 指摘2（高）主張強度と証拠強度のミスマッチ
- 監査観点: **論旨の一貫性 / 主張と根拠の対応**
- 根拠:
  - `README.md:3` 「品質が劇的に上がる」
  - `README.md:5` 「指示しなくても自然に出現」
  - `docs/guide.md:7` 「指示しなくても自然に出現」
  - 一方で `paper/paper-driven-dev.md:170-174` は N=1・評価者バイアス・モデル依存を明示
  - `paper/comparison-data.md:84-89` でも小標本・単一モデル・著者評価を明示
- 深掘り評価:
  - 研究的慎重さとトップページ表現の温度差が大きく、査読・導入検討時に「誇大表現」と受け取られる可能性がある。
- 仮優先度: **即時修正**

### 指摘3（中）定量比較の測定定義が曖昧
- 監査観点: **主張と根拠の対応 / 図表・例示の適切性**
- 根拠:
  - `paper/comparison-data.md:9` に「Manual counting by authors」
  - `paper/comparison-data.md:15` で Case1 行数を 40 / 269 と記載
  - `paper/comparison-data.md:35` で Case2 行数を 38 / 142 と記載
  - 実ファイルの総行数は `docs/examples/citation-rendering-before.md=67`, `docs/examples/citation-rendering.md=273`, `docs/examples/session-management-before.md=60`, `docs/examples/session-management.md=157`
  - `docs/examples/citation-rendering-comparison.md:14` でも「約40行 / 約270行」と近似表現
- 深掘り評価:
  - 「本文のみ」「ヘッダ除外」等の集計ルールを別紙化していないため、第三者が再計算しにくい。
  - 値自体が必ずしも誤りとは断定できないが、検証可能性が不足している。
- 仮優先度: **次版修正**

### 指摘4（中）テンプレート準拠の揺れ（§6）
- 監査観点: **用語・表記の統一性 / 主張と根拠の対応**
- 根拠:
  - `skills/article/SKILL.md:67-70` で Given/When/Then 形式を要件化
  - `skills/article/SKILL.md:81` でチェックリストにも明記
  - `docs/examples/session-management.md:121-139` は要件に準拠
  - `docs/examples/citation-rendering.md:250-260` は定義文中心で Given/When/Then が明示されない
- 深掘り評価:
  - サンプル間で記述規約が揃っておらず、利用者が期待する出力品質の基準が曖昧になる。
- 仮優先度: **次版修正**

### 指摘5（中）参考文献ソース強度の混在
- 監査観点: **引用・参考文献の整合性**
- 根拠:
  - `paper/paper-driven-dev.md:204-218` の参考文献に、査読論文（[1][2]）とブログ/実務サイト（[3][4][5][8]）が混在
  - 特に `paper/paper-driven-dev.md:212`（Six Pager Memo）と `paper/paper-driven-dev.md:218`（Learn Prompting）は一次学術根拠としては弱い
- 深掘り評価:
  - 実務文書としては許容範囲だが、「学術論文」体裁での主張補強としては根拠階層の説明が必要。
- 仮優先度: **次版修正**

### 指摘6（中）ロードマップの鮮度低下
- 監査観点: **文書間整合性**
- 根拠:
  - `README.md:64-67` に今後計画として「異なるドメインサンプル追加」「定量比較」「学術論文ドラフト」
  - 既に `docs/examples/session-management.md`（別ドメイン）と `paper/comparison-data.md`（定量比較）と `docs/note/article-draft.md`（ドラフト）が存在
- 深掘り評価:
  - 「完了済み項目」と「未着手項目」が同列で管理され、進捗の透明性が低い。
- 仮優先度: **次版修正**

### 深掘り時点の暫定アクション分類
- 即時修正:
  - 指摘1 実験条件・サンプル数の統一
  - 指摘2 冒頭メッセージの主張強度調整
- 次版修正:
  - 指摘3 測定定義の明文化
  - 指摘4 §6記法の統一
  - 指摘5 参考文献レイヤの明示
  - 指摘6 ロードマップ更新方式の改訂

## Round 3: 再評価

### 再評価方針
- 「不整合」か「文脈差（別時点・別目的）」かを分離して判定した。
- 直ちに信頼性を損なう項目を P1、改善効果が高い運用品質項目を P2、体裁最適化を P3 とした。

### 指摘別の再判定
1. 指摘1（実験条件・サンプル数）
   - 再判定: **妥当（P1）**
   - 理由: 別実験である可能性はあるが、現状は文書側で実験境界（時点/モデル/対象）を明示していない。読み手は単一実験セットと解釈しやすい。
   - 追加提案: 「Experiment A/B」や「as of YYYY-MM-DD」のメタ情報を各文書冒頭に付与。

2. 指摘2（主張強度と証拠強度）
   - 再判定: **妥当（P1）**
   - 理由: マーケティング文としては成立するが、同一リポジトリ内に研究的制約が併記されるため、断定口調は誤解誘発リスクが高い。
   - 追加提案: 「観測上」「現時点のケーススタディでは」等の限定句を冒頭に追加。

3. 指摘3（測定定義の曖昧さ）
   - 再判定: **妥当（P2）**
   - 理由: 数値は概ね整合するが、再計算手順がないため第三者検証性が不足。主張の再現性観点で改善余地が大きい。
   - 追加提案: 集計ルール（空行除外、プロンプト除外、見出し含有可否）を `paper/comparison-data.md` に明記。

4. 指摘4（§6 記法の揺れ）
   - 再判定: **妥当（P2）**
   - 理由: 出力品質の本質を損なう重大欠陥ではないが、「スキル規約どおりに生成される」という訴求の説得力を下げる。
   - 追加提案: `docs/examples/citation-rendering.md` の §6 を Given/When/Then に寄せるか、スキル要件側で許容形式を明文化。

5. 指摘5（参考文献強度の混在）
   - 再判定: **部分妥当（P3）**
   - 理由: 実務提案文書としては許容範囲。問題は「どの主張が学術根拠で、どこが実務知見か」の区別が薄い点。
   - 追加提案: 参考文献を「学術」「実務ブログ」「解説資料」に区分。

6. 指摘6（ロードマップ鮮度）
   - 再判定: **妥当（P2）**
   - 理由: 内容不整合というより運用透明性の課題。導入判断時の信頼感に影響する。
   - 追加提案: チェックボックス更新か、`Planned / In Progress / Done` の3状態管理へ変更。

### 再評価後の優先順位
- **P1（最優先）**
  - 指摘1 実験境界の明示不足（モデル・N・時点）
  - 指摘2 断定的メッセージの過強化
- **P2（中優先）**
  - 指摘3 定量比較の測定プロトコル欠落
  - 指摘4 §6 記法統一の不足
  - 指摘6 ロードマップ更新管理
- **P3（低優先）**
  - 指摘5 参考文献レイヤ区分の不足

## Round 4: 最終確認

### 総点検結果
- 主要な見落としは確認されなかった。
- ただし、以下の2点は対外信頼性に直結するため、最終的にも最優先で修正すべきと判断:
  - 実験条件の文書間不整合（N・モデル・時点）
  - 冒頭メッセージの断定強度と実証強度の乖離

### 最終結論（査定）
- **全体評価: B-（内容は有用だが、実証記述の統制が弱い）**
- 良い点:
  - 問題設定と提案テンプレートは再利用性が高い
  - サンプル（RAG/認証）で適用幅を示せている
  - 限界を明示する姿勢は維持されている
- 改善必須点:
  - 実験メタ情報（モデル、サンプル数、実施日、評価者）を文書単位で明記し、同一基準で横断比較できる状態にする
  - 強い断定表現を「観測ベースの主張」に調整する

### 推奨アクション（実行順）
1. **メタ情報の統一テンプレート化（P1）**
   - 対象: `paper/paper-driven-dev.md`, `paper/comparison-data.md`, `docs/note/article-draft.md`
   - 追加項目: `Model`, `N`, `Language`, `Date`, `Evaluator`, `Counting Rule`

2. **トップメッセージの語調調整（P1）**
   - 対象: `README.md`, `docs/guide.md`, `docs/note/article-draft.md`
   - 例: 「劇的に上がる」→「ケーススタディでは向上を観測」

3. **定量比較プロトコルの明文化（P2）**
   - 対象: `paper/comparison-data.md`
   - 行数・セクション数・性質数の算出手順を追記し、再計算可能にする

4. **§6 記法の統一（P2）**
   - 対象: `docs/examples/citation-rendering.md`
   - Given/When/Then へ整形してスキル規約と一致させる

5. **ロードマップ運用の更新（P2）**
   - 対象: `README.md`
   - `Planned / In Progress / Done` の状態管理へ変更

6. **参考文献の階層化（P3）**
   - 対象: `paper/paper-driven-dev.md`
   - 「学術」「実務」「解説」に区分し、主張との対応を明示
