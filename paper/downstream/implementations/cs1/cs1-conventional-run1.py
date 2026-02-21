"""
CS1 Conventional Run 1 — Citation Registry (first-appearance numbering)

Design basis: CS1-A-Run1 analysis
Architecture: Citation Registry held server-side during streaming.
Marker format: source_N appearing directly in raw LLM output text.
Key decisions from analysis:
  - map[source_id] -> number, written once, never changed
  - Invalid/unrecognised source IDs still get a number assigned and are
    flagged as "unresolved" in the source list (番号を後で詰めると要件違反)
  - Token-boundary split handled via internal buffer; regex finds
    source_N patterns and replaces with [n] on first appearance
"""

import re


class CitationRenumberer:
    """
    Citation Registry that processes streaming tokens one at a time.

    Source references appear as source_N (e.g., source_3, source_7) directly
    in the raw LLM output text. The registry replaces each with [n] by
    first-appearance order.

    The registry is append-only: once a source_id receives a display number
    that mapping is never changed, satisfying the immutability invariant.
    """

    # Matches source_N patterns directly in text
    _SOURCE_RE = re.compile(r'source_\d+')
    # A suffix that could be the start of a partial source_N token
    _PARTIAL_RE = re.compile(r's(?:o(?:u(?:r(?:c(?:e(?:_\d*)?)?)?)?)?)?$')

    def __init__(self) -> None:
        # Core registry: source_id -> display number (write-once)
        self._id_to_num: dict[str, int] = {}
        # Ordered record for get_source_list()
        self._ordered: list[tuple[int, str]] = []
        self._next_num: int = 1
        # Buffer for split tokens
        self._buf: str = ""

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def process_token(self, token: str) -> str:
        """
        Replace source_N patterns with [M] by first-appearance order.

        Tokens are buffered to handle cases where a source_N pattern
        arrives split across multiple tokens.
        """
        self._buf += token
        return self._flush()

    def get_source_list(self) -> list[tuple[int, str]]:
        """
        Return [(display_num, source_id), ...] ordered by first appearance.

        Call after streaming is complete. Any remaining buffer content is
        flushed first (handles streams that end without a trailing newline).
        """
        # Flush whatever is left (stream ended mid-buffer)
        if self._buf:
            remaining = self._buf
            self._buf = ""
            # Treat remaining as plain text; replace any source_N found
            self._flush_final(remaining)
        return list(self._ordered)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _flush(self) -> str:
        """
        Process self._buf, emit everything that is safe to release.

        Strategy:
          1. Find all complete source_N patterns in the buffer.
          2. Replace each with [n] using the registry.
          3. Hold any trailing partial match (e.g., "sour") for next token.
        """
        text = self._buf

        # Find the earliest position where a partial source_N could start
        # at the tail of the text (to avoid cutting off a pattern mid-stream)
        safe_end = self._safe_end(text)
        safe_text = text[:safe_end]
        held = text[safe_end:]

        # Replace all complete source_N patterns in safe_text
        result = self._SOURCE_RE.sub(self._replace_match, safe_text)

        self._buf = held
        return result

    def _flush_final(self, text: str) -> None:
        """Replace source_N patterns in remaining text (stream end flush)."""
        self._SOURCE_RE.sub(self._replace_match, text)

    def _safe_end(self, text: str) -> int:
        """
        Return the index up to which text is safe to process.

        The suffix text[safe_end:] could be a partial source_N pattern
        and must be held in the buffer for the next token.
        """
        # Walk backward to find the earliest position that could be
        # the start of an incomplete source_N pattern
        m = self._PARTIAL_RE.search(text)
        if m:
            return m.start()
        return len(text)

    def _replace_match(self, m: re.Match) -> str:
        """Replacement function for re.sub: register source_id and return [n]."""
        source_id = m.group(0)
        return f"[{self._register(source_id)}]"

    def _register(self, source_id: str) -> int:
        """Assign a display number to source_id on first call; return it thereafter."""
        if source_id not in self._id_to_num:
            num = self._next_num
            self._next_num += 1
            self._id_to_num[source_id] = num
            self._ordered.append((num, source_id))
        return self._id_to_num[source_id]
