"""
CS1 Paper-Format Run 4 — Online Citation Renumbering
Design source: docs/examples/fullpaper/cs1-paper-format-run4.md

Design: "First-Appearance Online Numbering" (初出順オンライン番号付与方式)

Data structures from the analysis:
    R:    set of valid source IDs (pre-registered retrieval results)
    M:    source_id -> citation_number (immutable HashMap, monotone-append-only)
    next: int (starting at 1)

Processing (for each citation reference):
    if c not in R:
        mark as unresolved (emit "[?]")
    elif c not in M:
        M[c] = next
        next += 1
    emit "[" + M[c] + "]"

Formal properties:
    命題1 (不変性):    M[c] is assigned on first occurrence only; no update branch.
    命題2 (リアルタイム性): O(1) per citation (HashMap lookup + constant operations).
    命題3 (最終整合性):    Final list B[k] = meta(M^{-1}(k)) consistent with inline [N].

The analysis uses [[source_N]] normalized tags with an FSM for chunk boundaries,
but this implementation processes RAW LLM text where citations appear as bare
`source_N` tokens. A regex over `source_\\d+` patterns is used instead.
"""

import re


class CitationRenumberer:
    """
    Processes streaming tokens, replacing source_N patterns with [N] display
    numbers by First-Appearance Online Numbering.

    Source IDs not in the pre-registered valid set R emit "[?]".
    If no valid_sources set is provided, all IDs are accepted.

    命題1 (Immutability): M[c] is set once; the update operation does not exist.
    """

    def __init__(self, valid_sources: set[str] | None = None):
        """
        Args:
            valid_sources: Set R of valid source IDs from the retrieval result set.
                           IDs outside R emit "[?]". Pass None to accept all IDs.
        """
        # R: valid source ID set (retrieval result set)
        self._R: set[str] | None = valid_sources
        # M: immutable HashMap — source_id -> citation_number (append-only)
        self._M: dict[str, int] = {}
        # Ordered list of source_ids preserving insertion order (for M^{-1})
        self._ordered: list[str] = []
        self._next: int = 1

    def _assign(self, source_id: str) -> str:
        """
        Assign or retrieve display number for source_id.

        命題1: M[source_id] is assigned at most once. The branch that would
        update an existing key does not exist in this implementation.

        Returns "[N]" or "[?]" for IDs outside valid_sources (R).
        """
        if self._R is not None and source_id not in self._R:
            return "[?]"
        if source_id not in self._M:
            self._M[source_id] = self._next
            self._ordered.append(source_id)
            self._next += 1
        return f"[{self._M[source_id]}]"

    def process_token(self, token: str) -> str:
        """Replace source_N patterns with [N] by first-appearance order."""
        def replace(match: re.Match) -> str:
            return self._assign(match.group(0))

        return re.sub(r"source_\d+", replace, token)

    def get_source_list(self) -> list[tuple[int, str]]:
        """Return [(1, "source_3"), (2, "source_7")] ordered by display number.

        命題3 (最終整合性): Generated from the same M used during streaming.
        Every [N] emitted has exactly one entry in this list; every entry
        corresponds to exactly one [N] in the output.
        """
        return [(self._M[sid], sid) for sid in self._ordered]
