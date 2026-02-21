"""
CS1 Paper-Format Run 5 — Online Citation Renumbering
Design source: docs/examples/fullpaper/cs1-paper-format-run5.md

Design: "First-Occurrence Fixed Assignment" (初出時固定方式)

State from the analysis:
    sid_to_idx: map source_id -> display_number (first-insertion only)
    idx_to_sid: list of source_ids ordered by display_number
    next: int (starting at 1)

Algorithm:
    on_cite(sid):
        csid = canonicalize(sid)   # merge same-document chunks into one entry
        if csid not in sid_to_idx:
            sid_to_idx[csid] = next
            idx_to_sid.append(csid)
            next += 1
        emit("[" + sid_to_idx[csid] + "]")

    on_finish():
        for i, sid in enumerate(idx_to_sid, start=1):
            render_reference(i, sid)

Key distinction vs other runs: canonicalize() de-duplicates chunk variants of
the same document (e.g. "source_7_chunk_2" and "source_7_chunk_0" → "source_7").

Three properties:
    命題1 (不変性):      sid_to_idx updated on first insertion only.
    命題2 (リアルタイム性): O(1) per on_cite (hash reference only).
    命題3 (最終整合性):    idx_to_sid / sid_to_idx shared by streaming and on_finish.

The analysis uses <cite id="source_N"/> tags, but this implementation processes
RAW LLM text where citations appear as bare `source_N` tokens.
A regex over `source_\\d+` patterns is used.
"""

import re


class CitationRenumberer:
    """
    Processes streaming tokens, replacing source_N patterns with [N] display
    numbers by First-Occurrence Fixed Assignment.

    Key distinction: canonicalize() merges multiple chunk variants of the same
    document. For example "source_7_chunk_2" and "source_7_chunk_0" both resolve
    to "source_7" and share a single display number.

    State:
        _sid_to_idx: source_id -> display_number (first-insertion only)
        _idx_to_sid: ordered list of canonical source_ids by display number
    """

    def __init__(self, valid_sources: set[str] | None = None):
        """
        Args:
            valid_sources: Optional set of valid canonical source IDs (checked
                           after canonicalization). Pass None to accept all IDs.
        """
        # sid_to_idx: monotone map, first-insertion only
        self._sid_to_idx: dict[str, int] = {}
        # idx_to_sid: ordered by display number (0-indexed; display = i + 1)
        self._idx_to_sid: list[str] = []
        self._next: int = 1
        self._valid_sources: set[str] | None = valid_sources
        # Audit log for unknown IDs (for replayability)
        self.unknown_ids: list[str] = []

    @staticmethod
    def canonicalize(source_id: str) -> str:
        """
        Merge multiple chunk variants of the same document into a single canonical ID.

        Strategy: strip trailing _chunk_N or _chunkN suffixes (case-insensitive).

        Examples:
            "source_7_chunk_2"  -> "source_7"
            "source_3_chunk_0"  -> "source_3"
            "source_7"          -> "source_7"   (unchanged)

        Implements: "複数チャンク同一文書は canonicalize で1件に統合"
        """
        return re.sub(r"_chunk_?\d+$", "", source_id, flags=re.IGNORECASE)

    def _on_cite(self, raw_sid: str) -> str:
        """
        Process a single citation source ID.

        Steps:
            1. Canonicalize (chunk deduplication).
            2. Validate against valid_sources if configured.
            3. Assign display number on first occurrence only.
            4. Return "[N]" or "[?]" for unresolved IDs.
        """
        sid = self.canonicalize(raw_sid)
        if self._valid_sources is not None and sid not in self._valid_sources:
            self.unknown_ids.append(sid)
            return "[?]"
        if sid not in self._sid_to_idx:
            # First-occurrence fixed assignment
            self._sid_to_idx[sid] = self._next
            self._idx_to_sid.append(sid)
            self._next += 1
        return f"[{self._sid_to_idx[sid]}]"

    def process_token(self, token: str) -> str:
        """Replace source_N patterns with [N] by first-appearance order."""
        def replace(match: re.Match) -> str:
            return self._on_cite(match.group(0))

        return re.sub(r"source_\d+", replace, token)

    def get_source_list(self) -> list[tuple[int, str]]:
        """Return [(1, "source_3"), (2, "source_7")] ordered by display number.

        on_finish() equivalent: enumerates idx_to_sid starting at 1.
        Shares state with streaming, guaranteeing 命題3 (最終整合性).
        """
        return [(i + 1, sid) for i, sid in enumerate(self._idx_to_sid)]
