# Git 論文執筆ワークフローモデル

paper-driven-dev リポジトリにおける git ワークフローの推奨モデル。

---

## 1. コミット戦略

### コミットタイプ

既存の `type: 日本語説明` 規約を維持しつつ、論文向けタイプを追加する。

| タイプ | 用途 | 例 |
|--------|------|-----|
| `paper:` | 論文本体の内容変更 | `paper: S3 に既存アプローチ2件を追加` |
| `data:` | 定量データ・図表 | `data: CS2 の定量比較テーブルを修正` |
| `review:` | 査読対応（コメント管理・レスポンスレター） | `review: R1-C3 循環論法への反論を追記` |
| `audit:` | 内部監査成果物 | `audit: Claude Code 監査結果を追加` |
| `docs:` | 論文以外のドキュメント（README、ガイド） | `docs: README の Quick Start を更新` |
| `feat:` | プラグインコード変更 | `feat: /article スキル定義を追加` |
| `fix:` | 事実誤認・誤字の修正 | `fix: paper S5.1 の引用番号ずれを修正` |
| `refactor:` | 内容を変えない構造変更 | `refactor: paper S3 をサブセクションに分割` |
| `build:` | ビルド・設定・マニフェスト | `build: プラグインマニフェストを更新` |
| `chore:` | 雑務（.gitignore、ディレクトリ整理） | `chore: .gitignore に .worktrees/ を追加` |

**`paper:` と `docs:` を分ける理由**: `git log --oneline --grep='^paper:'` で論文固有の履歴だけを抽出できる。

### 参照記法

- **セクション**: `S1`, `S3.2`, `S5.1`
- **査読者コメント**: `R1-C3`（Reviewer 1, Comment 3）

### 粒度の指針

| フェーズ | コミット単位 | 例 |
|----------|------------|-----|
| 初稿執筆 | セクションまたはサブセクション単位 | `paper: S3.2 RFC/ADR の分析を追加` |
| 査読対応 | 査読コメント単位（複数セクションにまたがってよい） | `review: R1-C2 交絡因子の議論を S5.1 と S7 に追加` |
| データ作業 | データ変更と参照するプロのーズ変更を分離 | `data: CS2 の計測値を再計算` → `paper: S4 をデータ修正に合わせて更新` |

### Tidy First 原則

構造変更と内容変更は必ず別コミットにする。

```bash
# 構造変更（内容不変）
git commit -m "refactor: paper S3 のサブセクション番号を振り直し"

# 内容変更
git commit -m "paper: S3.5 ペルソナプロンプティングのアプローチを追加"
```

構造変更コミットの前後でテスト（差分レビュー）を行い、意味が変わっていないことを確認する。

---

## 2. ブランチ戦略

### 基本方針

**`main` 中心で運用する。** ブランチは「投稿済みバージョンを壊すリスクがある場合」のみ作成する。

ソロの論文執筆では、ブランチ間の切り替えコスト（git checkout のコストではなく「最新の思考がどのブランチにあるか」の認知コスト）がブランチの利点を上回ることが多い。

### ブランチを作らない場面

- 投稿前の初稿執筆・改訂
- 誤字修正・軽微な修正
- 監査成果物の追加
- 後方互換なプラグイン変更

### ブランチを作る場面

| パターン | 命名 | 用途 |
|----------|------|------|
| 査読後の大規模改訂 | `revision/vN` | 投稿済みタグを保護しつつ改訂作業 |
| 実験的書き換え | `experiment/topic` | 失敗しても捨てられるように隔離 |
| プラグイン新機能 | `feat/name` | 論文の git log を汚さない |

### 改訂ブランチの運用例

```bash
# 査読を受け取った後
git checkout -b revision/v2

# 改訂作業...
git commit -m "review: R1-C1 循環論法の指摘に対し時系列を明確化"
git commit -m "review: R2-C4 実験条件の不整合を修正"
git commit -m "paper: S5 の提案手法を大幅に書き換え"

# 改訂完了
git checkout main
git merge --no-ff revision/v2 -m "merge: v2 改訂版をメインに統合"
git tag -a v2-submitted -m "v2 [venue] 改訂版投稿 (YYYY-MM-DD)"
```

**`--no-ff` を使う理由**: マージコミットにより、改訂作業がどこで始まりどこで終わったかが `git log --graph` で視覚的に明確になる。

