"""
CS1 Paper-Format Run 2 — Online Citation Renumbering
Design source: docs/examples/fullpaper/cs1-paper-format-run2.md

Design: "Monotonic First-Seen Mapping" (初出順・単調割当て)

The analysis proposes the following state:
    id2num:   Map<source_id, int>   — the monotonic mapping (append-only)
    num2id:   Array<source_id>      — 1-indexed list of source_ids by display number
    next_num: int                   — starts at 1

Algorithm (onCitation):
    if source_id not in id2num:
        id2num[source_id] = next_num
        num2id[next_num]  = source_id
        next_num += 1
    emit("[" + id2num[source_id] + "]")

Three properties satisfied:
    命題1 (リアルタイム性): immediate emit on detection.
    命題2 (番号不変):       id2num is append-only, never updated.
    命題3 (完了時整合):     bibliography from num2id matches all emitted [N].

Implementation note: the analysis uses <cite id="source_N"/> XML tags, but this
implementation processes RAW LLM text where citations appear as bare `source_N`
tokens. A regex over `source_\\d+` patterns is used.
"""

import re


class CitationRenumberer:
    """
    Processes streaming tokens, replacing source_N patterns with [N] display
    numbers by Monotonic First-Seen Mapping.

    State:
        _id2num  (id2num):   source_id -> display_number (append-only, never updated)
        _num2id  (num2id):   list of source_ids ordered by display_number (0-indexed,
                             display = index + 1)
        _next_num:           next display number to assign (starts at 1)
    """

    def __init__(self):
        # id2num: monotonic mapping — append-only, existing keys never updated
        self._id2num: dict[str, int] = {}
        # num2id: index 0 corresponds to display number 1
        self._num2id: list[str] = []
        self._next_num: int = 1

    def _on_citation(self, source_id: str) -> str:
        """
        Assign or retrieve display number for source_id.
        Implements the monotonic first-seen property: id2num is only extended,
        never modified for an existing key.
        Returns the formatted "[N]" string.
        """
        if source_id not in self._id2num:
            self._id2num[source_id] = self._next_num
            self._num2id.append(source_id)
            self._next_num += 1
        return f"[{self._id2num[source_id]}]"

    def process_token(self, token: str) -> str:
        """Replace source_N patterns with [N] by first-appearance order."""
        def replace(match: re.Match) -> str:
            return self._on_citation(match.group(0))

        return re.sub(r"source_\d+", replace, token)

    def get_source_list(self) -> list[tuple[int, str]]:
        """Return [(1, "source_3"), (2, "source_7")] ordered by display number.

        Generated from num2id (bibliography), guaranteeing 命題3 consistency:
        every [N] emitted during streaming corresponds to exactly one entry here.
        """
        return [(i + 1, sid) for i, sid in enumerate(self._num2id)]
