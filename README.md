# Paper-Driven Development

**LLM に学術論文の形式で書かせると、設計分析の品質向上が観測される。**

Paper-Driven Development は、LLM に学術論文の形式（§1 問題定義 〜 §7 制約と今後の課題）で技術文書を書かせることで、テンプレートが以下の行動を構造的に引き出す開発手法です:

- **体系的な先行事例調査** — 既存アプローチを網羅的に列挙・比較
- **各手法の批判的評価** — 利点だけでなく限界を明示
- **提案の形式的正当化** — 不変条件や前提を明確化
- **検証可能な性質の定義** — テスト条件として導出できる具体的な性質

## Quick Start

### Claude Code Plugin としてインストール

```shell
# マーケットプレイスを追加
/plugin marketplace add rema424/paper-driven-dev

# プラグインをインストール
/plugin install paper-driven-dev@rema424-paper-driven-dev

# 使う
/paper-driven-dev:article RAGシステムでストリーミング中に引用番号をリアルタイムで正しく表示する方法
```

### ローカルで試す

```shell
git clone https://github.com/rema424/paper-driven-dev.git
claude --plugin-dir ./paper-driven-dev
```

## 生成される文書の構造

```
§1. 問題定義
  §1.1 背景
  §1.2 矛盾する要求（対立するトレードオフ）
  §1.3 本文書の範囲
§2. 現状のアーキテクチャと制約
§3. 既存アプローチとその限界
§4. 問題の本質
§5. 提案手法
§6. 検証可能な性質
§7. 制約と今後の課題
```

## なぜ効くのか

3つの仮説があります（いずれも因果関係としては検証困難）:

1. **学習データ品質仮説**: 査読済み論文は高品質データであり、LLM が論文形式でより高品質な出力を生成する
2. **暗黙的 CoT 効果**: 論文形式が「問題定義→分析→提案」の思考順序を強制する
3. **ペルソナ効果**: 「論文を書け」が「研究者として分析せよ」というペルソナ指定として機能する

## ドキュメント

- [使い方ガイド](docs/guide.md) — 詳しい使い方、適用基準、関連手法との比較
- [サンプル: RAG 引用リナンバリング](docs/examples/citation-rendering.md) — 実際の生成例
- [サンプル: セッション管理方式の選定](docs/examples/session-management.md) — マルチテナント SaaS における認証設計分析

## 今後の計画

### Done

- [x] Before/After の定量比較（2ケーススタディ、[comparison-data.md](paper/comparison-data.md)）
- [x] 学術論文ドラフトの執筆（[paper-driven-dev.md](paper/paper-driven-dev.md)）
- [x] 内部監査（Claude Code / Codex による独立レビュー + ディスカッション）
- [x] 3条件比較実験（A: Conventional / B: Paper-format / C: PDD Template）の実施
- [x] B バリアント実験（B1/B2/B3）によるフレーミング効果の分離検証
- [x] CC×Codex 構造化議論に基づく論文・文書の全面改訂

### In Progress

- [ ] 論文の最終レビューと投稿準備

### Planned

- [ ] 異なるドメインでのサンプル追加（パフォーマンス最適化等）
- [ ] 複数 LLM での再現性確認（Claude, GPT, Gemini）
- [ ] 強化版プロンプト（CoT + ペルソナ）との比較
- [ ] D 条件（論文形式なしのチェックリスト）の検証
- [ ] 論文の投稿・公開

## License

[MIT](LICENSE)
