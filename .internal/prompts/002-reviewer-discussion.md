# 査読者間ディスカッション

## 入力
- @audits/audit-2026-02-19-claude-code.md
- @audits/audit-2026-02-19-codex.md

## タスク
サブエージェントを立ち上げ、3者間のロールプレイング議論を行ってください。

## 役割
- **Agent A（Claude査読者）** - Claude Codeによる査読の立場を代弁
- **Agent B（Codex査読者）** - Codexによる査読の立場を代弁
- **Agent C（論文執筆者）** - 本リポジトリのオーナーとして応答・判断

## 議論ルール
- 迎合せず、必要に応じて反論・異議を唱える
- 主張には根拠を示す
- 複数ラウンドのラリーを経て合意形成に至る
- 各ラウンドごとにファイルを更新する

## 成果物
`audits/audit-{日付}-discussion.md` に以下を出力：

```
## 参加者
- Agent A: Claude査読者
- Agent B: Codex査読者
- Agent C: 論文執筆者

## Round 1: 論点提示
## Round 2: 反論・深掘り
## Round N: ...
## 合意形成: 最終結論
```