---

## 3. タグ戦略

### 命名規約

形式: `vN-event`

| タグ | タイミング | 種類 | メッセージ例 |
|------|-----------|------|-------------|
| `v0-draft` | 内部レビュー完了時 | annotated | `v0 内部レビュー用ドラフト (2026-02-19)` |
| `v1-submitted` | 論文投稿時 | annotated | `v1 [venue] 投稿版 (YYYY-MM-DD)` |
| `v1-reviews` | 査読返却時 | lightweight | — |
| `v2-submitted` | 改訂版投稿時 | annotated | `v2 [venue] 改訂版投稿 (YYYY-MM-DD)` |
| `v2-accepted` | 採択・カメラレディ版 | annotated | `v2 採択版 (YYYY-MM-DD)` |

### annotated vs lightweight の使い分け

- **annotated tag**: 外部に提出するスナップショット。日付・投稿先・共著者等のメタデータを記録
- **lightweight tag**: 時系列上のマーカー。メタデータ不要

### semver を使わない理由

論文にはパブリック API がない。バージョン番号は投稿ラウンドに対応する序数（v1, v2, v3）であり、変更の大きさを示す semver（v1.2.3）とは意味が異なる。

### annotated tag の例

```bash
git tag -a v1-submitted -m "v1 [会議名/ジャーナル名] 投稿版 (YYYY-MM-DD)
- 投稿先: [venue]
- 提出形式: [PDF/Markdown]
- 共著者: [names]"
```

---

## 4. 査読対応フロー

### ディレクトリ構造

```
paper/
├── paper-driven-dev.md
├── comparison-data.md
└── reviews/
    └── v1/
        ├── reviewer-comments.md    # 査読コメントのカタログ
        └── response-letter.md      # レスポンスレター（逐次追記）
```

**`audits/` との使い分け**: `audits/` は投稿前の内部レビュー（AI 監査）。`paper/reviews/` は投稿後の外部査読への対応。

### Step 1: コメントのカタログ化

査読を受け取ったら、各コメントに安定 ID を付与する。

```markdown
# Reviewer Comments: v1

## Reviewer 1 (R1)

### R1-C1: 循環論法の指摘
SKILL.md の指示と「自然に出現する」という主張の矛盾について。

### R1-C2: 交絡因子の未分離
「論文形式の効果」と「構造化テンプレートの効果」が分離できていない。

## Reviewer 2 (R2)

### R2-C1: 実験条件の不整合
paper.md と comparison-data.md で異なる実験条件。
```

```bash
git add paper/reviews/v1/reviewer-comments.md
git commit -m "review: v1 査読コメントをカタログ化"
```

### Step 2: コメントごとの対応

**核心的ルール**: 毎回の `review:` コミットに、論文の変更とレスポンスレターの更新を一緒に含める。

```markdown
# Response to Reviewers: v1 → v2

## R1-C1: 循環論法の指摘
**判断**: 部分的に認める。時系列の説明を明確化。
**対応箇所**: S1 para 2, S3.1 新規追加
**変更内容**: テンプレート開発の動機（テンプレートなしでの観察）を明記。
```

```bash
git add paper/paper-driven-dev.md paper/reviews/v1/response-letter.md
git commit -m "review: R1-C1 循環論法への対応 - S1 に時系列を追記"
```

### Step 3: 追跡

コメントからコミットへの追跡:

```bash
git log --oneline --grep='R1-C1'
```

全査読対応コミットの一覧:

```bash
git log --oneline --grep='^review:'
```

---

## 5. バージョン管理ライフサイクル

### フェーズ図

```
Phase 0: Bootstrap
  main: Initial commit ... 現在
    ↓
Phase 1: 投稿前改訂          ← 現在地
  main: 監査結果を反映 → v0-draft タグ → 改訂作業
    ↓
Phase 2: 投稿
  main: v1-submitted タグ
    ↓ (査読待ち)
Phase 3: 査読受領
  main: v1-reviews タグ → revision/v2 ブランチ作成
    ↓
Phase 4: 改訂作業
  revision/v2: 各コメントへの対応コミット
    ↓
Phase 5: 改訂版投稿
  main: revision/v2 をマージ → v2-submitted タグ
    ↓ (採択の場合)
Phase 6: カメラレディ
  main: フォーマット調整 → v2-accepted タグ
```

