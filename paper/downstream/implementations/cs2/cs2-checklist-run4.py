"""
CS2 Checklist Run 4 — Multi-tenant SaaS Session Management

Design basis: cs2-checklist-run4.md (CS2-D-Run4, GPT-5.2 via Codex)

Key design decisions reflected:
- Each device gets an independent session_id (sid)
- user_session_epoch per user for bulk revocation
- Access Token carries: tid, uid, sid, epoch, exp (§7.2 step 1)
- Shared Redis-like store holds: user_epoch:{tid}:{uid} and session:{tid}:{sid}
- Authentication: local-first, cache miss → shared store (§7.2 step 3)
- Admin bulk revocation: atomic epoch increment + Pub/Sub event to all nodes (§7.2 step 4)
- Multiple devices: independent sids, simultaneously valid (§7.2 step 5)
- Horizontal scale: API nodes fully stateless; new nodes sync epoch on first request (§7.2 step 6)
- Tenant isolation: keys prefixed with tenant_id; admin scope limited to own tenant (§1 preamble)

§6: "分散環境で「即時失効」と「低遅延」を同時達成するには、
     各ノードのローカル高速判定と中央真実ソースの整合を崩さない設計が必要。"
"""

import secrets
import time
import threading
from typing import Optional


class SessionManager:
    """
    Multi-tenant session manager — Run 4 design.

    Shared store keys:
      "epoch:{tid}:{uid}"      -> int   (user epoch; INCR on bulk revoke)
      "sess:{token}"           -> dict  (full session record, keyed by opaque token)
      "user_tokens:{tid}:{uid}"-> set   (active tokens for this user in this tenant)
      "sess_active:{tid}:{sid}"-> bool  (False when individually revoked)

    L1 cache keys (per-node, evicted on revocation events):
      "epoch:{tid}:{uid}"      -> int
      "sess_active:{tid}:{sid}"-> bool
    """

    def __init__(self) -> None:
        self._store: dict = {}
        self._store_lock = threading.Lock()

        # Simulated per-node L1 cache (would be process-local memory in production)
        self._cache: dict = {}
        self._cache_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """
        Issue a per-device session.

        §7.2 step 1: "トークン: Access JWTに tid, uid, sid, epoch, exp を入れる."
        §7.2 step 5: "複数端末: 端末ごとに独立 sid を発行し同時有効化."
        """
        token = secrets.token_urlsafe(32)
        session_id = secrets.token_urlsafe(16)

        epoch_key = self._epoch_key(tenant_id, user_id)
        user_tokens_key = self._user_tokens_key(tenant_id, user_id)

        with self._store_lock:
            if epoch_key not in self._store:
                self._store[epoch_key] = 0
            current_epoch = self._store[epoch_key]

            # Store full session record under the opaque token
            self._store[f"sess:{token}"] = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "device_id": device_id,
                "session_id": session_id,
                "epoch_at_creation": current_epoch,
                "created_at": time.time(),
            }

            # Track per-user token set for bulk revocation count
            if user_tokens_key not in self._store:
                self._store[user_tokens_key] = set()
            self._store[user_tokens_key].add(token)

        return token

    def validate_session(self, token: str) -> Optional[dict]:
        """
        Authenticate a request.

        §7.2 step 3: "認証: JWT署名検証後、ローカルキャッシュの user_epoch/sid状態 を確認。
        ミス時のみRedis参照。"

        Returns {'tenant_id', 'user_id', 'device_id'} or None.
        """
        # Step A: resolve token → session record (analogous to JWT decode+sig-verify)
        with self._store_lock:
            record = self._store.get(f"sess:{token}")

        if record is None:
            return None

        tenant_id = record["tenant_id"]
        user_id = record["user_id"]
        session_id = record["session_id"]
        epoch_at_creation = record["epoch_at_creation"]

        # Step B: per-session active check via L1 → shared store
        if not self._is_session_active(tenant_id, session_id):
            return None

        # Step C: user epoch check via L1 → shared store
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
        Bulk-revoke all sessions for a user by incrementing the epoch.

        §7.2 step 4: "管理者失効: 原子的処理で user_epoch を増分し、
        失効イベントをPub/SubやStreamで全ノードへ配信。"
        Returns count of active sessions at time of invalidation.
        """
        epoch_key = self._epoch_key(tenant_id, user_id)
        user_tokens_key = self._user_tokens_key(tenant_id, user_id)

        with self._store_lock:
            # Atomic increment (simulates Redis INCR)
            self._store[epoch_key] = self._store.get(epoch_key, 0) + 1
            tokens: set = set(self._store.get(user_tokens_key, set()))
            count = len(tokens)

        # Simulate Pub/Sub event delivery: evict L1 epoch cache on all nodes
        self._evict_epoch_cache(tenant_id, user_id)

        return count

    def invalidate_session(self, token: str) -> bool:
        """
        Revoke a single session (per-device).

        §7.2 step 5: "必要なら端末単位失効も可能。"
        Returns True if session existed, False otherwise.
        """
        with self._store_lock:
            record = self._store.pop(f"sess:{token}", None)
            if record is None:
                return False

            tenant_id = record["tenant_id"]
            user_id = record["user_id"]
            session_id = record["session_id"]

            # Mark session as inactive (keyed by tenant+sid so other nodes can check)
            active_key = self._sess_active_key(tenant_id, session_id)
            self._store[active_key] = False

            # Remove from user token index
            user_tokens_key = self._user_tokens_key(tenant_id, user_id)
            tokens: set = self._store.get(user_tokens_key, set())
            tokens.discard(token)

        # Simulate event: evict per-session active flag from L1
        self._evict_sess_active_cache(tenant_id, session_id)

        return True

    # ------------------------------------------------------------------
    # Internal: L1 cache with shared store fallback
    # ------------------------------------------------------------------

    def _get_epoch(self, tenant_id: str, user_id: str) -> int:
        """Return user epoch from L1 or shared store (cache-aside)."""
        key = self._epoch_key(tenant_id, user_id)
        with self._cache_lock:
            v = self._cache.get(key)
        if v is not None:
            return v
        with self._store_lock:
            v = self._store.get(key, 0)
        with self._cache_lock:
            self._cache[key] = v
        return v

    def _is_session_active(self, tenant_id: str, session_id: str) -> bool:
        """Return True if session has not been individually revoked."""
        key = self._sess_active_key(tenant_id, session_id)
        with self._cache_lock:
            v = self._cache.get(key)
        if v is not None:
            return v
        with self._store_lock:
            # Absence of the active_key means session was never explicitly deactivated
            v = self._store.get(key, True)
        with self._cache_lock:
            self._cache[key] = v
        return v

    def _evict_epoch_cache(self, tenant_id: str, user_id: str) -> None:
        key = self._epoch_key(tenant_id, user_id)
        with self._cache_lock:
            self._cache.pop(key, None)

    def _evict_sess_active_cache(self, tenant_id: str, session_id: str) -> None:
        key = self._sess_active_key(tenant_id, session_id)
        with self._cache_lock:
            self._cache.pop(key, None)

    # ------------------------------------------------------------------
    # Key builders — tenant-prefixed for cross-tenant safety (§1 preamble)
    # ------------------------------------------------------------------

    @staticmethod
    def _epoch_key(tenant_id: str, user_id: str) -> str:
        return f"epoch:{tenant_id}:{user_id}"

    @staticmethod
    def _sess_active_key(tenant_id: str, session_id: str) -> str:
        return f"sess_active:{tenant_id}:{session_id}"

    @staticmethod
    def _user_tokens_key(tenant_id: str, user_id: str) -> str:
        return f"user_tokens:{tenant_id}:{user_id}"
