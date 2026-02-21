"""Interface for CS1: RAG Streaming Citation Renumbering.

The implementation must provide a CitationRenumberer class that processes
streaming tokens and renumbers source references (e.g., source_3, source_7)
into sequential display numbers ([1], [2], [3]).
"""

from abc import ABC, abstractmethod


class CitationRenumberer(ABC):
    """Abstract base class for streaming citation renumbering."""

    @abstractmethod
    def process_token(self, token: str) -> str:
        """Process a single streaming token.

        Replace any source references (source_N) with sequential display
        numbers ([M]) based on order of first appearance.

        Args:
            token: A text token from the LLM stream. May contain zero, one,
                   or multiple source references.

        Returns:
            The token with source references replaced by display numbers.
        """
        ...

    @abstractmethod
    def get_source_list(self) -> list[tuple[int, str]]:
        """Return the source list after stream processing.

        Returns:
            List of (display_number, original_source_id) tuples,
            ordered by display number.
            Example: [(1, "source_3"), (2, "source_7")]
        """
        ...
