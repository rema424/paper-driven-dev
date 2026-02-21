"""
CS1 Conventional Run 3 — Event-driven citation registration (immutable map)

Design basis: CS1-A-Run3 analysis
Architecture: "引用イベント駆動 + 初出固定番号" (citation-event-driven + first-seen fixed number)
Marker format: source_N appearing directly in raw LLM output text.
Key decisions from analysis:
  - Immutable map: once source_id -> number is written it is NEVER changed.
  - Unknown source IDs are treated as errors; they do NOT get a number and
    the pattern is replaced with an error indicator "[!unknown:source_id]".
  - On citation registration an internal event is fired (citation_registered),
    which callers can observe by providing a callback.
  - Numbering unit is per-response (not per-conversation).
  - The algorithm from the analysis is followed directly:
      on cite(source_id):
        if source_id not in map:
          map[source_id] = next_number
          next_number += 1
          emit citation_registered(map[source_id], source_id)
        emit text("[{map[source_id]}]")
"""

import re
from typing import Callable


class CitationRenumberer:
    """
    Event-driven citation renumberer following the Run 3 design.

    Source references appear as source_N (e.g., source_3, source_7) directly
    in the raw LLM output text.

    Unknown source IDs (not in the allowed set, if provided) are rejected
    with an error placeholder rather than receiving a number — they are
    never silently accepted into the registry.

    Optional callback:
        on_citation_registered(display_num: int, source_id: str) -> None
    Fires exactly once per unique source_id when it is first assigned a number.
    """

    _SOURCE_RE = re.compile(r'source_\d+')
    # Trailing partial that might continue into the next token
    _PARTIAL_RE = re.compile(r's(?:o(?:u(?:r(?:c(?:e(?:_\d*)?)?)?)?)?)?$')

    def __init__(
        self,
        allowed_sources: set[str] | None = None,
        on_citation_registered: Callable[[int, str], None] | None = None,
    ) -> None:
        # Optional whitelist; None means accept all IDs
        self._allowed: set[str] | None = allowed_sources
        # Observer callback for the "citation_registered" event
        self._on_registered = on_citation_registered
        # Immutable map (write-once invariant enforced by implementation)
        self._map: dict[str, int] = {}
        self._ordered: list[tuple[int, str]] = []
        self._next_number: int = 1
        # Streaming buffer for split-token handling
        self._buf: str = ""

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def process_token(self, token: str) -> str:
        """
        Accept a streaming token; return displayable text.

        source_N patterns are replaced with [n] (registered IDs) or
        [!unknown:source_id] (disallowed IDs).
        Text is held in the buffer only as long as it may be part of an
        incomplete source_N pattern; once confirmed safe it is released immediately.
        """
        self._buf += token
        return self._process_buffer()

    def get_source_list(self) -> list[tuple[int, str]]:
        """
        Return [(display_num, source_id), ...] ordered by first appearance.

        Reflects the "same map is the source of truth for the source list"
        principle from the Run 3 design.
        """
        # Flush remaining buffer
        if self._buf:
            remaining = self._buf
            self._buf = ""
            self._SOURCE_RE.sub(self._cite_match, remaining)
        return list(self._ordered)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_buffer(self) -> str:
        """Flush buffer, replacing complete patterns and holding partial ones."""
        text = self._buf

        m = self._PARTIAL_RE.search(text)
        if m:
            safe_text = text[:m.start()]
            self._buf = text[m.start():]
        else:
            safe_text = text
            self._buf = ""

        return self._SOURCE_RE.sub(self._cite_match, safe_text)

    def _cite_match(self, m: re.Match) -> str:
        """Replacement callback implementing the core Run 3 algorithm."""
        return self._on_cite(m.group(0))

    def _on_cite(self, source_id: str) -> str:
        """
        Core algorithm from Run 3 analysis:
          on cite(source_id):
            if source_id not in map:
              map[source_id] = next_number; next_number += 1
              emit citation_registered(...)
            emit text("[{map[source_id]}]")

        Returns the display string for this citation.
        Unknown IDs (not in allowed set) are rejected with an error string.
        """
        if self._allowed is not None and source_id not in self._allowed:
            return f"[!unknown:{source_id}]"

        if source_id not in self._map:
            num = self._next_number
            self._next_number += 1
            # Write once — never mutated again (immutable map invariant)
            self._map[source_id] = num
            self._ordered.append((num, source_id))
            # Fire registration event
            if self._on_registered is not None:
                self._on_registered(num, source_id)

        return f"[{self._map[source_id]}]"
