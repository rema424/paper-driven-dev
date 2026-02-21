"""
CS1-C-Run2: RAG Streaming Citation Renumberer
Design basis: First-mention Commit with Citation Ledger

Design decisions reflected from Run2 analysis (§5 提案手法):
- Named components: Source Registry, Citation Allocator (core),
  Citation Ledger, End-of-Stream List Builder.
- "初出コミット方式 (First-mention Commit)": the moment a source_id is first
  confirmed in the stream its display number is committed and never changed.
- source_N patterns appear directly in raw LLM output text; regex matches them.
- Citation Ledger records (n, source_id) in first-mention order as an
  append-only audit trail (§5.2 item 5).
- End-of-Stream List Builder generates the final source list from the Ledger,
  guaranteeing 1-to-1 correspondence with the body text (§6 性質3).
- Unknown IDs (not previously seen) are still allocated; the interface provides
  no external registry at construction time, so all seen IDs are treated as valid.
- Idempotence (§6 性質1, 2): same source_id always yields the same number.
"""

import re


class CitationRenumberer:
    """
    Implements the First-mention Commit strategy with Citation Ledger.

    Components
    ----------
    Citation Allocator : self._allocator — assigns/reuses display numbers.
    Citation Ledger    : self._ledger   — append-only (num, source_id) log.
    List Builder       : get_source_list — reads ledger for output.
    """

    # Matches source_N identifiers directly in raw LLM output text.
    _SOURCE_RE = re.compile(r'source_\d+')

    def __init__(self) -> None:
        # Citation Allocator state.
        self._allocator: dict[str, int] = {}  # source_id -> display_number
        self._next: int = 1

        # Citation Ledger: append-only, first-mention order.
        self._ledger: list[tuple[int, str]] = []

    def _commit(self, source_id: str) -> int:
        """
        First-mention commit: assign and record display number for source_id.

        Returns the (possibly pre-existing) display number.
        On first appearance: allocates next number and appends to Ledger.
        On subsequent appearances: returns existing number without mutation.
        """
        if source_id not in self._allocator:
            num = self._next
            self._allocator[source_id] = num
            self._next += 1
            self._ledger.append((num, source_id))
        return self._allocator[source_id]

    def process_token(self, token: str) -> str:
        """
        Replace source_N patterns with [M] by first-appearance order.

        Each source_N in the token is looked up in the Citation Allocator.
        First occurrence triggers a commit to the Ledger; re-occurrences
        simply reuse the existing number.
        """
        def _sub(m: re.Match) -> str:
            return f"[{self._commit(m.group(0))}]"
        return self._SOURCE_RE.sub(_sub, token)

    def get_source_list(self) -> list[tuple[int, str]]:
        """
        End-of-Stream List Builder.

        Returns the source list derived directly from the Citation Ledger —
        the append-only audit trail that guarantees correspondence with the
        body text.  The list is already in first-mention (display-number) order.
        """
        return list(self._ledger)
