# Implementation Task: RAG Streaming Citation Renumbering

## Problem Statement

RAGシステムでは、LLMが検索結果（例: source_3, source_7）を参照しながらストリーミングで回答を生成します。ユーザーには [1], [2], [3] のような読みやすい連番で引用を表示したいのですが、ストリーミング中は全文が確定していないため、最終的にどの引用が使われるかわかりません。

以下の要件を満たす実装を作成してください:
- ストリーミング中にリアルタイムで引用番号を表示する
- 一度表示した番号が後から変わらない
- ストリーム完了時にソース一覧と整合している

## Design Analysis

The following design analysis was produced for this problem. Use it to guide your implementation.

---
{design_document}
---

## Interface Specification

You MUST implement a class that conforms to this interface:

```python
from abc import ABC, abstractmethod

class CitationRenumberer(ABC):
    @abstractmethod
    def process_token(self, token: str) -> str:
        """Process a single streaming token.
        Replace any source references (source_N) with sequential display
        numbers ([M]) based on order of first appearance.
        Args:
            token: A text token from the LLM stream. May contain zero, one,
                   or multiple source references.
        Returns:
            The token with source references replaced by display numbers.
        """
        ...

    @abstractmethod
    def get_source_list(self) -> list[tuple[int, str]]:
        """Return the source list after stream processing.
        Returns:
            List of (display_number, original_source_id) tuples,
            ordered by display number.
            Example: [(1, "source_3"), (2, "source_7")]
        """
        ...
```

## Instructions

1. Read the design analysis carefully
2. Implement a concrete Python class that inherits from CitationRenumberer
3. Your implementation should reflect the design decisions and insights from the analysis
4. The implementation must be a single Python file
5. Include all necessary imports (including `import re` if needed)
6. Do NOT import from external packages — use only the Python standard library
7. Do NOT import the ABC class from a file — redefine CitationRenumberer as a plain class or just implement the methods directly
8. Your concrete class MUST have `process_token` and `get_source_list` methods with the exact signatures above

Output ONLY the Python code. No explanations, no markdown fences.
