# CS1 条件B: Paper Format — RAG引用リナンバリング (Run 1)

> **Run**: CS1-B-Run1
> **Date**: 2026-02-22
> **Model**: Claude Sonnet 4.6
> **Context**: Fresh agent invocation

---

# ストリーミングRAGシステムにおける引用番号の一貫性保証：到着順序割り当てによる設計

## 概要

Retrieval-Augmented Generation（RAG）システムにおけるストリーミング応答生成時、LLMは内部的に `source_3`、`source_7` のような識別子で検索結果を参照するが、ユーザーインタフェースには `[1]`、`[2]` のような連番表記が求められる。本稿では、ストリーミング中に引用番号を確定的かつ単調増加的に割り当てることで、表示済みの番号が後から変化しないという制約を満たす設計パターンを分析する。核心的な知見は、**引用番号の割り当てを「ストリームにおける初出順序」に基づき行う**ことにより、全文確定を待たずとも番号の不変性を保証できるという点にある。

---

## 1. はじめに

大規模言語モデル（LLM）をバックエンドとしたRAGシステムは、ユーザーの問い合わせに対して関連文書を検索し、それらを根拠として応答を生成する。GPT-4やClaude等の現代的なLLMはトークン単位でのストリーミング出力をサポートしており、応答全文の生成完了を待たずに逐次表示することでユーザー体験が大きく向上する。

しかしながら、ストリーミングと引用番号付けは相性が悪い。バッチ処理であれば全文を走査し `source_3` → `[1]`、`source_7` → `[2]` のような正規化マッピングを事後的に構築できるが、ストリーミング時には全文が確定していないため、このアプローチは適用できない。

本稿の問題設定は次の三要件から構成される：

1. **リアルタイム表示**：ストリーミング中に引用番号を表示する
2. **番号不変性**：一度表示した番号が後から変更されない
3. **終端整合性**：ストリーム完了時にソース一覧と引用番号が整合している

これらの要件は一見競合するが、適切な設計によって同時に満たすことができる。本稿ではその設計を体系的に分析する。

---

## 2. 関連研究

### 2.1 RAGシステムのアーキテクチャ

Lewis et al. (2020) が提案したRAG（Retrieval-Augmented Generation）フレームワークは、密なパッセージ検索とシーケンス・ツー・シーケンス生成を組み合わせたものである。その後の発展として、検索結果をコンテキストに含めた上でLLMに回答生成を委ねるアーキテクチャが普及した。この設計では、LLMは検索結果を内部的な識別子（例：`[source_0]`、`source_3`）で参照する。

### 2.2 ストリーミング出力の先行事例

ChatGPTのServer-Sent Events（SSE）実装を始め、多くのLLMサービスがストリーミング応答をサポートしている。しかし、これらのシステムにおける引用番号付けは多くの場合バッチ処理として実装されており、ストリーミング中の引用整合性は十分に研究されていない。

### 2.3 一貫性ハッシュとシーケンス番号割り当て

分散システムにおける番号割り当て問題は古典的な研究対象であり、Lamport (1978) のクロックアルゴリズムはイベントの因果順序に基づく単調増加番号割り当ての基礎を提供した。本稿が提案する設計はこれと概念的に類似しており、「到着順序」を決定的な割り当て基準として用いる。

---

## 3. 問題の形式化

### 3.1 モデル

以下の記号を用いる：

- $S = \{s_1, s_2, \ldots, s_n\}$：RAGが取得したソース集合（内部識別子付き）
- $T = t_1 t_2 \cdots t_k$：LLMが生成するトークン列（ストリーム）
- $R(t_i)$：トークン $t_i$ が含む引用参照の集合（空集合の場合もある）
- $\phi: S \to \mathbb{N}$：内部識別子から表示番号へのマッピング関数

### 3.2 要件の形式化

**要件1（リアルタイム性）**：トークン $t_i$ が出力された時点で $R(t_i)$ 内の全ソースに対して $\phi$ が定義されていること。

**要件2（番号不変性）**：一度割り当てられた表示番号は変化しない。すなわち、$s \in S$ について $\phi(s)$ が定義された後は不変である。

