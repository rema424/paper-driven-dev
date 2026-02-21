"""
CS1 Conventional Run 5 — State-machine buffer with source_N patterns

Design basis: CS1-A-Run5 analysis
Architecture: Server-side state machine buffer; four explicit state variables
              (nextNumber, sourceToNumber, numberToSource, streamBuffer)
Marker format: source_N appearing directly in raw LLM output text.
Key decisions from analysis:
  - State machine (not regex-only) to handle chunk boundaries robustly
  - Unknown source IDs: ignored + logged (NOT assigned a number, not "[?]")
    "通常は無視＋ログが安全" — they simply pass through as raw text
  - Re-numbering (詰め直し) is explicitly forbidden
  - numberToSource drives the final source list (1..N enumeration)
  - Bidirectional consistency check at stream end (監査ログ推奨)
  - citation_added event: tracked internally for audit purposes
"""

import re


class CitationRenumberer:
    """
    State-machine based citation renumberer following the Run 5 design.

    Source references appear as source_N (e.g., source_3, source_7) directly
    in the raw LLM output text and are replaced with [n] by first-appearance order.

    State variables (matching the Run 5 design verbatim):
      nextNumber       : int        — monotonically increasing counter
      sourceToNumber   : dict       — source_id -> display number (write-once)
      numberToSource   : dict       — display number -> source_id (for list)
      streamBuffer     : str        — accumulated unparsed input

    Unknown source IDs pass through as literal text and are appended to
    an internal ignore log (not displayed as "[?]", not numbered).
    """

    # Matches a fully complete source_N pattern
    _SOURCE_RE = re.compile(r'source_\d+')
    # Trailing partial that might continue into the next token
    _PARTIAL_RE = re.compile(r's(?:o(?:u(?:r(?:c(?:e(?:_\d*)?)?)?)?)?)?$')

    def __init__(self, retrieved_sources: set[str] | None = None) -> None:
        # Known retrieved source IDs; None means accept all
        self._retrieved: set[str] | None = retrieved_sources

        # Run 5 state variables
        self.nextNumber: int = 1
        self.sourceToNumber: dict[str, int] = {}
        self.numberToSource: dict[int, str] = {}
        self.streamBuffer: str = ""

        # Audit log: citation_added events
        self._citation_added_log: list[tuple[int, str]] = []
        # Ignore log: unrecognised source IDs that passed through
        self._ignore_log: list[str] = []
        # Accumulated emitted text for bidirectional consistency check
        self._emitted_text: list[str] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def process_token(self, token: str) -> str:
        """
        Feed a streaming token through the state machine; return output text.

        Complete source_N patterns are replaced with [n] immediately.
        Partial patterns accumulate in streamBuffer until completed.
        """
        self.streamBuffer += token
        output = self._run_state_machine()
        self._emitted_text.append(output)
        return output

    def get_source_list(self) -> list[tuple[int, str]]:
        """
        Flush buffer and return [(display_num, source_id), ...] 1..N.

        Drives the list exclusively from numberToSource (Run 5: "1..Nで列挙")
        and runs the bidirectional consistency check (監査ログ推奨).
        """
        # Flush remaining buffer as plain text
        if self.streamBuffer:
            remaining = self.streamBuffer
            self.streamBuffer = ""
            self._emitted_text.append(remaining)

        result = [
            (num, self.numberToSource[num])
            for num in range(1, self.nextNumber)
        ]

        # Bidirectional consistency check
        self._audit_consistency(result)

        return result

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def _run_state_machine(self) -> str:
        """
        Process streamBuffer through the state machine.

        Uses regex to find complete source_N patterns and handles the
        partial-pattern suffix carefully — reflecting the Run 5
        "バッファ＋状態機械" approach.
        """
        text = self.streamBuffer

        # Find where a partial source_N could start at the tail
        pm = self._PARTIAL_RE.search(text)
        if pm:
            safe_text = text[:pm.start()]
            self.streamBuffer = text[pm.start():]
        else:
            safe_text = text
            self.streamBuffer = ""

        return self._SOURCE_RE.sub(self._handle_match, safe_text)

    def _handle_match(self, m: re.Match) -> str:
        """Replacement callback: process a fully parsed source_id."""
        return self._handle_citation(m.group(0))

    def _handle_citation(self, source_id: str) -> str:
        """
        Process a fully parsed source_id.

        Policy (Run 5):
          - If source_id is unknown: pass through as raw text + ignore log
          - If known and new: assign number, fire citation_added event
          - If known and seen: reuse existing number (re-numbering forbidden)
        """
        if self._retrieved is not None and source_id not in self._retrieved:
            # Ignore + log (run 5: "通常は無視＋ログが安全")
            self._ignore_log.append(source_id)
            # Pass through as literal text
            return source_id

        if source_id not in self.sourceToNumber:
            num = self.nextNumber
            self.nextNumber += 1
            # Write-once into both maps
            self.sourceToNumber[source_id] = num
            self.numberToSource[num] = source_id
            # citation_added event (Run 5: "citation_added イベントを送るとUI実装が楽")
            self._citation_added_log.append((num, source_id))

        return f"[{self.sourceToNumber[source_id]}]"

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    def _audit_consistency(self, source_list: list[tuple[int, str]]) -> None:
        """
        Bidirectional consistency check (Run 5: "本文中に出た番号と一覧の双方向チェック").

        Check 1: every [n] in emitted text has an entry in source list
        Check 2: every entry in source list was referenced in emitted text
        """
        full_text = "".join(self._emitted_text)
        ref_pattern = re.compile(r'\[(\d+)\]')
        referenced = {int(m.group(1)) for m in ref_pattern.finditer(full_text)}
        listed = {num for num, _ in source_list}

        unreferenced = listed - referenced
        unlisted = referenced - listed
        # In production: send unreferenced/unlisted to monitoring system
        # Here we store them for inspection if needed
        self._audit_unreferenced = unreferenced
        self._audit_unlisted = unlisted
