"""
CS2 Checklist Run 3 — Multi-tenant SaaS Session Management

Design basis: cs2-checklist-run3.md (CS2-D-Run3, GPT-5.2 via Codex)

Key design decisions reflected:
- Two-layer revocation hierarchy: user_epoch (bulk) + per-session revocation key
- session_id issued per device; Access Token carries tenant_id, user_id, session_id,
  user_epoch, exp (§7.2)
- Authentication: local signature verification first, then L1-cached revocation state
  (revoked_session flag and user_epoch); Redis only on cache miss
- Admin bulk revocation: increment user_epoch + publish event → all nodes evict L1 entry
- Admin single-session revocation: set revoked_session key + publish event
- Tenant isolation: all storage keys are tenant-prefixed
- Horizontal scale: API nodes are stateless; L1 cache is rebuildable from shared store

§6 identifies the core difficulty:
  "分散環境で「ほぼ即時の全体失効」と「認証のローカル高速処理」を同時成立させる点"
Resolved by L1 cache + event-driven invalidation.
"""

import secrets
import time
import threading
from typing import Optional


class SessionManager:
    """
    Multi-tenant session manager — Run 3 design.

    Shared store keys:
      "epoch:{tid}:{uid}"          -> int   (user_epoch; INCR for bulk revocation)
      "revoked:{tid}:{sid}"        -> bool  (True when single session revoked)
      "sess:{token}"               -> dict  (session record)
      "user_tokens:{tid}:{uid}"    -> set   (all live tokens for a user)

    L1 cache keys (same names; evicted on revocation events):
      "epoch:{tid}:{uid}"          -> int
      "revoked:{tid}:{sid}"        -> bool
    """

    def __init__(self) -> None:
        self._shared_store: dict = {}
        self._store_lock = threading.Lock()

        self._l1: dict = {}
        self._l1_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """
        Issue a new device session.

        §7.2: "session_id を端末ごとに発行し、Access Token に
        tenant_id, user_id, session_id, user_epoch, exp を含めます。"
        """
        token = secrets.token_urlsafe(32)
        session_id = secrets.token_urlsafe(16)

        epoch_key = self._epoch_key(tenant_id, user_id)
        user_tokens_key = self._user_tokens_key(tenant_id, user_id)

        with self._store_lock:
            if epoch_key not in self._shared_store:
                self._shared_store[epoch_key] = 0
            current_epoch = self._shared_store[epoch_key]

            self._shared_store[f"sess:{token}"] = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "device_id": device_id,
                "session_id": session_id,
                "epoch_at_creation": current_epoch,
                "created_at": time.time(),
            }

            if user_tokens_key not in self._shared_store:
                self._shared_store[user_tokens_key] = set()
            self._shared_store[user_tokens_key].add(token)

        return token

    def validate_session(self, token: str) -> Optional[dict]:
        """
        Validate a session token using the two-layer check.

        §7.2 auth flow:
          1. Local signature verification (here: token lookup — analogous to JWT sig verify)
          2. Check revoked_session flag via L1 → shared store
          3. Check user_epoch via L1 → shared store

        Returns {'tenant_id', 'user_id', 'device_id'} or None.
        """
        with self._store_lock:
            record = self._shared_store.get(f"sess:{token}")

        if record is None:
            return None

        tenant_id = record["tenant_id"]
        user_id = record["user_id"]
        session_id = record["session_id"]
        epoch_at_creation = record["epoch_at_creation"]

        # Layer 1: per-session revocation check (L1 → shared store)
        if self._is_revoked(tenant_id, session_id):
            return None

        # Layer 2: user-epoch check (L1 → shared store)
        current_epoch = self._get_epoch(tenant_id, user_id)
        if current_epoch != epoch_at_creation:
            return None

        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "device_id": record["device_id"],
        }

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """
        Bulk-revoke all user sessions by incrementing user_epoch.

        §7.2: "全端末失効: user_epoch をインクリメントしてイベント配信。"
        Returns count of active sessions at time of invalidation.
        """
        epoch_key = self._epoch_key(tenant_id, user_id)
        user_tokens_key = self._user_tokens_key(tenant_id, user_id)

        with self._store_lock:
            self._shared_store[epoch_key] = self._shared_store.get(epoch_key, 0) + 1
            tokens: set = set(self._shared_store.get(user_tokens_key, set()))
            count = len(tokens)

        # Simulate event delivery: invalidate L1 epoch cache for this user
        self._evict_epoch(tenant_id, user_id)

        return count

    def invalidate_session(self, token: str) -> bool:
        """
        Revoke a single session (individual device logout).

        §7.2: "単一端末失効: session_id を失効化してイベント配信。"
        Returns True if session existed, False otherwise.
        """
        with self._store_lock:
            record = self._shared_store.pop(f"sess:{token}", None)
            if record is None:
                return False

            tenant_id = record["tenant_id"]
            user_id = record["user_id"]
            session_id = record["session_id"]

            # Mark session as revoked in shared store
            revoked_key = self._revoked_key(tenant_id, session_id)
            self._shared_store[revoked_key] = True

            # Remove from user token index
            user_tokens_key = self._user_tokens_key(tenant_id, user_id)
            tokens: set = self._shared_store.get(user_tokens_key, set())
            tokens.discard(token)

        # Simulate event: evict L1 entry for this session's revocation status
        self._evict_revoked(tenant_id, session_id)

        return True

    # ------------------------------------------------------------------
    # Internal: L1 cache with shared store fallback
    # ------------------------------------------------------------------

    def _get_epoch(self, tenant_id: str, user_id: str) -> int:
        """Return user_epoch from L1, or fetch and cache from shared store."""
        key = self._epoch_key(tenant_id, user_id)
        with self._l1_lock:
            v = self._l1.get(key)
        if v is not None:
            return v
        with self._store_lock:
            v = self._shared_store.get(key, 0)
        with self._l1_lock:
            self._l1[key] = v
        return v

    def _is_revoked(self, tenant_id: str, session_id: str) -> bool:
        """Return per-session revocation status from L1 or shared store."""
        key = self._revoked_key(tenant_id, session_id)
        with self._l1_lock:
            v = self._l1.get(key)
        if v is not None:
            return v
        with self._store_lock:
            v = self._shared_store.get(key, False)
        with self._l1_lock:
            self._l1[key] = v
        return v

    def _evict_epoch(self, tenant_id: str, user_id: str) -> None:
        key = self._epoch_key(tenant_id, user_id)
        with self._l1_lock:
            self._l1.pop(key, None)

    def _evict_revoked(self, tenant_id: str, session_id: str) -> None:
        key = self._revoked_key(tenant_id, session_id)
        with self._l1_lock:
            self._l1.pop(key, None)

    # ------------------------------------------------------------------
    # Key builders — tenant-prefixed (§4 "tenant_id 単位の厳密分離")
    # ------------------------------------------------------------------

    @staticmethod
    def _epoch_key(tenant_id: str, user_id: str) -> str:
        return f"epoch:{tenant_id}:{user_id}"

    @staticmethod
    def _revoked_key(tenant_id: str, session_id: str) -> str:
        return f"revoked:{tenant_id}:{session_id}"

    @staticmethod
    def _user_tokens_key(tenant_id: str, user_id: str) -> str:
        return f"user_tokens:{tenant_id}:{user_id}"
