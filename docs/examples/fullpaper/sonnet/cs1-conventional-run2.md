# CS1 条件A: Conventional — RAG引用リナンバリング (Run 2)

> **Run**: CS1-A-Run2
> **Date**: 2026-02-22
> **Model**: Claude Sonnet 4.6
> **Context**: Fresh agent invocation

---

## 問題の本質

RAGシステムにおける引用リナンバリング問題の核心は、**時間的不確実性**にある。LLMはストリーミング中に `source_3` や `source_7` のような内部識別子を使いながら回答を生成するが、ユーザーには `[1]`, `[2]`, `[3]` のような連番を見せたい。問題は以下の3つの制約が同時に成立しなければならない点にある。

1. **即時性**: 引用が初めて登場した時点でユーザーに番号を表示する
2. **不変性**: 一度表示した番号は後から変わってはならない
3. **整合性**: ストリーム完了時の引用一覧と番号体系が一致している

この3つを同時に満たすのが難しい理由は、ストリーミング中は「最終的にどの引用が何個使われるか」が不明なためである。もし事前に確定していれば、あらかじめマッピングを構築してからストリーミングを開始できる。

---

## 設計アプローチの分析

### アプローチ1: 先行マッピング方式（2フェーズ）

**概念**

ストリーミングを2段階に分ける。第1フェーズでLLMに「どの引用を使うか」を事前に列挙させ、第2フェーズで本文生成をストリーミングする。

**実装の概略**

```
Phase 1: LLMへのプロンプト
  "まず、使用する検索結果のIDをJSON形式で列挙してください"
  → LLMが ["source_3", "source_7"] を返す

Phase 2: マッピング構築
  source_3 → [1]
  source_7 → [2]

Phase 3: 本文のストリーミング開始（マッピング確定済み）
```

**長所**

- 実装がシンプル
- 本文ストリーミング中に番号が変わることは絶対にない
- 後処理が不要

**短所**

- LLMが本文生成前に引用を正確に予測できるとは限らない。実際の推論過程で「やはりこの引用も使おう」となる可能性がある
- Phase 1の応答を待つ分、最初の文字が表示されるまでのレイテンシが増加する
- LLMへのリクエストが2回必要になり、コストと時間が増える

**評価**: 制約を完全に満たすが、前提（LLMが引用を正確に事前予測できる）が崩れると整合性が失われる。

---

### アプローチ2: 出現順アサイン方式（インクリメンタル）

**概念**

ストリーミング中にトークンを監視し、内部識別子が初めて登場した時点で連番を割り当てる。割り当て順は出現順で確定する。

**実装の概略**

```python
class CitationMapper:
    def __init__(self):
        self.mapping = {}  # source_id -> display_number
        self.counter = 0

    def get_or_assign(self, source_id: str) -> int:
        if source_id not in self.mapping:
            self.counter += 1
            self.mapping[source_id] = self.counter
        return self.mapping[source_id]

def process_stream(token_stream):
    mapper = CitationMapper()
    for token in token_stream:
        # トークン内の内部識別子を検出
        if is_citation_token(token):
            source_id = extract_source_id(token)
            number = mapper.get_or_assign(source_id)
            yield render_citation(number)  # "[1]" など
        else:
            yield token
```

**ストリーム完了時の整合**

ストリーム終了後、`mapper.mapping` を反転させてソース一覧を構築する。

```python
sources = [
    retrieve_source(source_id)
    for source_id, num in sorted(mapper.mapping.items(), key=lambda x: x[1])
]
```

**長所**

- 真のリアルタイム処理。最初のトークンから表示できる
- 一度割り当てた番号は変わらない（アサイン済みの場合は既存番号を返すため）
- 追加のLLMリクエストが不要

**短所**

- 引用の出現順が最終的な連番の順序になる。ユーザーが期待する「文書順」や「関連度順」とずれる可能性がある
- 引用が途中でキャンセルされた場合（LLMが言及したが後で撤回した場合）、番号の歯抜けが生じる

**評価**: 3つの制約を全て満たす。最も実用的なアプローチ。

---

### アプローチ3: 後処理置換方式（バッファリング）

**概念**

ストリーミング中は内部識別子をそのまま保持し、ストリーム完了後に全体を走査してリナンバリングする。UIには「処理済み」バージョンのみを表示する。

**実装の概略**

```python
buffer = []
for token in token_stream:
    buffer.append(token)
    # UIには「処理中」インジケーターを表示
    yield show_loading_indicator()

# ストリーム完了後
full_text = "".join(buffer)
renumbered_text = renumber_citations(full_text)
sources = extract_and_order_sources(full_text)
yield full_text_with_sources(renumbered_text, sources)
```

**長所**

- 番号の整合性が完全に保証される
- 任意の順序（文書順、関連度順など）でリナンバリングできる

**短所**

- ストリーミングの意味を失う。ユーザーは全文生成完了まで何も読めない
- レイテンシが最大になる
- 「リアルタイムで引用番号を表示する」という要件を満たさない

**評価**: 要件の「ストリーミング中にリアルタイムで引用番号を表示する」を根本的に違反する。

---

### アプローチ4: プレースホルダー+差分更新方式

