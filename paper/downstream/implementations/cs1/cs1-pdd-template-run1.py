"""
CS1-C-Run1: RAG Streaming Citation Renumberer
Design basis: Monotonic Citation Allocation (MCA)

Design decisions reflected from Run1 analysis (§5 提案手法):
- Implements "単調引用割当 (Monotonic Citation Allocation; MCA)".
- The Citation Manager acts as a stateful transducer over the raw token stream.
- source_N patterns (e.g. source_3, source_7) appear directly in the LLM output;
  this processor intercepts them via regex and replaces with [n] on first appearance.
- The map (source_id -> number) is the single source of truth (§5.1); the
  References Builder derives the final source list from it at stream end.
- Once a number is assigned it is never changed (番号不変, §6 性質1).
- Only cited sources appear in the list (性質4 "使用したものだけ").
- No buffering is needed: source_N tokens are always complete (no split risk).
"""

import re


class CitationRenumberer:
    """
    Implements Monotonic Citation Allocation (MCA).

    The LLM emits raw source_N identifiers directly in the text stream.
    This Citation Manager replaces each source_N with a stable [n] display
    number assigned on first occurrence, maintaining the append-only map as
    the single source of truth.

    State (§5.2 Citation Manager):
        _map  : dict[str, int]  -- source_id -> display_number (append-only)
        _next : int             -- next display number to allocate
    """

    # Matches source_N identifiers directly in raw LLM output text.
    _SOURCE_RE = re.compile(r'source_\d+')

    def __init__(self) -> None:
        self._map: dict[str, int] = {}  # source_id -> display number (append-only)
        self._next: int = 1             # next number; increments monotonically

    def _allocate(self, source_id: str) -> int:
        """
        Allocate or reuse display number for source_id.

        First-appearance assignment: new source_id receives self._next and
        increments it.  Subsequent appearances return the same number (性質1).
        """
        if source_id not in self._map:
            self._map[source_id] = self._next
            self._next += 1
        return self._map[source_id]

    def process_token(self, token: str) -> str:
        """
        Replace source_N patterns with [M] by first-appearance order.

        Each source_N in the token is replaced inline.  The map is updated
        on first occurrence; re-occurrences reuse the existing number.
        No buffering is required because source_N is always a contiguous
        token with no split risk across chunk boundaries.
        """
        def _sub(m: re.Match) -> str:
            return f"[{self._allocate(m.group(0))}]"
        return self._SOURCE_RE.sub(_sub, token)

    def get_source_list(self) -> list[tuple[int, str]]:
        """
        Return [(display_num, source_id), ...] ordered by display_num.

        The References Builder reads directly from the single-source-of-truth
        map, guaranteeing correspondence with every [n] emitted in the body
        (§6 性質3: 完了時の一覧整合).  Only cited sources appear (性質4).
        """
        return sorted(
            ((num, sid) for sid, num in self._map.items()),
            key=lambda t: t[0],
        )
