# CS1 条件A: Conventional — RAG引用リナンバリング (Run 2)

> **Run**: CS1-A-Run2
> **Date**: 2026-02-20
> **Thread**: 新規 (Codex MCP: 019c79bd-2858-7ad3-a778-d5e6da9851f3)
> **Model**: GPT-5.2 (via Codex)

---

**結論**
最も安定する設計は、**「LLMは `source_x` の内部IDだけ出す」**、**「表示用の `[1] [2]` はストリーミング層で付与する」**の分離です。

**推奨アーキテクチャ**
1. 検索結果を `source_3`, `source_7` のような内部IDで管理し、メタ情報（title/url/snippet）を保持します。
2. LLMには `[1]` を直接出させず、`<cite source="source_7"/>` のような機械可読タグを出させます。
3. ストリーム受信側でタグを逐次パースし、`source_id -> 表示番号` のマップに登録します。
4. 初出の `source_id` にだけ次番号を割り当てます（`next=1,2,3...`）。再出は同じ番号を再利用します。
5. 画面には即時に `[n]` を表示し、完了時は同じマップから引用一覧を生成します。

**要件への対応**
- ストリーミング中にリアルタイム表示: タグ検出時にその場で `[n]` を描画。
- 一度表示した番号が変わらない: マップは追記のみ、再採番しない。
- 完了時に整合: 引用一覧は同一マップを唯一の真実源として生成。

**実装ポイント（重要）**
- チャンク分割対策: タグが分割到着するため、インクリメンタルパーサを使う。
- 不正ID対策: 検索結果に存在しないIDは `[?]` 表示か無視し、番号採番しない。
- 競合対策: 並列処理時は採番処理を排他（mutex/atomic）で保護。
- 再接続対策: `citation_map` を `message_id` 単位で保持し、再開時に再利用。

**最小ロジック**
```text
onCitation(source_id):
  if source_id not in retrieved_sources:
    return "[?]"
  if source_id not in citation_map:
    citation_map[source_id] = next_number++
  return "[" + citation_map[source_id] + "]"
```

**例**
ストリーム中に `source_7 -> source_3 -> source_7` が出た場合:
- 本文表示: `[1] ... [2] ... [1]`
- 最終一覧:
  - `[1] source_7 ...`
  - `[2] source_3 ...`

必要なら次に、SSE/WebSocketイベント設計（`text_delta`, `citation_delta`, `citations_final`）まで具体化できます。
