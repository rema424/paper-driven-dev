# CS1 条件A: Conventional — RAG引用リナンバリング (Run 3)

> **Run**: CS1-A-Run3
> **Date**: 2026-02-22
> **Model**: Claude Sonnet 4.6
> **Context**: Fresh agent invocation

---

# RAGストリーミング引用リナンバリング設計分析

## 問題の本質

この問題の核心は「確定前のデータへの依存」にある。LLMはストリーミング中に `source_3` や `source_7` といった内部IDを参照するが、ユーザー向けの連番 `[1]`, `[2]` は全引用が確定してから初めて意味を持つ。しかし「一度表示した番号が変わらない」という要件が、後処理による一括変換を禁じている。

この制約の組み合わせが問題を非自明にする。

---

## 設計アプローチの分析

### アプローチ1: 遅延割当（Lazy Assignment）

**概要**: 引用が初めて出現した順に番号を割り当てる。`source_3` が最初に現れたら `[1]`、次に `source_7` が現れたら `[2]` とする。

**実装スケッチ**:

```python
class StreamingCitationMapper:
    def __init__(self):
        self.source_to_number = {}  # {"source_3": 1, "source_7": 2}
        self.counter = 0

    def get_or_assign(self, source_id: str) -> int:
        if source_id not in self.source_to_number:
            self.counter += 1
            self.source_to_number[source_id] = self.counter
        return self.source_to_number[source_id]

    def process_chunk(self, chunk: str) -> str:
        # "source_X" パターンを検出して置換
        import re
        def replace_citation(match):
            source_id = match.group(0)
            num = self.get_or_assign(source_id)
            return f"[{num}]"
        return re.sub(r'source_\d+', replace_citation, chunk)
```

**長所**:
- 実装がシンプル
- 一度割り当てた番号は変わらない（要件を満たす）
- ストリームを通じてO(1)の状態管理

**短所**:
- 最終的なソース一覧との順序整合性が保証されない
- LLMが同じ引用を繰り返す場合、重複割当を避ける処理が必要
- チャンク境界で `source_` という文字列が分断された場合に対応が必要

**チャンク境界問題の対策**:

```python
class StreamingCitationMapper:
    def __init__(self):
        self.source_to_number = {}
        self.counter = 0
        self.buffer = ""  # 未確定のチャンク末尾を保持

    def process_chunk(self, chunk: str) -> str:
        text = self.buffer + chunk
        self.buffer = ""

        # パターンが途中で切れている可能性を考慮
        # "source_" で終わる場合はバッファリング
        import re
        pattern = r'source_\d+'

        # 末尾が不完全なパターンかチェック
        if re.search(r'source_\d*$', text) and not re.search(r'source_\d+', text):
            # 末尾の不完全なパターンをバッファへ
            match = re.search(r'source_\d*$', text)
            self.buffer = match.group(0)
            text = text[:match.start()]

        def replace_citation(m):
            source_id = m.group(0)
            if source_id not in self.source_to_number:
                self.counter += 1
                self.source_to_number[source_id] = self.counter
            return f"[{self.source_to_number[source_id]}]"

        return re.sub(pattern, replace_citation, text)
```

---

### アプローチ2: プリアロケーション（Pre-allocation）

**概要**: RAGシステムはLLMに渡す前に検索結果を持っている。その検索結果に事前に番号を付け、LLMにも番号付きで渡す。

**プロンプト設計**:

```
以下の情報源を参照して回答してください:
[1] source_3: "Pythonは1991年に..."
[2] source_7: "型ヒントはPython 3.5で..."
[3] source_1: "パフォーマンス比較では..."

回答中で情報源を引用する際は [1], [2], [3] の番号を使用してください。
```

**長所**:
- LLMがそのまま `[1]`, `[2]` を出力するため、変換処理が不要
- ソース一覧との整合性が構造的に保証される
- チャンク境界問題が発生しない

**短所**:
- LLMが番号を守らない場合がある（ハルシネーションリスク）
- 検索結果として返ってきたが実際に使われなかったソースも番号を持つ
- ソース一覧には実際に引用されたものだけを表示したい場合、後処理が必要

