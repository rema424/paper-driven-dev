"""
CS2-B-Run1: Gateway-centric opaque session management.

Design basis: cs2-paper-format-run1.md

Key design decisions from the paper:
- Opaque session tokens (random bytes, no user info embedded in token itself)
- Authority store keyed by T:{tid}:S:{sid} with TTL
- User-to-session set T:{tid}:U:{uid}:SESS for fast bulk invalidation
- Tokens stored under HMAC(token) in the store (store leak protection)
- Per-device separate session IDs to support multi-device login (R1)
- Immediate invalidation by atomic deletion of all session records (R2)
- Stateless app layer; all session state in the authority store (R3)
- Validate function is a single O(1) dict lookup — no joins (R4)
"""

import secrets
import hashlib
import hmac
import time
from typing import Optional


_SESSION_TTL_SECONDS = 3600  # 1 hour default session lifetime

# Secret for HMAC-keying tokens in the store (store-leak protection)
_HMAC_SECRET = secrets.token_bytes(32)


def _hmac_key(token: str) -> str:
    """Derive the store key from a raw token using HMAC-SHA256.

    The raw token is never stored directly; only its HMAC is kept as the key.
    This means a store dump alone does not expose usable tokens.
    """
    return hmac.new(_HMAC_SECRET, token.encode(), hashlib.sha256).hexdigest()


class SessionManager:
    """
    Authority-store-based opaque session manager.

    Storage layout (in-memory simulation of a distributed KVS):

    _session_store:
        "T:{tid}:S:{hmac_sid}" -> {
            "tenant_id": str,
            "user_id": str,
            "device_id": str,
            "status": "active" | "revoked",
            "expires_at": float,   # Unix timestamp
        }

    _user_session_index:
        "T:{tid}:U:{uid}" -> set of raw session tokens

    The _user_session_index holds raw tokens (not HMACs) so that bulk
    invalidation can derive the HMAC keys and delete from _session_store.
    In a real deployment this index would itself be protected (e.g., the set
    members could also be HMACs), but for the in-memory prototype we keep the
    raw tokens to keep the deletion logic clear.
    """

    def __init__(self) -> None:
        # Simulates T:{tid}:S:{hmac_sid} -> session record
        self._session_store: dict[str, dict] = {}
        # Simulates T:{tid}:U:{uid} -> {raw_token, ...}
        self._user_session_index: dict[str, set] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _session_store_key(self, tid: str, raw_token: str) -> str:
        return f"T:{tid}:S:{_hmac_key(raw_token)}"

    def _user_index_key(self, tid: str, uid: str) -> str:
        return f"T:{tid}:U:{uid}"

    def _is_expired(self, record: dict) -> bool:
        return time.time() > record["expires_at"]

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """Create a new opaque session token for the given (tenant, user, device).

        A separate session ID (token) is issued per device, allowing the same
        user to maintain concurrent sessions from different devices (R1).

        Returns the raw opaque token that the client will present on each request.
        """
        raw_token = secrets.token_hex(32)  # 256-bit entropy, URL-safe hex

        store_key = self._session_store_key(tenant_id, raw_token)
        record = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "device_id": device_id,
            "status": "active",
            "expires_at": time.time() + _SESSION_TTL_SECONDS,
        }
        self._session_store[store_key] = record

        # Register in user-to-session index for fast bulk invalidation
        idx_key = self._user_index_key(tenant_id, user_id)
        if idx_key not in self._user_session_index:
            self._user_session_index[idx_key] = set()
        self._user_session_index[idx_key].add(raw_token)

        return raw_token

    def validate_session(self, token: str) -> Optional[dict]:
        """Validate an opaque session token.

        The gateway performs a single authority-store lookup (R4).
        Looks up T:{tid}:{hmac_sid} — but because we use opaque tokens,
        we must iterate tenant namespaces or embed the tenant prefix in
        the token.  For the in-memory prototype we encode the tenant_id
        into the store key lookup by scanning all matching HMAC keys.

        Design note: In a real system the client would present both the
        token and the tenant_id (e.g., via subdomain or header), so the
        gateway would form the exact key without scanning.  Here we embed
        the tenant lookup by iterating candidate store keys.

        Returns {"tenant_id", "user_id", "device_id"} if valid, else None.
        """
        # In production the tenant_id would be derived from the request
        # context (subdomain / header).  In this prototype we scan for the
        # HMAC of the supplied token across all stored keys.
        token_hmac = _hmac_key(token)
        for store_key, record in self._session_store.items():
            # Key format: T:{tid}:S:{hmac}
            if store_key.endswith(f":S:{token_hmac}"):
                if record["status"] != "active":
                    return None
                if self._is_expired(record):
                    # Lazy expiry: remove the stale record
                    self._session_store.pop(store_key, None)
                    tid = record["tenant_id"]
                    uid = record["user_id"]
                    idx_key = self._user_index_key(tid, uid)
                    self._user_session_index.get(idx_key, set()).discard(token)
                    return None
                return {
                    "tenant_id": record["tenant_id"],
                    "user_id": record["user_id"],
                    "device_id": record["device_id"],
                }
        return None

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """Atomically invalidate all sessions for a user in a tenant.

        Implements the bulk-delete pattern described in §3.5:
        1. Retrieve the user-to-session set.
        2. Delete each session record from the authority store.
        3. Clear the index entry.

        After this call the next gateway lookup for any token of this user
        will find no record and reject the request (R2).

        Returns the count of invalidated sessions.
        """
        idx_key = self._user_index_key(tenant_id, user_id)
        raw_tokens = self._user_session_index.pop(idx_key, set())
        count = 0
        for raw_token in raw_tokens:
            store_key = self._session_store_key(tenant_id, raw_token)
            if self._session_store.pop(store_key, None) is not None:
                count += 1
        return count

    def invalidate_session(self, token: str) -> bool:
        """Invalidate a single session by its opaque token.

        Returns True if the session existed and was removed, False otherwise.
        """
        token_hmac = _hmac_key(token)
        for store_key, record in list(self._session_store.items()):
            if store_key.endswith(f":S:{token_hmac}"):
                del self._session_store[store_key]
                # Clean up the user index
                tid = record["tenant_id"]
                uid = record["user_id"]
                idx_key = self._user_index_key(tid, uid)
                self._user_session_index.get(idx_key, set()).discard(token)
                return True
        return False
