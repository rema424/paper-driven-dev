"""Hidden test suite for CS1: RAG Streaming Citation Renumbering.

Tests are derived SOLELY from the problem statement requirements:
  - ストリーミング中にリアルタイムで引用番号を表示する
  - 一度表示した番号が後から変わらない
  - ストリーム完了時にソース一覧と整合している

10 test cases covering functional correctness.
"""

import pytest


def _get_renumberer(impl_module):
    """Find and instantiate the CitationRenumberer from the implementation."""
    for name in dir(impl_module):
        obj = getattr(impl_module, name)
        if (
            isinstance(obj, type)
            and hasattr(obj, "process_token")
            and hasattr(obj, "get_source_list")
        ):
            try:
                return obj()
            except TypeError:
                continue  # abstract class, skip
    pytest.fail("No CitationRenumberer implementation found")


class TestCS1BasicRenumbering:
    """Requirement: ストリーミング中にリアルタイムで引用番号を表示する"""

    def test_single_citation(self, impl_module):
        """A single source reference should be renumbered to [1]."""
        r = _get_renumberer(impl_module)
        result = r.process_token("See source_3 for details.")
        assert "[1]" in result
        assert "source_3" not in result

    def test_two_different_citations(self, impl_module):
        """Two different sources should get sequential numbers."""
        r = _get_renumberer(impl_module)
        r1 = r.process_token("See source_3.")
        r2 = r.process_token("Also source_7.")
        assert "[1]" in r1
        assert "[2]" in r2

    def test_first_appearance_order(self, impl_module):
        """Numbers should be assigned by order of first appearance,
        regardless of original source number."""
        r = _get_renumberer(impl_module)
        r1 = r.process_token("source_7")
        r2 = r.process_token("source_1")
        # source_7 appeared first → [1], source_1 appeared second → [2]
        assert "[1]" in r1
        assert "[2]" in r2

    def test_text_preservation(self, impl_module):
        """Non-citation text should pass through unchanged."""
        r = _get_renumberer(impl_module)
        result = r.process_token("Hello world with no citations")
        assert "Hello world with no citations" == result


class TestCS1NumberStability:
    """Requirement: 一度表示した番号が後から変わらない"""

    def test_repeated_source_same_number(self, impl_module):
        """The same source referenced multiple times gets the same number."""
        r = _get_renumberer(impl_module)
        r1 = r.process_token("See source_3.")
        r2 = r.process_token("Again source_3.")
        # Both should contain [1]
        assert "[1]" in r1
        assert "[1]" in r2
        assert "[2]" not in r2

    def test_number_stability_across_stream(self, impl_module):
        """After assigning [1] to source_3, later appearance of source_3
        should still produce [1] even after new sources are encountered."""
        r = _get_renumberer(impl_module)
        r.process_token("source_3")  # → [1]
        r.process_token("source_7")  # → [2]
        r3 = r.process_token("source_3 again")  # → still [1]
        assert "[1]" in r3
        assert "[3]" not in r3


class TestCS1SourceListConsistency:
    """Requirement: ストリーム完了時にソース一覧と整合している"""

    def test_source_list_matches_citations(self, impl_module):
        """Source list should contain exactly the sources referenced."""
        r = _get_renumberer(impl_module)
        r.process_token("source_3")
        r.process_token("source_7")
        sources = r.get_source_list()
        source_ids = [s[1] for s in sources]
        assert "source_3" in source_ids
        assert "source_7" in source_ids
        assert len(sources) == 2

    def test_source_list_ordering(self, impl_module):
        """Source list should be ordered by display number."""
        r = _get_renumberer(impl_module)
        r.process_token("source_5")
        r.process_token("source_2")
        sources = r.get_source_list()
        assert sources[0] == (1, "source_5")
        assert sources[1] == (2, "source_2")

    def test_empty_stream(self, impl_module):
        """No citations processed → empty source list."""
        r = _get_renumberer(impl_module)
        r.process_token("No citations here")
        sources = r.get_source_list()
        assert sources == []

    def test_multiple_citations_in_one_token(self, impl_module):
        """A token with multiple citations should handle all of them."""
        r = _get_renumberer(impl_module)
        result = r.process_token("Compare source_3 and source_7.")
        assert "[1]" in result
        assert "[2]" in result
        sources = r.get_source_list()
        assert len(sources) == 2