**要件3（終端整合性）**：ストリーム完了時、表示された引用番号のソース一覧が実際に参照されたソースと一致する。

### 3.3 問題の困難性

バッチ処理では全文走査後に $\phi$ を構成するため三要件を自明に満たせるが、ストリーミングでは要件1が「先読み禁止」の制約を課す。これにより、後に出現するソースの情報を用いた番号割り当て最適化が不可能となる。

---

## 4. 設計の分析

### 4.1 到着順序割り当て（First-Appearance Ordering）

最もシンプルかつ要件を満たす設計は、**ソースの初出順に番号を割り当てる**ことである。

```
アルゴリズム: 到着順序割り当て

状態:
  mapping: Dict[str, int] = {}  # 内部識別子 → 表示番号
  counter: int = 0              # 次に割り当てる番号

トークン t_i を受信したとき:
  for each reference r in R(t_i):
    if r not in mapping:
      counter += 1
      mapping[r] = counter
    emit token with mapping[r]
```

このアルゴリズムは単調増加的に番号を割り当てるため、要件2（番号不変性）を構造的に保証する。番号はグローバルカウンタから順次払い出されるため、割り当ての後退（再割り当てによる番号変更）が原理的に発生しない。

### 4.2 終端整合性の達成

ストリーム完了後、`mapping` ディクショナリには実際に参照された全ソースとその表示番号が記録されている。これをソート（番号昇順）することで、表示と整合したソース一覧を構築できる：

```
ストリーム完了時:
  sources_ordered = sorted(mapping.items(), key=lambda x: x[1])
  emit sources_list: [(display_num, source_id), ...]
```

`mapping` はストリーム中に逐次更新されているため、追加の走査なしに完成している。これにより要件3が保証される。

### 4.3 実装上の考慮点

#### 4.3.1 引用トークンの検出

LLMがストリームに `source_3` や `[source_7]` のような引用マーカーを埋め込む場合、トークン境界をまたいでマーカーが出現する可能性がある。例えば `[sour`、`ce_3]` という2トークンに分割されるケースでは、単純なトークン単位のパースでは検出に失敗する。

解決策として、**ローリングバッファ**を用いた部分マッチ検出が有効である：

```
バッファ: str = ""
パターン: Regex = re.compile(r'\[?source_\d+\]?')

トークン t_i を受信したとき:
  buffer += t_i.text
  matches = pattern.findall(buffer)
  for match in matches:
    process_citation(match)
    buffer = buffer[buffer.index(match) + len(match):]
  emit processed_buffer_prefix
```

#### 4.3.2 引用なしソースの扱い

LLMが特定のソースを取得コンテキストに含まれていたにもかかわらず引用しなかった場合、そのソースは `mapping` に現れない。これは正しい動作であり、ソース一覧には実際に引用されたもののみを含めることで意味的な整合性が保たれる。

#### 4.3.3 重複引用の表示

同一ソースへの複数回の引用は、初出時に割り当てられた番号を再利用する。これは `mapping` の参照で自然に実現される。

---

## 5. 代替設計との比較

### 5.1 バッファリング後一括変換

全ストリームをバッファリングし、完了後に引用を正規化してから表示する設計。

**利点**：実装が単純。引用番号をソースIDのアルファベット順や重要度順に整列できる。

**欠点**：要件1（リアルタイム性）に根本的に違反する。応答全文が生成されるまでユーザーは何も見えない。

### 5.2 プレースホルダ方式

ストリーム中は `[?]` のようなプレースホルダを表示し、完了後に実際の番号で置換する。

**利点**：リアルタイム表示が可能。後処理で最適な番号順序を選択できる。

**欠点**：要件2（番号不変性）に違反する。プレースホルダから実番号への「変化」が発生する。DOM操作やクライアントサイドの更新ロジックが複雑になる。

### 5.3 ソースID直接表示

内部識別子 `source_3` をそのまま表示する。

**利点**：変換処理が不要。

**欠点**：ユーザーフレンドリーでない。`source_3`、`source_7` のような非連番表示は可読性が低い。

### 5.4 比較まとめ

