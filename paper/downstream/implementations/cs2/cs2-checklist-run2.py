"""
CS2 Checklist Run 2 — Multi-tenant SaaS Session Management

Design basis: cs2-checklist-run2.md (CS2-D-Run2, GPT-5.2 via Codex)

Key design decisions reflected:
- Hybrid approach: short-lived access tokens + central revocation state
- user_session_version embedded in token; validated against shared store
- L1 in-memory cache per node; only consults shared store on cache miss
- Admin revocation: atomically increments version + publishes invalidation event to L1
- Refresh Token managed centrally; deleted immediately on revocation
- Key space strictly prefixed by tenant_id for tenant isolation
- API nodes are fully stateless (all session state lives in shared store)

The analysis (§7.1) states the core principle:
  "Access Tokenは短命JWT（例: 5分）でローカル検証。
   user_session_version をトークンに含め、Redisの最新版と比較して失効判定。
   管理者失効時は対象ユーザーのversionを原子的にインクリメントし、全ノードへイベント配信。"

Tradeoff noted in §2: "低レイテンシ と 即時失効" —
the L1 cache satisfies low-latency; version-increment + cache eviction satisfies instant revocation.
"""

import secrets
import time
import threading
from typing import Optional


class SessionManager:
    """
    Multi-tenant session manager based on the Run 2 checklist analysis.

    Simulated storage:
      _shared_store:
        "sv:{tid}:{uid}"              -> int   (user session_version / "user_session_version")
        "sess:{token}"                -> dict  (session record: tenant_id, user_id, device_id,
                                                session_id, sv_at_creation)
        "user_sessions:{tid}:{uid}"   -> set   (all active tokens for a user in a tenant)
        "refresh:{token}"             -> dict  (refresh token record; deleted on revocation)

      _l1_cache (per-node, simulates L1 memory cache):
        "sv:{tid}:{uid}"              -> int   (cached session_version)
    """

    def __init__(self) -> None:
        self._shared_store: dict = {}
        self._store_lock = threading.Lock()

        # L1 cache: simulates per-node in-memory state that is invalidated via Pub/Sub events
        self._l1_cache: dict = {}
        self._cache_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """
        Issue a new session for a specific device.

        §7.2 step 1: "ログイン時に session_id を端末単位で発行し、
        JWT claimsに tenant_id/user_id/session_id/version を格納。"
        Here we use an opaque token instead of JWT (in-memory implementation).
        """
        token = secrets.token_urlsafe(32)
        session_id = secrets.token_urlsafe(16)

        sv_key = self._sv_key(tenant_id, user_id)
        user_sessions_key = self._user_sessions_key(tenant_id, user_id)

        with self._store_lock:
            if sv_key not in self._shared_store:
                self._shared_store[sv_key] = 0
            current_sv = self._shared_store[sv_key]

            self._shared_store[f"sess:{token}"] = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "device_id": device_id,
                "session_id": session_id,
                "sv_at_creation": current_sv,
                "created_at": time.time(),
            }

            if user_sessions_key not in self._shared_store:
                self._shared_store[user_sessions_key] = set()
            self._shared_store[user_sessions_key].add(token)

        return token

    def validate_session(self, token: str) -> Optional[dict]:
        """
        Validate token.

        §7.2 step 2: "認証ミドルウェアは署名検証後、L1メモリキャッシュの user_version を参照。
        未ヒット時のみRedis参照。"

        Returns {'tenant_id', 'user_id', 'device_id'} if valid, else None.
        """
        with self._store_lock:
            record = self._shared_store.get(f"sess:{token}")

        if record is None:
            return None

        tenant_id = record["tenant_id"]
        user_id = record["user_id"]
        sv_at_creation = record["sv_at_creation"]

        # Consult L1 cache first; fall back to shared store on miss
        current_sv = self._get_sv(tenant_id, user_id)

        # If the current version is higher than what was baked into the token,
        # the user's sessions were bulk-revoked after this token was issued.
        if current_sv != sv_at_creation:
            return None

        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "device_id": record["device_id"],
        }

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """
        Bulk-revoke all sessions for a user by incrementing session_version.

        §7.2 step 3: "管理者失効APIはRedis Lua等で version++ とRefresh削除を原子的に実行し、
        Pub/Subで全APIノードのL1キャッシュを即時無効化。"
        Returns count of sessions that were active.
        """
        sv_key = self._sv_key(tenant_id, user_id)
        user_sessions_key = self._user_sessions_key(tenant_id, user_id)

        with self._store_lock:
            # Atomic version increment (simulates Redis Lua script)
            self._shared_store[sv_key] = self._shared_store.get(sv_key, 0) + 1

            tokens: set = set(self._shared_store.get(user_sessions_key, set()))
            count = len(tokens)

            # Also clean up refresh tokens for these sessions
            for t in tokens:
                record = self._shared_store.get(f"sess:{t}")
                if record:
                    sid = record["session_id"]
                    self._shared_store.pop(f"refresh:{sid}", None)

        # Simulate Pub/Sub event: invalidate L1 cache for this user's version
        self._evict_sv_cache(tenant_id, user_id)

        return count

    def invalidate_session(self, token: str) -> bool:
        """
        Revoke a single session token immediately.

        For fine-grained (per-device) revocation the version approach is not enough;
        we remove the session record directly and evict any cached sv entry so the
        next validation cannot find the record.
        Returns True if the session existed, False otherwise.
        """
        with self._store_lock:
            record = self._shared_store.pop(f"sess:{token}", None)
            if record is None:
                return False

            tenant_id = record["tenant_id"]
            user_id = record["user_id"]
            session_id = record["session_id"]

            # Remove from user session index
            user_sessions_key = self._user_sessions_key(tenant_id, user_id)
            tokens: set = self._shared_store.get(user_sessions_key, set())
            tokens.discard(token)

            # Remove associated refresh token
            self._shared_store.pop(f"refresh:{session_id}", None)

        # Simulate event: other nodes would also drop this token on next request
        # (Since record is deleted from shared store, any cache miss will return None)
        self._evict_sv_cache(tenant_id, user_id)

        return True

    # ------------------------------------------------------------------
    # Internal: L1 cache helpers
    # ------------------------------------------------------------------

    def _get_sv(self, tenant_id: str, user_id: str) -> int:
        """Return session_version from L1 cache, or fetch from shared store."""
        sv_key = self._sv_key(tenant_id, user_id)

        with self._cache_lock:
            cached = self._l1_cache.get(sv_key)
        if cached is not None:
            return cached

        # Cache miss — consult shared store
        with self._store_lock:
            sv = self._shared_store.get(sv_key, 0)

        with self._cache_lock:
            self._l1_cache[sv_key] = sv

        return sv

    def _evict_sv_cache(self, tenant_id: str, user_id: str) -> None:
        """Evict L1 cache entry; simulates receiving the Pub/Sub invalidation event."""
        sv_key = self._sv_key(tenant_id, user_id)
        with self._cache_lock:
            self._l1_cache.pop(sv_key, None)

    # ------------------------------------------------------------------
    # Key builders — tenant-prefixed for strict isolation (§2 "テナント分離")
    # ------------------------------------------------------------------

    @staticmethod
    def _sv_key(tenant_id: str, user_id: str) -> str:
        return f"sv:{tenant_id}:{user_id}"

    @staticmethod
    def _user_sessions_key(tenant_id: str, user_id: str) -> str:
        return f"user_sessions:{tenant_id}:{user_id}"