**LLMの指示遵守を高める工夫**:

```
重要な指示: 引用は必ず [番号] 形式で記述してください。
例: 「Pythonは動的型付け言語です [1]。」
番号は上記リストの番号のみ使用可能です。存在しない番号を作ってはいけません。
```

---

### アプローチ3: 仮番号＋事後確定（Placeholder + Commit）

**概要**: ストリーミング中は内部IDをそのまま透過させ、クライアント側でリアルタイムに番号を割り当てる。表示はSSEやWebSocketで行い、クライアントがローカル状態として番号マッピングを保持する。

**アーキテクチャ**:

```
Server (LLM Stream)          Client (Browser)
─────────────────────────    ─────────────────────────────
"Pythonは"                →  "Pythonは"
"ストリーミング"           →  "ストリーミング"
"言語です [source_3]"     →  "言語です [1]"  ← クライアントが変換
"。型は"                  →  "。型は"
"[source_7]"              →  "[2]"  ← クライアントが変換
```

**クライアント実装（TypeScript）**:

```typescript
class CitationRenderer {
  private sourceToNumber = new Map<string, number>();
  private counter = 0;
  private buffer = "";

  processChunk(chunk: string): string {
    const text = this.buffer + chunk;
    this.buffer = "";

    const pattern = /source_\d+/g;
    let result = "";
    let lastIndex = 0;
    let match;

    // パターンを検索して置換
    while ((match = pattern.exec(text)) !== null) {
      result += text.slice(lastIndex, match.index);
      const sourceId = match[0];

      if (!this.sourceToNumber.has(sourceId)) {
        this.counter++;
        this.sourceToNumber.set(sourceId, this.counter);
      }

      result += `[${this.sourceToNumber.get(sourceId)}]`;
      lastIndex = pattern.lastIndex;
    }

    // 末尾の不完全なパターンチェック
    const remaining = text.slice(lastIndex);
    if (/source_\d*$/.test(remaining) && !/source_\d+/.test(remaining)) {
      this.buffer = remaining.match(/source_\d*$/)![0];
      result += remaining.slice(0, remaining.length - this.buffer.length);
    } else {
      result += remaining;
    }

    return result;
  }

  // ストリーム完了時にソース一覧を生成
  generateSourceList(retrievedSources: Map<string, SourceMetadata>): SourceItem[] {
    const items: SourceItem[] = [];
    for (const [sourceId, num] of this.sourceToNumber) {
      const metadata = retrievedSources.get(sourceId);
      if (metadata) {
        items.push({ number: num, ...metadata });
      }
    }
    return items.sort((a, b) => a.number - b.number);
  }
}
```

**長所**:
- サーバー側の実装が単純
- クライアントが番号管理の責任を持つため、UI要件に柔軟に対応できる
- バッファリング処理がクライアント側に集中し、テストしやすい

**短所**:
- クライアントがビジネスロジック（番号割当）を持つ
- 複数クライアント（モバイル、デスクトップ、API）それぞれに実装が必要
- SSR（サーバーサイドレンダリング）環境では複雑になる

---

### アプローチ4: ストリーム後変換＋差分更新（Post-stream Delta）

**概要**: ストリーミング中は引用なしで本文を表示し、引用箇所にプレースホルダー（アンカー）を挿入する。ストリーム完了後、確定した引用マッピングで一括更新する。

**UX設計**:

```
ストリーミング中:
"Pythonは動的型付け言語です[...]。型ヒントは[...]で導入されました。"

ストリーム完了後（差分更新）:
"Pythonは動的型付け言語です[1]。型ヒントは[2]で導入されました。"

ソース一覧も同時に表示:
[1] Python公式ドキュメント
[2] PEP 484 — Type Hints
```

**実装**:

```javascript
// DOM操作での差分更新
function commitCitations(placeholders, mapping) {
  placeholders.forEach(placeholder => {
    const sourceId = placeholder.dataset.sourceId;
    const num = mapping[sourceId];
    placeholder.textContent = `[${num}]`;
    placeholder.classList.replace('pending', 'resolved');
  });
}
```

