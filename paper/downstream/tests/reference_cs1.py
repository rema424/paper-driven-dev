"""Reference implementation for CS1 — used to verify tests."""

import re
import sys

sys.path.insert(0, __file__.rsplit("/", 2)[0])
from interfaces.cs1_interface import CitationRenumberer


class ReferenceCitationRenumberer(CitationRenumberer):
    def __init__(self):
        self._mapping: dict[str, int] = {}
        self._next_num = 1

    def process_token(self, token: str) -> str:
        def replace(match):
            source_id = match.group(0)
            if source_id not in self._mapping:
                self._mapping[source_id] = self._next_num
                self._next_num += 1
            return f"[{self._mapping[source_id]}]"

        return re.sub(r"source_\d+", replace, token)

    def get_source_list(self) -> list[tuple[int, str]]:
        return sorted(
            [(num, src) for src, num in self._mapping.items()],
            key=lambda x: x[0],
        )