**概念**

ストリーミング中は仮番号（`?`）でプレースホルダーを表示し、引用が確定した時点でWebSocketやSSEで差分更新を送信する。

**実装の概略**

```
ストリーム中: "この技術は[?]によって提唱され..."
引用確定時: フロントエンドに差分 {placeholder_id: "p1", number: 1} を送信
フロントエンド: p1 を [1] に置換
```

**長所**

- 本文のストリーミングを妨げない
- 最終的な番号体系を柔軟に決定できる

**短所**

- フロントエンドの実装が複雑（差分更新の受信と適用）
- 「一度表示した番号が後から変わらない」という要件に反する（`?` → `[1]` への変化は許容か？）
- 引用が何度も更新される場合、ユーザーの視線が乱れる

**評価**: 「番号が変わらない」の解釈次第で有効だが、UX上の懸念がある。

---

## 推奨設計

**アプローチ2（出現順アサイン方式）** を基本とし、以下の拡張を加える。

### 推奨実装の詳細

```python
import re
from dataclasses import dataclass, field
from typing import Generator, Optional

@dataclass
class CitationState:
    mapping: dict = field(default_factory=dict)  # source_id -> display_number
    counter: int = 0
    sources_registry: dict = field(default_factory=dict)  # source_id -> metadata

    def assign(self, source_id: str) -> int:
        """初回登場時に番号を割り当て、以降は同じ番号を返す"""
        if source_id not in self.mapping:
            self.counter += 1
            self.mapping[source_id] = self.counter
        return self.mapping[source_id]

    def get_ordered_sources(self) -> list:
        """出現順にソートされたソース一覧を返す"""
        ordered = sorted(self.mapping.items(), key=lambda x: x[1])
        return [
            {
                "number": num,
                "id": source_id,
                "metadata": self.sources_registry.get(source_id, {})
            }
            for source_id, num in ordered
        ]

CITATION_PATTERN = re.compile(r'\[source_(\d+)\]')

def streaming_pipeline(
    llm_stream: Generator[str, None, None],
    source_registry: dict
) -> Generator[dict, None, None]:
    """
    LLMストリームを受け取り、引用リナンバリング済みのイベントを生成する
    """
    state = CitationState(sources_registry=source_registry)
    buffer = ""  # 引用パターンをまたぐトークンのバッファ

    for token in llm_stream:
        buffer += token

        # バッファ内で完結した引用を処理
        last_pos = 0
        for match in CITATION_PATTERN.finditer(buffer):
            # マッチ前のテキストを即座に出力
            if match.start() > last_pos:
                yield {
                    "type": "text",
                    "content": buffer[last_pos:match.start()]
                }

            # 引用番号を割り当て
            source_id = f"source_{match.group(1)}"
            number = state.assign(source_id)

            yield {
                "type": "citation",
                "content": f"[{number}]",
                "source_id": source_id,
                "number": number
            }
            last_pos = match.end()

        # 処理済み部分をバッファから削除。未完了パターンは残す
        buffer = buffer[last_pos:]

    # 残余バッファを出力（引用パターンの途中でストリームが終わった場合の安全策）
    if buffer:
        yield {"type": "text", "content": buffer}

    # ストリーム完了: ソース一覧を出力
    yield {
        "type": "sources",
        "content": state.get_ordered_sources()
    }
```

### 境界トークン問題への対処

ストリーミングでは `[source_3]` が `[sour` と `ce_3]` のように分割されることがある。バッファ方式で対処する。

```python
def should_flush_buffer(buffer: str) -> bool:
    """
    引用パターンが途中で切れている可能性があるか確認する
    '[' を含むが ']' を含まない場合はまだパターンが完結していない可能性がある
    """
    if '[' in buffer and ']' not in buffer:
        return False  # パターン完結待ち
    return True
```

ただし、無限にバッファしないよう、一定文字数（例: 50文字）を超えた場合は強制フラッシュする安全弁も必要。

---

## 各制約への適合確認

| 要件 | 充足状況 | 根拠 |
|------|----------|------|
| ストリーミング中にリアルタイムで引用番号を表示 | ✓ | 引用トークン検出と同時に番号を割り当て・出力 |
| 一度表示した番号が後から変わらない | ✓ | `mapping` にアサイン済みの場合は常に同じ番号を返す |
| ストリーム完了時にソース一覧と整合 | ✓ | `get_ordered_sources()` が `mapping` を元に一覧を生成する |

---

## トレードオフの整理

**この設計が諦めているもの**

- ソースの「関連度順」での番号付け: 出現順が連番の基準になる
- 全引用数の事前把握: 何個の引用が使われるかはストリーム完了まで不明

**この設計が優先しているもの**

- ゼロ追加レイテンシ: ストリーミング開始から即座に引用番号を表示できる
- 実装のシンプルさ: フロントエンドに特別な差分適用ロジックが不要
- 要件の完全充足: 3つの制約を全て満たす

出現順の連番付けは多くのRAGシステムで自然な選択であり、ユーザーは「本文の文脈でどの順番で登場したか」という意味で番号を解釈できる。これは `[1]` が最初に言及された引用であるという直感に合致する。
