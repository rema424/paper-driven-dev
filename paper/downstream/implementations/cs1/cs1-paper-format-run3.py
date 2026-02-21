"""
CS1 Paper-Format Run 3 — Online Citation Renumbering
Design source: docs/examples/fullpaper/cs1-paper-format-run3.md

Design: "Online Monotonic Allocation" (初出順単調割当方式)

Formal model from the analysis:
    map M = {}       # source_id -> citation_number (undefined→defined, one-time transition)
    list L = []      # citation_number-ordered list of source_ids
    next = 1

    on_citation(ids):
        for s in ids:
            if s not in M:
                M[s] = next
                L.append(s)
                next += 1
            emit_inline_citation([M[s]])

    on_finalize():
        for i, s in enumerate(L, start=1):
            emit_bibliography_item(i, metadata(s))

Key properties:
    リアルタイム表示: O(1) hash lookup per citation, immediate emit.
    番号不変性:       M[s] transitions once (undefined→defined); no update branch exists.
    完了時整合性:     bibliography and inline citations share the same M/L state.

The analysis uses <<cite:source_7>> structured tokens, but this implementation
processes RAW LLM text where citations appear as bare `source_N` tokens.
A regex over `source_\\d+` patterns replaces the structured-token detection.
"""

import re


class CitationRenumberer:
    """
    Processes streaming tokens, replacing source_N patterns with [N] display
    numbers by Online Monotonic Allocation.

    Formal invariant: M is a one-time transition function — each key transitions
    exactly once from undefined to defined, never updated thereafter.

    State (shared between streaming and finalization):
        _M (map M): source_id -> citation_number (one-time transition)
        _L (list L): first-appearance ordered list of source_ids
        _next:       next citation number (starts at 1)
    """

    def __init__(self):
        # M: one-time transition map (undefined → defined)
        self._M: dict[str, int] = {}
        # L: first-appearance ordered list of source_ids
        self._L: list[str] = []
        self._next: int = 1

    def _on_citation(self, source_id: str) -> str:
        """
        Serialized allocation point for a single source_id.

        One-time transition: if source_id is not in M, assign M[s]=next and
        append to L. Existing keys are only read, never reassigned.
        Returns "[N]" for the assigned display number.
        """
        if source_id not in self._M:
            # Transition: undefined → defined (exactly once)
            self._M[source_id] = self._next
            self._L.append(source_id)
            self._next += 1
        return f"[{self._M[source_id]}]"

    def process_token(self, token: str) -> str:
        """Replace source_N patterns with [N] by first-appearance order."""
        def replace(match: re.Match) -> str:
            return self._on_citation(match.group(0))

        return re.sub(r"source_\d+", replace, token)

    def get_source_list(self) -> list[tuple[int, str]]:
        """Return [(1, "source_3"), (2, "source_7")] ordered by display number.

        on_finalize() equivalent: enumerates L using M for number lookup.
        Shares the same M/L state used during streaming, guaranteeing that
        all [N] in the output have a corresponding entry in this list (完了時整合性).
        """
        return [(self._M[key], key) for key in self._L]
