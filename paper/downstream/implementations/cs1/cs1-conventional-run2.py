"""
CS1 Conventional Run 2 — Incremental citation parser with citation_map

Design basis: CS1-A-Run2 analysis
Architecture: LLM/source layer separation; display numbers assigned purely
              in the streaming layer via an incremental (chunk-aware) parser.
Marker format: source_N appearing directly in raw LLM output text.
Key decisions from analysis:
  - LLM outputs internal IDs only; '[1]' style numbers are *never* generated
    by the LLM — the streaming layer owns all numbering.
  - citation_map is append-only (追記のみ、再採番しない).
  - source_id not present in the retrieved sources set returns "[?]" and
    is NOT added to citation_map (invalid ID policy: strict reject).
  - Incremental parser handles chunk-split patterns across token boundaries.
  - The same citation_map is the single source of truth for get_source_list().
"""

import re


class CitationRenumberer:
    """
    Streaming citation renumberer based on the Run 2 incremental-parser design.

    Source references appear as source_N (e.g., source_3, source_7) directly
    in the raw LLM output text.

    Invalid source IDs (not in the retrieved set) produce "[?]" and are
    excluded from the citation map and source list entirely.

    To use with a known set of retrieved sources, pass them at construction:
        renumberer = CitationRenumberer(retrieved={"source_3", "source_7"})
    If retrieved is None (default), all source IDs are accepted.
    """

    # Matches a complete source_N pattern
    _SOURCE_RE = re.compile(r'source_\d+')
    # Detects a trailing partial source_N that may continue in the next token
    _PARTIAL_RE = re.compile(r's(?:o(?:u(?:r(?:c(?:e(?:_\d*)?)?)?)?)?)?$')

    def __init__(self, retrieved: set[str] | None = None) -> None:
        # Set of source IDs that the retrieval layer returned (optional guard)
        self._retrieved: set[str] | None = retrieved
        # citation_map: source_id -> display_number (append-only, never mutated)
        self._citation_map: dict[str, int] = {}
        # Insertion-ordered list for get_source_list()
        self._ordered: list[tuple[int, str]] = []
        self._next_number: int = 1
        # Incremental parse buffer
        self._buf: str = ""

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def process_token(self, token: str) -> str:
        """
        Feed a streaming token; return displayable text with citations replaced.

        '[?]' is emitted for unrecognised source IDs (not in retrieved set).
        """
        self._buf += token
        return self._drain()

    def get_source_list(self) -> list[tuple[int, str]]:
        """
        Return [(display_num, source_id), ...] in first-appearance order.

        Uses citation_map as the single source of truth, matching the Run 2
        design principle that the map is "唯一の真実源".
        """
        # Flush any remaining buffered content
        if self._buf:
            remaining = self._buf
            self._buf = ""
            self._SOURCE_RE.sub(self._resolve_match, remaining)
        return list(self._ordered)

    # ------------------------------------------------------------------
    # Internal implementation
    # ------------------------------------------------------------------

    def _drain(self) -> str:
        """
        Drain the buffer: emit all text that is definitively not a partial pattern.
        """
        text = self._buf

        # Find where a partial source_N could start at the tail
        m = self._PARTIAL_RE.search(text)
        if m:
            safe_text = text[:m.start()]
            self._buf = text[m.start():]
        else:
            safe_text = text
            self._buf = ""

        return self._SOURCE_RE.sub(self._resolve_match, safe_text)

    def _resolve_match(self, m: re.Match) -> str:
        """Replacement callback: map source_id to display citation string."""
        return self._resolve(m.group(0))

    def _resolve(self, source_id: str) -> str:
        """
        Map source_id to display citation string.

        - If retrieved set is provided and source_id is absent: return "[?]"
        - Otherwise: register on first occurrence and return "[n]"
        """
        if self._retrieved is not None and source_id not in self._retrieved:
            return "[?]"

        if source_id not in self._citation_map:
            num = self._next_number
            self._next_number += 1
            self._citation_map[source_id] = num
            self._ordered.append((num, source_id))

        return f"[{self._citation_map[source_id]}]"
