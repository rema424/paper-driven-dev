"""
CS2 Checklist Run 1 — Multi-tenant SaaS Session Management

Design basis: cs2-checklist-run1.md (CS2-D-Run1, GPT-5.2 via Codex)

Key design decisions reflected:
- Hybrid approach: short-lived opaque access tokens + server-side session store
- Two-layer revocation: user-level session_version (bulk) + per-session status (fine-grained)
- In-memory simulation of "local cache" (L1) backed by shared store (simulated Redis dict)
- session_version increment for instant bulk invalidation of all user sessions
- Per-session revocation for individual device logout
- Tenant-scoped key isolation: keys prefixed with tenant_id to prevent cross-tenant leakage
- Stateless-ready: all state lives in the shared store, not per-server memory

The analysis identified the core tension as:
  "distributed environment: all nodes knowing the current revocation state"
  vs "minimize per-request I/O by processing locally".
This implementation resolves it by keeping a fast in-memory "local cache" that is
invalidated on revocation, with the shared store as the source of truth.
"""

import secrets
import time
import threading
from typing import Optional


class SessionManager:
    """
    Multi-tenant session manager based on the Run 1 checklist analysis.

    Storage layout (simulating Redis + DB in plain dicts):

    _shared_store:
        "sv:{tenant_id}:{user_id}"          -> int  (session_version; incremented on bulk revoke)
        "sess:{token}"                       -> dict (session record)
        "revoked_sess:{tenant_id}:{sid}"     -> bool (per-session revocation flag)
        "user_sessions:{tenant_id}:{user_id}"-> set  (set of tokens belonging to this user)

    _local_cache (L1, simulating per-node in-memory cache):
        "sv:{tenant_id}:{user_id}"           -> int  (cached session_version)
        "revoked_sess:{tenant_id}:{sid}"     -> bool (cached revocation status)
    """

    def __init__(self) -> None:
        # Simulated shared store (would be Redis in production)
        self._shared_store: dict = {}
        self._store_lock = threading.Lock()

        # Simulated L1 local cache (per-node in-memory, invalidated by events)
        self._local_cache: dict = {}
        self._cache_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """Create a new session for a device. Returns an opaque session token."""
        token = secrets.token_urlsafe(32)
        session_id = secrets.token_urlsafe(16)
        created_at = time.time()

        sv_key = self._sv_key(tenant_id, user_id)
        user_sessions_key = self._user_sessions_key(tenant_id, user_id)

        with self._store_lock:
            # Initialise session_version for this user if not yet present
            if sv_key not in self._shared_store:
                self._shared_store[sv_key] = 0

            current_sv = self._shared_store[sv_key]

            # Persist the session record (token -> session data)
            self._shared_store[f"sess:{token}"] = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "device_id": device_id,
                "session_id": session_id,
                "session_version": current_sv,
                "created_at": created_at,
            }

            # Track which tokens belong to this user (for bulk invalidation)
            if user_sessions_key not in self._shared_store:
                self._shared_store[user_sessions_key] = set()
            self._shared_store[user_sessions_key].add(token)

        return token

    def validate_session(self, token: str) -> Optional[dict]:
        """
        Validate a session token.

        Authentication flow (mirroring the checklist's §7.2 request auth):
          1. Look up the session record.
          2. Check per-session revocation flag (L1 cache → shared store).
          3. Check user-level session_version matches what is stored in the session
             record (L1 cache → shared store).

        Returns {'tenant_id', 'user_id', 'device_id'} if valid, else None.
        """
        with self._store_lock:
            record = self._shared_store.get(f"sess:{token}")

        if record is None:
            return None

        tenant_id = record["tenant_id"]
        user_id = record["user_id"]
        session_id = record["session_id"]
        token_sv = record["session_version"]

        # Step 1: Check per-session revocation (L1 → shared store)
        if self._is_session_revoked(tenant_id, session_id):
            return None

        # Step 2: Check user-level session_version (L1 → shared store)
        current_sv = self._get_session_version(tenant_id, user_id)
        if current_sv != token_sv:
            # session_version has been incremented since token was issued → revoked
            return None

        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "device_id": record["device_id"],
        }

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """
        Invalidate ALL sessions for a user in a tenant by incrementing session_version.

        This mirrors §7.2 "管理者による即時無効化: ユーザー全セッション無効化".
        Returns count of tokens that were active at time of invalidation.
        """
        sv_key = self._sv_key(tenant_id, user_id)
        user_sessions_key = self._user_sessions_key(tenant_id, user_id)

        with self._store_lock:
            # Atomically increment session_version (simulates Redis INCR + Lua)
            old_sv = self._shared_store.get(sv_key, 0)
            new_sv = old_sv + 1
            self._shared_store[sv_key] = new_sv

            # Count active tokens for this user
            tokens = set(self._shared_store.get(user_sessions_key, set()))
            count = len(tokens)

        # Simulate event publication: invalidate L1 cache for this user's session_version
        # (In production this would be a Pub/Sub or Kafka event to all nodes)
        self._invalidate_sv_cache(tenant_id, user_id)

        return count

    def invalidate_session(self, token: str) -> bool:
        """
        Invalidate a single session by its token.

        This mirrors §7.2 "特定セッション無効化: session_status を revoked にし、
        イベント SessionRevoked(tid, session_id) を発行".
        Returns True if the session existed, False otherwise.
        """
        with self._store_lock:
            record = self._shared_store.get(f"sess:{token}")
            if record is None:
                return False

            tenant_id = record["tenant_id"]
            user_id = record["user_id"]
            session_id = record["session_id"]

            # Mark the session as revoked in the shared store
            revoked_key = self._revoked_sess_key(tenant_id, session_id)
            self._shared_store[revoked_key] = True

            # Remove from user's token index
            user_sessions_key = self._user_sessions_key(tenant_id, user_id)
            tokens: set = self._shared_store.get(user_sessions_key, set())
            tokens.discard(token)

            # Remove the session record itself
            del self._shared_store[f"sess:{token}"]

        # Simulate event: invalidate L1 cache entry for this session
        self._invalidate_revoked_sess_cache(tenant_id, session_id)

        return True

    # ------------------------------------------------------------------
    # Internal helpers: L1 cache with shared store fallback
    # ------------------------------------------------------------------

    def _get_session_version(self, tenant_id: str, user_id: str) -> int:
        """Get the current session_version, consulting L1 cache first."""
        sv_key = self._sv_key(tenant_id, user_id)

        with self._cache_lock:
            cached = self._local_cache.get(sv_key)
        if cached is not None:
            return cached

        # Cache miss: fetch from shared store and warm the cache
        with self._store_lock:
            sv = self._shared_store.get(sv_key, 0)
        with self._cache_lock:
            self._local_cache[sv_key] = sv
        return sv

    def _is_session_revoked(self, tenant_id: str, session_id: str) -> bool:
        """Check if a specific session has been individually revoked."""
        revoked_key = self._revoked_sess_key(tenant_id, session_id)

        with self._cache_lock:
            cached = self._local_cache.get(revoked_key)
        if cached is not None:
            return cached

        with self._store_lock:
            revoked = self._shared_store.get(revoked_key, False)
        with self._cache_lock:
            self._local_cache[revoked_key] = revoked
        return revoked

    def _invalidate_sv_cache(self, tenant_id: str, user_id: str) -> None:
        """Evict the L1 cache entry for a user's session_version (simulates event receipt)."""
        sv_key = self._sv_key(tenant_id, user_id)
        with self._cache_lock:
            self._local_cache.pop(sv_key, None)

    def _invalidate_revoked_sess_cache(self, tenant_id: str, session_id: str) -> None:
        """Evict the L1 cache entry for a specific session (simulates event receipt)."""
        revoked_key = self._revoked_sess_key(tenant_id, session_id)
        with self._cache_lock:
            self._local_cache.pop(revoked_key, None)

    # ------------------------------------------------------------------
    # Key builders (tenant-scoped to prevent cross-tenant leakage)
    # ------------------------------------------------------------------

    @staticmethod
    def _sv_key(tenant_id: str, user_id: str) -> str:
        return f"sv:{tenant_id}:{user_id}"

    @staticmethod
    def _revoked_sess_key(tenant_id: str, session_id: str) -> str:
        return f"revoked_sess:{tenant_id}:{session_id}"

    @staticmethod
    def _user_sessions_key(tenant_id: str, user_id: str) -> str:
        return f"user_sessions:{tenant_id}:{user_id}"