**長所**:
- 「一度表示した番号が変わらない」を別の解釈で実現（番号は確定後のみ表示）
- 最終的な整合性が完全に保証される

**短所**:
- ストリーミング中にユーザーが引用番号を見られない
- 要件の「ストリーミング中にリアルタイムで表示する」に反する可能性

---

## 推奨設計

要件を厳密に解釈すると「ストリーミング中にリアルタイムで表示」かつ「番号が変わらない」かつ「ソース一覧と整合」を同時に満たす必要がある。この3要件を最も素直に満たすのは**アプローチ2（プリアロケーション）とアプローチ1（遅延割当）の組み合わせ**である。

### 推奨アーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│                  RAG Pipeline                        │
│                                                     │
│  1. 検索 → [source_1, source_3, source_7]           │
│                                                     │
│  2. 関連性スコアでソート                              │
│     → [(source_3, 0.95), (source_7, 0.87), ...]    │
│                                                     │
│  3. 番号割当（プリアロケーション）                     │
│     → {source_3: 1, source_7: 2, source_1: 3}      │
│                                                     │
│  4. LLMプロンプト構築                                 │
│     "[1] = source_3内容, [2] = source_7内容..."     │
│                                                     │
│  5. LLMがストリームで [1], [2] を直接出力            │
│                                                     │
│  6. ストリーム完了後、実際に引用されたものを           │
│     ソース一覧として確定表示                           │
└─────────────────────────────────────────────────────┘
```

**ソース一覧の整合処理**:

```python
def finalize_source_list(
    response_text: str,
    preallocated_mapping: dict[str, int],  # {source_3: 1, source_7: 2}
    source_metadata: dict[str, SourceMetadata]
) -> list[SourceItem]:
    """
    実際に引用された番号のみをソース一覧に含める
    """
    import re
    used_numbers = set(int(m) for m in re.findall(r'\[(\d+)\]', response_text))

    # 逆引きマップ（番号 → source_id）
    number_to_source = {v: k for k, v in preallocated_mapping.items()}

    result = []
    for num in sorted(used_numbers):
        source_id = number_to_source.get(num)
        if source_id and source_id in source_metadata:
            result.append(SourceItem(
                number=num,
                metadata=source_metadata[source_id]
            ))

    return result
```

---

## エッジケース分析

### ケース1: LLMが未割当番号を生成した場合

LLMが `[4]` を出力したが、プリアロケーションで `[4]` は存在しない場合。

**対策**: ストリーム完了後のバリデーションで検出し、該当箇所をUI上でマークする（例: `[4†]` など）。プロダクション環境ではアラートを発砲してモニタリングする。

### ケース2: 同一ソースへの複数回引用

`source_3` が本文中に3回出現しても、常に `[1]` として表示される。プリアロケーション方式では自然に解決される。

### ケース3: 検索結果が0件の場合

検索結果がない場合、LLMへの指示に「引用は不要」と明示し、`[]` 形式の出力を抑制する。

### ケース4: ストリームの途中断（接続切断）

部分的なレスポンスでも、それまでに割り当てた番号は不変。ユーザーが再接続した場合は最初からストリームを再生成するか、部分キャッシュから再開する設計を選択する。

---

## 設計判断のトレードオフ表

| アプローチ | 実装複雑度 | 番号安定性 | ソース整合性 | LLM依存度 |
|-----------|-----------|-----------|------------|---------|
| 遅延割当 | 低 | 高 | 中（後処理要） | 低 |
| プリアロケーション | 低 | 高 | 高（構造的） | 高（指示遵守） |
| クライアント変換 | 中 | 高 | 中（後処理要） | 低 |
| 後変換＋差分更新 | 高 | — | 高 | 低 |

プリアロケーションはLLMの指示遵守という不確実性を持つが、プロンプトエンジニアリングとバリデーションで十分に制御可能であり、全体的なシステム複雑度が最も低い。**実運用ではプリアロケーションを基本とし、遅延割当をフォールバックとして組み合わせる設計を推奨する。**
