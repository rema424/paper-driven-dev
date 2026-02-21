"""
CS1 Paper-Format Run 1 — Online Citation Renumbering
Design source: docs/examples/fullpaper/cs1-paper-format-run1.md

Design: "First-Use Numbering" (初出順番号付与)

The analysis proposes a Citation Resolver (middleware) that maintains:
    M: source_key -> int  (assigned display number)
    L: [source_key]       (first-appearance ordered list)
    next: int             (next number to assign, starting at 1)

On detecting a citation reference:
    - If the key is unseen, assign M[key]=next, append to L, increment next.
    - Replace the reference with [M[key]].

Immutability guaranteed: M is monotone-append-only (existing keys never reassigned).
Consistency: get_source_list() is generated from the same L and M used during streaming.

Implementation note: the analysis describes ⟦cite:source_key⟧ as the marker format,
but this implementation processes RAW LLM text where citations appear as bare
`source_N` tokens (e.g. "source_3", "source_7"). A regex find-and-replace over
`source_\\d+` patterns is used instead of marker-based buffering.
"""

import re


class CitationRenumberer:
    """
    Processes streaming tokens, replacing source_N patterns with [M] display
    numbers assigned by first-appearance order (First-Use Numbering).

    State (Citation Resolver):
        _mapping (M): source_key -> display_number (monotone, append-only)
        _ordered (L): first-appearance ordered list of source keys
        _next:        next display number to assign (starts at 1)
    """

    def __init__(self):
        # M: source_key -> display number (monotone, append-only)
        self._mapping: dict[str, int] = {}
        # L: first-appearance ordered list of source keys
        self._ordered: list[str] = []
        # next number to assign
        self._next: int = 1

    def _assign(self, key: str) -> int:
        """
        Assign or retrieve the display number for key.
        M is only ever extended (monotone): existing entries are never updated.
        """
        if key not in self._mapping:
            self._mapping[key] = self._next
            self._ordered.append(key)
            self._next += 1
        return self._mapping[key]

    def process_token(self, token: str) -> str:
        """Replace source_N patterns with [M] by first-appearance order."""
        def replace(match: re.Match) -> str:
            key = match.group(0)  # e.g. "source_3"
            return f"[{self._assign(key)}]"

        return re.sub(r"source_\d+", replace, token)

    def get_source_list(self) -> list[tuple[int, str]]:
        """Return [(1, "source_3"), (2, "source_7")] ordered by display number."""
        return [(self._mapping[key], key) for key in self._ordered]