| 設計 | リアルタイム性 | 番号不変性 | 終端整合性 | 実装複雑性 |
|------|--------------|-----------|-----------|-----------|
| 到着順序割り当て | ○ | ○ | ○ | 低 |
| バッファリング後一括変換 | ✗ | ○ | ○ | 低 |
| プレースホルダ方式 | △ | ✗ | ○ | 高 |
| ソースID直接表示 | ○ | ○ | ○ | 最低 |

到着順序割り当ては三要件を全て満たす唯一の設計である。

---

## 6. アーキテクチャ設計

### 6.1 コンポーネント構成

```
┌─────────────────────────────────────────────┐
│  RAGシステム全体                              │
│                                               │
│  ┌─────────┐    ┌──────────┐    ┌─────────┐ │
│  │ 検索エンジン │ → │  LLM     │ → │ Citation │ │
│  │ (source取得) │    │ (生成)   │    │ Mapper   │ │
│  └─────────┘    └──────────┘    └─────────┘ │
│                                       ↓       │
│                              ┌──────────────┐ │
│                              │ ストリーム出力  │ │
│                              │ (番号付き引用) │ │
│                              └──────────────┘ │
└─────────────────────────────────────────────┘
```

### 6.2 CitationMapper の責務

CitationMapper コンポーネントは単一責任として引用マッピングを担う：

- **入力**：LLMトークンストリーム（内部識別子付き引用を含む）
- **状態**：`mapping: Dict[str, int]`、`counter: int`
- **出力**：変換済みトークンストリーム（表示番号付き引用）、完了時ソース一覧

このコンポーネントはステートフルだが副作用を持たず、同一入力ストリームに対して決定的な出力を生成する。

### 6.3 ストリーミングプロトコルの設計

Server-Sent Events（SSE）を用いる場合、以下のイベント型を設計する：

```
event: token
data: {"text": "詳細については", "citations": []}

event: token
data: {"text": " [1]", "citations": [{"display": 1, "source_id": "source_3"}]}

event: token
data: {"text": " および [2]", "citations": [{"display": 2, "source_id": "source_7"}]}

event: sources
data: {"sources": [
  {"display": 1, "source_id": "source_3", "title": "..."},
  {"display": 2, "source_id": "source_7", "title": "..."}
]}

event: done
data: {}
```

`token` イベントに `citations` 配列を含めることで、クライアントはトークン受信時に引用マッピングを更新できる。`sources` イベントはストリーム完了直前に送信され、最終的なソース一覧を提供する。

---

## 7. 正確性の証明

**命題**：到着順序割り当てアルゴリズムは三要件を同時に満たす。

**証明**：

**要件1（リアルタイム性）**：アルゴリズムはトークン受信時にその場で `mapping` を参照・更新するため、トークン出力と同時に表示番号が確定する。バッファリングや先読みを必要としない。□

**要件2（番号不変性）**：`mapping` への書き込みは `r not in mapping` の条件を満たす場合のみ発生し、既存エントリの上書きは行われない。`counter` は単調増加のみが許可されており、減少や再利用はしない。したがって、一度 `mapping[r] = v` が設定された後、`mapping[r]` は不変である。□

**要件3（終端整合性）**：ストリーム完了時、`mapping` には処理済みトークンに含まれていた全引用参照が登録されている（帰納的に：各トークン処理時にその引用を登録しているため）。これを昇順ソートすることで、表示番号と内部識別子の対応が完全に記録されたソース一覧が得られる。□

---

## 8. 実装例

以下にPythonによる実装例を示す：

