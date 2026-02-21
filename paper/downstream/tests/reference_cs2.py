"""Reference implementation for CS2 — used to verify tests."""

import secrets
import sys

sys.path.insert(0, __file__.rsplit("/", 2)[0])
from interfaces.cs2_interface import SessionManager


class ReferenceSessionManager(SessionManager):
    def __init__(self):
        self._sessions: dict[str, dict] = {}

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        token = secrets.token_hex(32)
        self._sessions[token] = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "device_id": device_id,
        }
        return token

    def validate_session(self, token: str) -> dict | None:
        return self._sessions.get(token)

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        to_remove = [
            t
            for t, info in self._sessions.items()
            if info["tenant_id"] == tenant_id and info["user_id"] == user_id
        ]
        for t in to_remove:
            del self._sessions[t]
        return len(to_remove)

    def invalidate_session(self, token: str) -> bool:
        if token in self._sessions:
            del self._sessions[token]
            return True
        return False
