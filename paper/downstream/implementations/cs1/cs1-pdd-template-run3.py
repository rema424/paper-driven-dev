"""
CS1-C-Run3: RAG Streaming Citation Renumberer
Design basis: First-Use Monotonic Binding (FUMB)

Design decisions reflected from Run3 analysis (§5 提案手法):
- Named components: Source Registry, Citation Binder, Stream Renderer, Finalizer.
- FUMB invariants enforced mechanically (§5.1):
    Immutability  : f(source)=k at time t implies f(source)=k for all t' > t.
    Uniqueness    : no two distinct source_ids share the same display number.
    Completeness  : every k that appears in the body is present in the final list.
- source_N patterns appear directly in raw LLM output; regex matches them.
- Citation Binder is append-only: no deletion, no re-assignment.
- Idempotency (§6 性質5): same source_id always maps to the same existing binding;
  duplicate citations produce no new allocation.
- Finalizer reads the Binder in insertion order (single source of truth).
- Stream Renderer produces [n] inline with no buffering delay.
"""

import re


class CitationRenumberer:
    """
    Implements First-Use Monotonic Binding (FUMB).

    Components
    ----------
    Citation Binder  : self._binder  — append-only dict source_id -> number.
    Stream Renderer  : process_token — replaces source_N with [n] inline.
    Finalizer        : get_source_list — reads Binder in insertion order.

    FUMB Invariants:
        Immutability : once bound, f(source_id) never changes.
        Uniqueness   : each number is assigned to at most one source_id.
        Completeness : every emitted [n] has a corresponding Binder entry.
    """

    # Matches source_N identifiers directly in raw LLM output text.
    _SOURCE_RE = re.compile(r'source_\d+')

    def __init__(self) -> None:
        # Citation Binder: append-only, never mutated after insertion.
        self._binder: dict[str, int] = {}
        # Explicit insertion-order list to make append-only property visible
        # (Python 3.7+ dict preserves order, but this documents intent clearly).
        self._order: list[str] = []
        self._next: int = 1

    def _bind(self, source_id: str) -> int:
        """
        Return the display number for source_id (First-Use Monotonic Binding).

        - If source_id is already bound, return the existing number (Immutability).
        - If not, bind it to self._next and increment (append-only extension).
        """
        if source_id not in self._binder:
            num = self._next
            self._binder[source_id] = num
            self._order.append(source_id)
            self._next += 1
        return self._binder[source_id]

    def process_token(self, token: str) -> str:
        """
        Stream Renderer: replace source_N patterns with [M] by first-appearance order.

        Each source_N in the token fires _bind(), which either allocates a new
        number (first use) or returns the existing one (idempotent re-use).
        The FUMB Immutability invariant is upheld by the append-only Binder.
        """
        def _sub(m: re.Match) -> str:
            return f"[{self._bind(m.group(0))}]"
        return self._SOURCE_RE.sub(_sub, token)

    def get_source_list(self) -> list[tuple[int, str]]:
        """
        Finalizer: produce the authoritative source list from the Citation Binder.

        Reads self._binder in insertion order (self._order) to construct the list.
        The Finalizer uses the same Binder as the Stream Renderer, guaranteeing
        that every [n] in the body corresponds to exactly one entry here
        (FUMB Completeness invariant).
        """
        return [(self._binder[sid], sid) for sid in self._order]