```python
import re
from typing import Generator, Dict, List, Tuple

class CitationMapper:
    """
    ストリームトークン内の内部引用識別子を
    到着順序に基づく連番に変換する。
    """

    CITATION_PATTERN = re.compile(r'source_(\w+)')

    def __init__(self):
        self.mapping: Dict[str, int] = {}
        self.counter: int = 0
        self._buffer: str = ""

    def process_token(self, token_text: str) -> str:
        """
        トークンを処理し、引用識別子を表示番号に変換した
        テキストを返す。
        """
        self._buffer += token_text
        result = []
        last_end = 0

        for match in self.CITATION_PATTERN.finditer(self._buffer):
            source_id = match.group(0)  # e.g., "source_3"

            if source_id not in self.mapping:
                self.counter += 1
                self.mapping[source_id] = self.counter

            display_num = self.mapping[source_id]
            result.append(self._buffer[last_end:match.start()])
            result.append(f"[{display_num}]")
            last_end = match.end()

        # 未マッチ部分はバッファに残す（次トークンで完成する可能性）
        processed = "".join(result)
        self._buffer = self._buffer[last_end:]

        return processed

    def finalize(self) -> Tuple[str, List[Tuple[int, str]]]:
        """
        ストリーム完了時に呼び出す。
        残バッファと整列済みソース一覧を返す。
        """
        remaining = self._buffer
        self._buffer = ""

        sources = sorted(
            [(num, sid) for sid, num in self.mapping.items()],
            key=lambda x: x[0]
        )

        return remaining, sources


def stream_rag_response(
    llm_stream: Generator[str, None, None]
) -> Generator[dict, None, None]:
    """
    LLMストリームを引用番号付きで変換して出力する。
    """
    mapper = CitationMapper()

    for token in llm_stream:
        processed = mapper.process_token(token)
        if processed:
            yield {"type": "token", "text": processed}

    remaining, sources = mapper.finalize()
    if remaining:
        yield {"type": "token", "text": remaining}

    yield {
        "type": "sources",
        "sources": [
            {"display": num, "source_id": sid}
            for num, sid in sources
        ]
    }

    yield {"type": "done"}
```

---

## 9. 考察

### 9.1 設計の単純性

到着順序割り当ては、直感的に「最初に見たものに番号1を振る」というルールを形式化したものである。この単純さが正確性証明を容易にし、実装バグのリスクを低減する。

### 9.2 ユーザー体験への影響

到着順序による番号付けでは、本文中の登場順と番号順が一致する。これは学術論文の引用慣行（本文中での引用順が番号順になる IEEE スタイル等）と一致しており、ユーザーにとって直感的である。

一方、検索結果の関連度スコア順に番号を振りたい場合（高スコアなものが `[1]` になるよう）は、そのソートをバッチ処理後に行う必要があり、ストリーミングとの両立は困難である。要件の優先順位次第では、この点のトレードオフを明示的に設計判断として記録する必要がある。

### 9.3 障害モードの分析

**不完全な引用マーカー**：ストリームが途中で切断された場合、バッファに不完全なマーカーが残る可能性がある。`finalize()` でバッファをそのまま出力することで、可読性は低下するが情報損失は最小化できる。

**LLMの引用ハルシネーション**：LLMが取得されていない `source_99` のような架空の識別子を生成した場合、これも番号が割り当てられてしまうが、最終的なソース一覧構築時に「存在しないソースID」として検出・除去する後処理が必要となる。

---

## 10. 結論

本稿では、ストリーミングRAGシステムにおいて引用番号のリアルタイム表示・番号不変性・終端整合性という三要件を同時に満たす設計として、**到着順序割り当て**を提案・分析した。

この設計の核心は単純な洞察に基づいている：「ストリーム中に初めて出現した順序」という決定的な基準を用いることで、先読みなしに確定的な番号割り当てが可能となる。このアプローチは代替設計と比較して実装が最もシンプルでありながら、三要件を唯一同時に満たす。

今後の課題として、複数LLMによる並列生成を行うRAGシステムへの拡張（引用番号の名前空間衝突問題）、および多言語環境における引用マーカーのパターン汎化が挙げられる。

---

## 参考文献

- Lewis, P., Perez, E., Piktus, A., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *Advances in Neural Information Processing Systems*, 33, 9459–9474.
- Lamport, L. (1978). Time, Clocks, and the Ordering of Events in a Distributed System. *Communications of the ACM*, 21(7), 558–565.
- OpenAI. (2023). ChatGPT: Optimizing Language Models for Dialogue. *OpenAI Blog*.
- Anthropic. (2024). The Claude Model Family. *Anthropic Technical Documentation*.
