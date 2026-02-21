"""
CS1-D-Run1: RAG Streaming Citation Renumberer

Design guidance: CS1 条件D Structured Checklist Run 1
Key principles from the analysis:
- Separate internal source ID from display number [n] (section 7.1).
- Use first-seen (online) numbering: assign the next number only when a
  source_id is encountered for the first time in the stream (section 7.2-B).
- The assignment map is append-only; no re-numbering after the fact.
- The registry (ordered_sources) is the single source of truth for the
  final source list (section 7.2-D).

Input tokens arrive as raw LLM text containing source_N patterns directly
(e.g., "See source_3 for details about source_7.").
The process_token method detects these patterns via regex and replaces them
with display numbers [M] by first-appearance order.
"""

import re


class CitationRenumberer:
    """Replace source_N patterns with [M] by first-appearance order.

    Implements the server-side citation number registry described in the
    Run 1 analysis (section 7.2-B):
      - map[source_key] -> n  (source ID to display number)
      - ordered_sources       (insertion-order list of (n, source_id))
      - next_id counter       (monotonically increasing, never decremented)

    The regex pattern ``source_\\d+`` is used to detect citations directly in
    the raw LLM stream text, consistent with the actual input format.
    """

    _PATTERN = re.compile(r'source_\d+')

    def __init__(self):
        # Registry: source_id -> assigned display number (1-based, append-only).
        self._registry: dict[str, int] = {}
        # Ordered list preserving first-appearance order: (display_num, source_id).
        self._ordered: list[tuple[int, str]] = []
        # Next display number to assign (monotonically increasing).
        self._next: int = 1

    def process_token(self, token: str) -> str:
        """Replace source_N patterns with [M] by first-appearance order.

        For each source_N occurrence in token:
          - If seen before, reuse the previously assigned display number.
          - If new, assign the next available number (first-seen rule).
        Returns the token with all source_N references replaced by [M].
        """
        def replace(match: re.Match) -> str:
            source_id = match.group(0)
            if source_id not in self._registry:
                num = self._next
                self._registry[source_id] = num
                self._ordered.append((num, source_id))
                self._next += 1
            return f'[{self._registry[source_id]}]'

        return self._PATTERN.sub(replace, token)

    def get_source_list(self) -> list[tuple[int, str]]:
        """Return sources ordered by display number (first-appearance order).

        Returns a list of (display_number, source_id) tuples, e.g.:
          [(1, "source_3"), (2, "source_7")]
        This list is derived solely from the append-only registry (section 7.1),
        making it the single source of truth consistent with the displayed text.
        """
        return list(self._ordered)
