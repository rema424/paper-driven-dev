"""
CS1-D-Run2: RAG Streaming Citation Renumberer

Design guidance: CS1 条件D Checklist Run 2
Key principles from the analysis:
- The true key is source_id, not the display number (section 7.1).
- Display number is assigned once on first sight of a source_id (section 7.1).
- The assignment map is append-only: only additions, no re-numbering (section 7.1).
- CitationRegistry holds: id2num (Map), num2id (Array), next counter (section 7.2).
- On detection: if unknown, assign next; if known, reuse existing num (section 7.2).
- Final source list is built from num2id in order (section 7.2).

Input tokens arrive as raw LLM text containing source_N patterns directly
(e.g., "See source_7 details. Also source_3.").
The process_token method detects these via regex and replaces with [M].
"""

import re


class CitationRenumberer:
    """Replace source_N patterns with [M] by first-appearance order.

    Implements the CitationRegistry approach from CS1-D-Run2 analysis.

    Internal state mirrors the analysis description:
      id2num  - source_id -> display_num mapping (append-only)
      num2id  - ordered list of source_ids indexed by (display_num - 1)
      next    - next display number to assign (starts at 1)
    """

    _PATTERN = re.compile(r'source_\d+')

    def __init__(self):
        # CitationRegistry state as described in section 7.2.
        self.id2num: dict[str, int] = {}
        self.num2id: list[str] = []  # index 0 corresponds to display_num 1
        self.next: int = 1

    def _register(self, source_id: str) -> int:
        """Assign a display number on first sight; return existing on repeat.

        Implements the append-only map: only new entries are added,
        existing entries are never modified.
        """
        if source_id not in self.id2num:
            num = self.next
            self.id2num[source_id] = num
            self.num2id.append(source_id)
            self.next += 1
        return self.id2num[source_id]

    def process_token(self, token: str) -> str:
        """Replace source_N patterns with [M] by first-appearance order.

        Each source_N found in the token is looked up or registered in the
        CitationRegistry. The token is returned with all source_N occurrences
        replaced by their stable display numbers [M].
        """
        def replace(match: re.Match) -> str:
            return f'[{self._register(match.group(0))}]'

        return self._PATTERN.sub(replace, token)

    def get_source_list(self) -> list[tuple[int, str]]:
        """Return [(display_num, original_source_id), ...] ordered by display_num.

        Built from num2id (insertion order) as described in section 7.2:
        num2id order gives the final source list.
        """
        return [(i + 1, sid) for i, sid in enumerate(self.num2id)]
