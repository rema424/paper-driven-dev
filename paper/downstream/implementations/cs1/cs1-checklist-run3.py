"""
CS1-D-Run3: RAG Streaming Citation Renumberer

Design guidance: CS1 条件D Structured Checklist Run 3
Key principles from the analysis:
- Separate internal ID from display number (section 7.1).
- Use a monotone-increase map: if source_id not in map -> assign next_index (section 7.2).
- The map IS the single source of truth for the final source list (section 7.1);
  not re-derived from body text.
- On stream completion, source list is generated from the map in assignment order
  (section 7.2).

Input tokens arrive as raw LLM text containing source_N patterns directly
(e.g., "See source_3 and source_7.").
The process_token method detects these via regex and replaces with [M].
"""

import re


class CitationRenumberer:
    """Replace source_N patterns with [M] by first-appearance order.

    Implements the monotone-increase map approach from CS1-D-Run3 analysis.

    The assignment map is the sole source of truth:
      if source_id not in map: map[source_id] = next_index; next_index += 1
    Final source list comes directly from iterating the map in insertion order.
    """

    _PATTERN = re.compile(r'source_\d+')

    def __init__(self):
        # Monotone-increase map: source_id -> display_num (insertion-ordered).
        # This is the sole source of truth per section 7.1.
        self._map: dict[str, int] = {}
        self._next_index: int = 1

    def _assign_or_lookup(self, source_id: str) -> int:
        """Assign a new display number if source_id is first seen.

        Implements the core rule from section 7.2:
          if source_id not in map: map[source_id] = next_index; next_index += 1
        Returns the (new or existing) display number.
        """
        if source_id not in self._map:
            self._map[source_id] = self._next_index
            self._next_index += 1
        return self._map[source_id]

    def process_token(self, token: str) -> str:
        """Replace source_N patterns with [M] by first-appearance order.

        Each source_N in the token is processed through the monotone-increase
        map. The token is returned with all occurrences replaced by [map[source_id]].
        Immediately outputs [n] which is immutable once assigned.
        """
        def replace(match: re.Match) -> str:
            return f'[{self._assign_or_lookup(match.group(0))}]'

        return self._PATTERN.sub(replace, token)

    def get_source_list(self) -> list[tuple[int, str]]:
        """Return [(display_num, original_source_id), ...] ordered by display_num.

        The map is the sole source of truth (section 7.1); no re-parsing of
        emitted text. Sorted by assigned display number to match insertion order.
        """
        return sorted(
            ((num, sid) for sid, num in self._map.items()),
            key=lambda pair: pair[0]
        )
