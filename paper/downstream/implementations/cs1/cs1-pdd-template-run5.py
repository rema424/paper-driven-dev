"""
CS1-C-Run5: RAG Streaming Citation Renumberer
Design basis: Monotonic Citation Ledger (MCL)

Design decisions reflected from Run5 analysis (§5 提案手法):
- Named components:
    Source Registry      : set of valid source_ids (all seen IDs accepted here
                           since no external registry is available at __init__).
    MCL Indexer          : core state machine, directly from §5.2 pseudocode:
                               state: source_to_num, num_to_source, next=1
                               on cite(s): validate; if s not in source_to_num:
                                   source_to_num[s]=next; num_to_source[next]=s; next+=1
                               emit "[" + source_to_num[s] + "]"
    Stream Renderer      : emits [n] into the output immediately.
    Finalizer            : at completion, iterate num_to_source[1..next-1] for list.

- source_N patterns appear directly in raw LLM output; regex matches them.
- The §5.2 pseudocode is translated almost verbatim; field names match the spec.
- num_to_source is an explicit list (1-indexed via offset trick) rather than a dict
  to match "list num_to_source" in the pseudocode.
- Idempotence (§6 性質2): same cite(s) always returns the same number.
- Realtime property (§6 性質5): number is emitted in the same process_token call,
  bounded only by regex matching latency.
- Invalid/unknown source_ids (§6 性質6): in the absence of an external registry
  all seen source_N IDs are treated as valid and assigned numbers normally.
"""

import re


class CitationRenumberer:
    """
    Implements Monotonic Citation Ledger (MCL).

    State (mirroring §5.2 pseudocode, verbatim names):
        source_to_num : dict[str, int]  -- forward map
        num_to_source : list[str]       -- reverse list, 1-indexed (index 0 unused)
        next          : int             -- next number to allocate (starts at 1)

    The Stream Renderer detects source_N patterns directly in raw token text.
    """

    # Matches source_N identifiers directly in raw LLM output text.
    _SOURCE_RE = re.compile(r'source_\d+')

    def __init__(self) -> None:
        # MCL Indexer state (§5.2 pseudocode, verbatim names).
        self.source_to_num: dict[str, int] = {}
        self.num_to_source: list[str] = [""]  # index 0 is placeholder; 1-indexed.
        self.next: int = 1

    def _on_cite(self, s: str) -> str:
        """
        Process a cite(s) event per §5.2 pseudocode.

        validate s in Source Registry
          (here: always valid — no external registry at construction time)
        if s not in source_to_num:
            source_to_num[s] = next
            num_to_source[next] = s    (append to list)
            next += 1
        emit "[" + source_to_num[s] + "]"
        """
        if s not in self.source_to_num:
            self.source_to_num[s] = self.next
            self.num_to_source.append(s)   # num_to_source[self.next] = s
            self.next += 1
        return f"[{self.source_to_num[s]}]"

    def process_token(self, token: str) -> str:
        """
        Stream Renderer: replace source_N patterns with [M] by first-appearance order.

        Each source_N in the token fires _on_cite(), which either allocates a new
        number (first use) or returns the existing one (idempotent re-use).
        The number is emitted in the same call, satisfying the realtime property
        from §6 性質5.
        """
        return self._SOURCE_RE.sub(lambda m: self._on_cite(m.group(0)), token)

    def get_source_list(self) -> list[tuple[int, str]]:
        """
        Finalizer: generate source list from num_to_source[1..next-1].

        Per §5.2: "iterate num_to_source[1..next-1] for the list."
        This guarantees that the list is identical in structure to the body:
        every [n] in the body corresponds to num_to_source[n] (§6 性質4).
        """
        return [
            (n, self.num_to_source[n])
            for n in range(1, self.next)
        ]
