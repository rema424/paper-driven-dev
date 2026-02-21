"""
CS1-D-Run5: RAG Streaming Citation Renumberer

Design guidance: CS1 条件D Checklist Run 5
Key principles from the analysis:
- Separate "internal ID" from "display number" (section 7.1).
- Display number is assigned only on first appearance; thereafter immutable
  (section 7.1).
- Body display and citation events are saved as an append-only log (section 7.1).
- State held as three explicit fields per turn: display_no_by_source,
  source_by_display_no, next_no (section 7.2).
- On completion: build final source list from source_by_display_no order
  and verify body number set matches list number set (section 7.2).

Input tokens arrive as raw LLM text containing source_N patterns directly
(e.g., "source_7 is the primary reference. source_3 provides context.").
The process_token method detects these via regex and replaces with [M].
"""

import re


class CitationRenumberer:
    """Replace source_N patterns with [M] by first-appearance order.

    Implements the explicit triple-state design from CS1-D-Run5 analysis.

    State (per turn) as described in section 7.2:
      display_no_by_source: dict[str, int]  - source_id -> display number
      source_by_display_no: list[str]       - index (0-based) -> source_id
      next_no: int                          - next display number to assign

    Append-only event log:
      citation_bound_log: list[(source_id, display_num)]
    """

    _PATTERN = re.compile(r'source_\d+')

    def __init__(self):
        # Triple-state as described in section 7.2.
        self.display_no_by_source: dict[str, int] = {}
        self.source_by_display_no: list[str] = []
        self.next_no: int = 1

        # Append-only event log: citation_bound(source_id, display_num).
        # Emitted once per new source_id at time of first allocation.
        self.citation_bound_log: list[tuple[str, int]] = []

        # Numbers emitted in body text for post-stream verification.
        self._body_num_set: set[int] = set()

    def _allocate(self, source_id: str) -> int:
        """Allocate display_no for source_id on first appearance.

        Implements the first-seen assignment from section 7.2:
          if first: allocate next_no, emit citation_bound event.
        Returns the (new or existing) display number.
        """
        if source_id not in self.display_no_by_source:
            num = self.next_no
            self.display_no_by_source[source_id] = num
            self.source_by_display_no.append(source_id)
            self.next_no += 1
            # Append-only citation_bound event (section 7.1).
            self.citation_bound_log.append((source_id, num))
        return self.display_no_by_source[source_id]

    def process_token(self, token: str) -> str:
        """Replace source_N patterns with [M] by first-appearance order.

        Each source_N in the token is processed through the triple-state
        allocator. Returns the token with all source_N occurrences replaced
        by their immutable display numbers [M].
        """
        def replace(match: re.Match) -> str:
            source_id = match.group(0)
            num = self._allocate(source_id)
            self._body_num_set.add(num)
            return f'[{num}]'

        return self._PATTERN.sub(replace, token)

    def get_source_list(self) -> list[tuple[int, str]]:
        """Return [(display_num, original_source_id), ...] ordered by display_num.

        Built from source_by_display_no (insertion order) as described in
        section 7.2: source_by_display_no order gives the final source list.
        """
        return [(i + 1, sid) for i, sid in enumerate(self.source_by_display_no)]

    def verify_consistency(self) -> bool:
        """Post-stream verification: body numbers must exactly match source list numbers.

        Returns True when the set of numbers emitted in body text matches the
        set of numbers in the final source list (section 7.2 completion check).
        """
        list_nums = set(range(1, self.next_no))
        return self._body_num_set == list_nums
