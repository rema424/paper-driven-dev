"""
CS1-D-Run4: RAG Streaming Citation Renumberer

Design guidance: CS1 条件D Structured Checklist Run 4
Key principles from the analysis:
- Separate citation ID (source_7) from display number ([2]) (section 7.1).
- CitationAllocator: Map<source_id, number> + next_number (section 7.2).
- New ID detected: assign next_number only at first confirmed detection (section 7.1).
- Known ID: reuse existing number without consuming next_number (section 7.2).
- Allocation map is append-only; no re-numbering (section 7.1).
- Source list is generated from the allocator map sorted by number,
  not from body text re-scan (section 7.2).
- On completion, verify body citation number set matches source list number set
  (section 7.2).

Input tokens arrive as raw LLM text containing source_N patterns directly
(e.g., "source_3 explains this. See also source_7.").
The process_token method detects these via regex and replaces with [M].
"""

import re


class CitationRenumberer:
    """Replace source_N patterns with [M] by first-appearance order.

    Implements the CitationAllocator design from CS1-D-Run4 analysis.

    Allocation state:
      _map         - Map<source_id, number> (append-only)
      _next_number - next number to assign (monotonically increasing)

    Body tracking for post-stream verification:
      _body_nums   - set of display numbers emitted to body text
    """

    _PATTERN = re.compile(r'source_\d+')

    def __init__(self):
        # CitationAllocator state as described in section 7.2.
        self._map: dict[str, int] = {}
        self._next_number: int = 1
        # Numbers emitted in body text for completion-time verification.
        self._body_nums: set[int] = set()

    def _allocate(self, source_id: str) -> int:
        """Allocate display number for source_id.

        Assigns next_number on first encounter; returns existing number on
        subsequent encounters. The map is append-only per section 7.1.
        """
        if source_id not in self._map:
            num = self._next_number
            self._map[source_id] = num
            self._next_number += 1
        return self._map[source_id]

    def process_token(self, token: str) -> str:
        """Replace source_N patterns with [M] by first-appearance order.

        Each source_N is processed through the CitationAllocator. The
        token is returned with all source_N occurrences replaced by [M].
        Display numbers are immediately stable once assigned.
        """
        def replace(match: re.Match) -> str:
            source_id = match.group(0)
            num = self._allocate(source_id)
            self._body_nums.add(num)
            return f'[{num}]'

        return self._PATTERN.sub(replace, token)

    def get_source_list(self) -> list[tuple[int, str]]:
        """Return [(display_num, original_source_id), ...] ordered by display_num.

        Source list is generated from the allocator map sorted by number,
        not derived from body text re-scan (section 7.2).
        """
        return sorted(
            ((num, sid) for sid, num in self._map.items()),
            key=lambda pair: pair[0]
        )

    def verify(self) -> bool:
        """Post-stream integrity check: body citation numbers == source list numbers.

        Returns True when the set of numbers emitted in body text exactly matches
        the set of numbers in the final source list (section 7.2).
        """
        list_nums = {num for num, _ in self.get_source_list()}
        return self._body_nums == list_nums
