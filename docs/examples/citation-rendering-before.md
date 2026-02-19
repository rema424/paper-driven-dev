# Before: 通常プロンプトによる出力

> 以下は、論文形式を指定せず、通常のプロンプトで同じ問題を LLM に聞いた場合の出力です。
> [After（論文形式）](citation-rendering.md) と比較してください。

## プロンプト

```
以下の技術的な問題について、設計分析と解決策を提案してください。

問題: RAGシステムにおいて、LLMがストリーミングで構造化JSON出力
（{ body: "...[source_N]...", citedSourceIds: [...] }）を返す際、
引用参照（[source_N]）をリアルタイムかつ正しい連番（[1], [2], [3]...）で
描画する方法。

LLMは検索結果の元番号（例: source_3, source_7）を使って引用しますが、
ユーザーに表示する際は使用した引用のみの連番にリナンバリングする必要が
あります。しかしストリーミング中は全文が確定していないため、最終的な
連番が決まりません。

この問題の解決策を提案してください。
```

## 出力

**結論**
`source_N`（内部ID）と`[1] [2]...`（表示番号）を分離し、**サーバー側でストリーミング中に逐次マッピング**する設計が最適です。
これによりリアルタイム表示と最終整合性を両立できます。

**なぜ難しいか**
- ストリーム途中では全文未確定。
- 引用トークンがチャンク分割される（例: `[sou` + `rce_7]`）。
- LLMの`citedSourceIds`は途中で不完全/不整合になり得る。

**推奨アーキテクチャ**
- 画面表示用番号はLLMに任せず、バックエンドで決定する。
- `body`の`[source_N]`を検出した順に採番する（初出順）。
- 変換ルール:
  - 初出`source_7` → `[1]`
  - 初出`source_3` → `[2]`
  - 再出`source_7` → `[1]`再利用
- クリック遷移用に`displayNo -> sourceId`マップを保持。

**ストリーム処理アルゴリズム（要点）**
```ts
rawToDisplay: Map<string, number> = new Map();
orderedRawIds: string[] = [];
next = 1;

function mapCitation(rawId: string) {
  if (!rawToDisplay.has(rawId)) {
    rawToDisplay.set(rawId, next++);
    orderedRawIds.push(rawId);
  }
  return rawToDisplay.get(rawId)!;
}
```
- `carry buffer`を持ち、チャンク跨ぎの`[source_N]`を正しく復元して検出。
- 描画は都度`[source_N] -> [displayNo]`へ置換して出力。

**最終確定時**
- 最終`body`を再走査して整合性チェック。
- `citedSourceIds`は**LLM値を信頼せず**、`orderedRawIds`から再生成（または照合して不一致をログ）。

**重要な設計判断**
- **append-onlyストリーム**（過去テキストを編集しない）を前提にできるなら、この方式で「リアルタイムかつ最終的にも正しい連番」が成立します。
- もし途中で過去文が書き換わる可能性があるなら、表示番号は一時表示にして**最後に一括リナンバリング**する2段階方式が安全です。