### 現状からの即時アクション

```bash
# 1. 未コミットファイルをコミット
git add .gitignore
git add audits/audit-2026-02-19-claude-code.md
git add audits/audit-2026-02-19-codex.md
git add audits/audit-2026-02-19-discussion.md
git add audits/prompts/001-comprehensive-audit.md
git add audits/prompts/002-reviewer-discussion.md
git commit -m "audit: 内部監査成果物を追加"

# 2. v0-draft タグを打つ
git tag -a v0-draft -m "v0 内部レビュー用ドラフト (2026-02-19)
- 論文ドラフト完成
- 定量比較データ（2ケーススタディ）
- Claude Code / Codex 監査完了
- 査読者間ディスカッション完了"
```

### Phase 1 → 2: 投稿

```bash
git status  # クリーンであることを確認
git tag -a v1-submitted -m "v1 [venue] 投稿版 (YYYY-MM-DD)"
git push origin main --tags
```

### Phase 2 → 3: 査読受領

```bash
git tag v1-reviews
git checkout -b revision/v2
mkdir -p paper/reviews/v1
# reviewer-comments.md を作成
git add paper/reviews/v1/reviewer-comments.md
git commit -m "review: v1 査読コメントをカタログ化"
```

### Phase 4 → 5: 改訂版投稿

```bash
git checkout main
git merge --no-ff revision/v2 -m "merge: v2 改訂版 - 全査読コメントへの対応を統合"
git tag -a v2-submitted -m "v2 [venue] 改訂版投稿 (YYYY-MM-DD)
- R1: N件のコメントに対応
- R2: N件のコメントに対応
- 主な変更: ..."
git push origin main --tags
```

---

## 6. 命名規約一覧

| 対象 | 規約 | 例 |
|------|------|-----|
| コミットタイプ | 英小文字 | `paper:`, `review:`, `data:` |
| コミット説明 | 日本語 | `S3.2 の分析を追加` |
| セクション参照 | `S` + 番号 | `S1`, `S3.2` |
| 査読コメントID | `RN-CN` | `R1-C3`, `R2-C1` |
| タグ（投稿） | `vN-submitted` | `v1-submitted` |
| タグ（ドラフト） | `vN-draft` | `v0-draft` |
| タグ（査読受領） | `vN-reviews` | `v1-reviews` |
| タグ（採択） | `vN-accepted` | `v2-accepted` |
| ブランチ（改訂） | `revision/vN` | `revision/v2` |
| ブランチ（実験） | `experiment/topic` | `experiment/alternative-s5` |
| ブランチ（機能） | `feat/name` | `feat/multi-model-support` |
| 査読ディレクトリ | `paper/reviews/vN/` | `paper/reviews/v1/` |

---

## 7. 設計判断の根拠

### main 中心の理由

ソロの論文執筆では「最新の思考がどのブランチにあるか」という認知コストが高い。ブランチの恩恵（並行作業の隔離）はソロでは限定的。投稿済みバージョンの保護が必要な場面でのみブランチを使う。

### `--no-ff` マージの理由

fast-forward マージだと改訂作業が `main` の直線履歴に溶け込む。`--no-ff` によるマージバブルが、改訂の開始・終了を `git log --graph` で可視化する。

### annotated tag の理由

投稿は専門的・法的に重要なイベント。日付・投稿先・共著者のメタデータを数ヶ月後に参照したい場面がある。annotated tag はこのメタデータを保存する。

### `.internal/` と `paper/reviews/` の使い分け

`.internal/` は git 追跡外のスクラッチスペース（下書き、個人メモ）。`paper/reviews/` は査読者と編集者に共有するフォーマルな成果物。レスポンスレターは追跡対象にすべき。

### 論文とプラグインを同一リポジトリに置く理由

この論文は PDD プラグインについて書かれており、プラグインは PDD を実装している。自己言及的な構造を持つプロジェクトでは、分離するとコンテキストが失われる。コミットタイプのプレフィックスで履歴をフィルタリングすれば十分。

```bash
# 論文の履歴だけ
git log --oneline --grep='^paper:\|^data:\|^review:'

# プラグインの履歴だけ
git log --oneline --grep='^feat:\|^fix:\|^build:'
```

将来プラグインが独立プロダクトとして独自のリリースサイクルを持つようになった時点で分離を検討する。
