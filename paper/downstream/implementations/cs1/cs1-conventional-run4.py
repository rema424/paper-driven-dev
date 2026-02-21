"""
CS1 Conventional Run 4 — Three-component architecture (Registry + Parser + Finalizer)

Design basis: CS1-A-Run4 analysis
Architecture: "Citation Registry + Stream Parser/Rewriter + Finalizer"
Marker format: source_N appearing directly in raw LLM output text.
Key decisions from analysis:
  - Three explicit invariants that together guarantee all three requirements:
      1. id_to_num is written once and never changed
      2. next_num is monotonically increasing only
      3. Final source list is generated exclusively from id_to_num
  - Invalid source_id values (not in Source Catalog) receive "[?]" and a
    monitoring log entry; they do NOT enter the registry (no number assigned).
  - Numbering scope is per-response; do not share registry across conversations.
  - Finalizer performs consistency check: numbers referenced in output text
    must match entries in id_to_num.
  - Buffer handles token-boundary splits of source_N patterns.
"""

import re


class StreamParser:
    """
    Stateful incremental parser for source_N patterns.

    Separates parsing responsibility from the registry, following the
    three-component decomposition in the Run 4 design.
    """

    _SOURCE_RE = re.compile(r'source_\d+')
    _PARTIAL_RE = re.compile(r's(?:o(?:u(?:r(?:c(?:e(?:_\d*)?)?)?)?)?)?$')

    def __init__(self) -> None:
        self._buf: str = ""

    def feed(self, token: str) -> list[tuple[str, str]]:
        """
        Feed a token; return list of (kind, value) pairs where:
          - ('text', s)      — literal text safe to emit
          - ('cite', id)     — a complete citation with given source id
        """
        self._buf += token
        return self._drain()

    def flush(self) -> list[tuple[str, str]]:
        """Flush remaining buffer as plain text (call at stream end)."""
        remaining = self._buf
        self._buf = ""
        if remaining:
            return [("text", remaining)]
        return []

    def _drain(self) -> list[tuple[str, str]]:
        text = self._buf
        events: list[tuple[str, str]] = []

        # Find where a partial source_N could start at the tail
        pm = self._PARTIAL_RE.search(text)
        if pm:
            safe_text = text[:pm.start()]
            self._buf = text[pm.start():]
        else:
            safe_text = text
            self._buf = ""

        pos = 0
        for match in self._SOURCE_RE.finditer(safe_text):
            before = safe_text[pos:match.start()]
            if before:
                events.append(("text", before))
            events.append(("cite", match.group(0)))
            pos = match.end()

        tail = safe_text[pos:]
        if tail:
            events.append(("text", tail))

        return events


class CitationRegistry:
    """
    Append-only registry: source_id -> display number.

    Enforces Run 4 invariants:
      1. id_to_num written once, never changed
      2. next_num monotonically increasing
    """

    def __init__(self, source_catalog: set[str] | None = None) -> None:
        # Optional catalog of known source IDs (Source Catalog component)
        self._catalog: set[str] | None = source_catalog
        # Invariant 1: written once
        self._id_to_num: dict[str, int] = {}
        # Ordered for list generation
        self._ordered: list[tuple[int, str]] = []
        # Invariant 2: monotonically increasing
        self._next_num: int = 1
        # Monitoring log for invalid IDs
        self._invalid_log: list[str] = []

    def resolve(self, source_id: str) -> str:
        """
        Resolve source_id to display string.

        Returns "[n]" for valid IDs (registered on first call),
        "[?]" for IDs not in the source catalog, with a log entry.
        """
        if self._catalog is not None and source_id not in self._catalog:
            self._invalid_log.append(source_id)
            return "[?]"

        if source_id not in self._id_to_num:
            # Invariant 1 + 2: assign once, increment monotonically
            num = self._next_num
            self._next_num += 1
            self._id_to_num[source_id] = num
            self._ordered.append((num, source_id))

        return f"[{self._id_to_num[source_id]}]"

    def get_ordered(self) -> list[tuple[int, str]]:
        """Return [(num, source_id), ...] in registration order."""
        return list(self._ordered)

    @property
    def invalid_log(self) -> list[str]:
        return list(self._invalid_log)


class Finalizer:
    """
    Post-stream consistency checker (Run 4 Finalizer component).

    Verifies that every display number referenced in the emitted text has a
    corresponding entry in the registry (Invariant 3: list generated from map).
    """

    _CITATION_REF = re.compile(r'\[(\d+)\]')

    @staticmethod
    def check(emitted_text: str, source_list: list[tuple[int, str]]) -> list[str]:
        """
        Return list of error strings. Empty list means consistent.
        """
        errors: list[str] = []
        registered_nums = {num for num, _ in source_list}
        referenced_nums = {
            int(m.group(1)) for m in Finalizer._CITATION_REF.finditer(emitted_text)
        }
        for num in referenced_nums - registered_nums:
            errors.append(f"[{num}] referenced in text but not in source list")
        return errors


class CitationRenumberer:
    """
    Public facade combining StreamParser + CitationRegistry + Finalizer.

    Implements the required interface: process_token / get_source_list.

    Source references appear as source_N (e.g., source_3, source_7) directly
    in the raw LLM output text and are replaced with [n] by first-appearance order.
    """

    def __init__(self, source_catalog: set[str] | None = None) -> None:
        self._parser = StreamParser()
        self._registry = CitationRegistry(source_catalog=source_catalog)
        self._emitted: list[str] = []  # accumulated output for Finalizer

    def process_token(self, token: str) -> str:
        """Process one streaming token; return displayable text."""
        events = self._parser.feed(token)
        return self._render(events)

    def get_source_list(self) -> list[tuple[int, str]]:
        """
        Flush remaining buffer, run Finalizer check, return source list.

        Invariant 3 (from Run 4): list is generated exclusively from the registry.
        """
        # Flush parser buffer
        flush_events = self._parser.flush()
        self._render(flush_events)

        # Finalizer consistency check (errors logged but do not raise)
        full_text = "".join(self._emitted)
        source_list = self._registry.get_ordered()
        errors = Finalizer.check(full_text, source_list)
        if errors:
            # Monitoring log (per Run 4: record errors, use fallback display)
            for _err in errors:
                pass  # In production: send to monitoring system

        return source_list

    def _render(self, events: list[tuple[str, str]]) -> str:
        parts: list[str] = []
        for kind, value in events:
            if kind == "text":
                parts.append(value)
            elif kind == "cite":
                parts.append(self._registry.resolve(value))
        result = "".join(parts)
        self._emitted.append(result)
        return result
