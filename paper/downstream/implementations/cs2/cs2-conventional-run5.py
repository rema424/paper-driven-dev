"""
CS2-A-Run5: user_epoch + sid revocation set with L1 cache simulation
Design: Dual revocation paths — user_epoch counter AND explicit sid revocation set

Based on the Run 5 design analysis:
- JWT claims: tid(tenant), uid, sid(session_id), ue(user_epoch), exp, iat, aud
- Dual revocation mechanism:
    1. user_epoch (int): incremented on all-device revocation
    2. sid revocation set: explicit set of revoked session IDs (per-device revocation)
- L1 cache: simulated as a local dict with short TTL; event-driven invalidation
- Auth flow (low-latency, from analysis):
    1. API node verifies JWT signature (local key cache)
    2. Verify exp/aud/tid
    3. L1 cache: check sid in revocation set AND compare user_epoch
    4. Cache miss -> Redis 1 MGET (pipeline); result populates L1
    5. Revocation event -> immediately clear relevant L1 entries
- Keys always prefixed with tenant boundary (multi-tenant isolation)
- Revocation TTL matches token expiry (cleanup of stale entries)
- Audit log mandatory for admin operations
"""

import secrets
import threading
import time


_L1_TTL_SECONDS = 30  # Simulated L1 cache TTL (short, as recommended in analysis)


class _L1Cache:
    """
    Simulated per-node L1 (in-memory) cache for revocation state.
    In a real system this would be a process-local dict updated by Pub/Sub events.
    Entries expire after TTL to bound staleness when event delivery is delayed.
    """

    def __init__(self, ttl: float = _L1_TTL_SECONDS):
        self._ttl = ttl
        self._user_epoch: dict[tuple[str, str], tuple[int, float]] = {}  # (tenant,uid) -> (epoch, ts)
        self._revoked_sids: dict[tuple[str, str], float] = {}  # (tenant,sid) -> expiry_ts

    def get_user_epoch(self, tenant_id: str, user_id: str) -> int | None:
        entry = self._user_epoch.get((tenant_id, user_id))
        if entry is None:
            return None
        epoch, cached_at = entry
        if time.monotonic() - cached_at > self._ttl:
            del self._user_epoch[(tenant_id, user_id)]
            return None
        return epoch

    def set_user_epoch(self, tenant_id: str, user_id: str, epoch: int):
        self._user_epoch[(tenant_id, user_id)] = (epoch, time.monotonic())

    def invalidate_user_epoch(self, tenant_id: str, user_id: str):
        """Simulates event-driven L1 invalidation for user epoch."""
        self._user_epoch.pop((tenant_id, user_id), None)

    def is_sid_revoked(self, tenant_id: str, sid: str) -> bool | None:
        expiry = self._revoked_sids.get((tenant_id, sid))
        if expiry is None:
            return None  # cache miss
        if time.monotonic() > expiry:
            del self._revoked_sids[(tenant_id, sid)]
            return None
        return True

    def mark_sid_revoked(self, tenant_id: str, sid: str):
        self._revoked_sids[(tenant_id, sid)] = time.monotonic() + self._ttl

    def invalidate_sid(self, tenant_id: str, sid: str):
        """Force-invalidate a specific sid cache entry (event-driven)."""
        self._revoked_sids.pop((tenant_id, sid), None)


class SessionManager:
    """
    Dual-path revocation manager with L1 cache simulation.

    Storage layout:
      _user_epoch[tenant][uid]        -> int (current user epoch)
      _sessions[tenant][sid]          -> {user_id, device_id, ue, revoked}
      _user_sessions[tenant][uid]     -> set of sids
      _revoked_sids[tenant]           -> set of explicitly revoked sids
      _token_index[token]             -> (tenant_id, sid)
      _token_claims[token]            -> {ue: int}  (token-embedded claims)
      _audit_log                      -> list of audit entries
      _l1                             -> L1Cache instance (simulates per-node cache)
    """

    def __init__(self):
        # t:{tid}:u:{uid}:epoch  (from analysis key format)
        self._user_epoch: dict[str, dict[str, int]] = {}
        # session records
        self._sessions: dict[str, dict[str, dict]] = {}
        # user -> session set
        self._user_sessions: dict[str, dict[str, set]] = {}
        # explicit sid revocation set (per-device path)
        self._revoked_sids: dict[str, set] = {}
        # token reverse index
        self._token_index: dict[str, tuple[str, str]] = {}
        # token claims snapshot: {ue}
        self._token_claims: dict[str, dict] = {}
        # audit log (from analysis: 管理操作は監査ログ必須)
        self._audit_log: list[dict] = []
        # L1 cache (simulates per-node local cache)
        self._l1 = _L1Cache()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_epoch(self, tenant_id: str, user_id: str) -> int:
        """
        Simulates L1 cache -> Redis MGET fallback (analysis step 3/4).
        L1 hit: return cached epoch directly.
        L1 miss: fetch from "Redis" (backing dict) and populate L1.
        """
        cached = self._l1.get_user_epoch(tenant_id, user_id)
        if cached is not None:
            return cached
        # L1 miss -> fetch from backing store (Redis equivalent)
        epoch = self._user_epoch.get(tenant_id, {}).get(user_id, 0)
        self._l1.set_user_epoch(tenant_id, user_id, epoch)
        return epoch

    def _incr_epoch(self, tenant_id: str, user_id: str) -> int:
        tenant_map = self._user_epoch.setdefault(tenant_id, {})
        new_epoch = tenant_map.get(user_id, 0) + 1
        tenant_map[user_id] = new_epoch
        # Invalidate L1 (simulates Pub/Sub event -> each node clears its L1)
        self._l1.invalidate_user_epoch(tenant_id, user_id)
        return new_epoch

    def _is_sid_revoked(self, tenant_id: str, sid: str) -> bool:
        """
        Check sid revocation via L1 cache first, then backing store.
        """
        l1_result = self._l1.is_sid_revoked(tenant_id, sid)
        if l1_result is not None:
            return l1_result
        # L1 miss -> check backing store
        revoked = sid in self._revoked_sids.get(tenant_id, set())
        if revoked:
            self._l1.mark_sid_revoked(tenant_id, sid)
        return revoked

    def _add_revoked_sid(self, tenant_id: str, sid: str):
        self._revoked_sids.setdefault(tenant_id, set()).add(sid)
        # Broadcast to L1 (simulates event dispatch -> each node updates cache)
        self._l1.mark_sid_revoked(tenant_id, sid)

    def _audit(self, action: str, tenant_id: str, user_id: str, **kwargs):
        self._audit_log.append({
            "ts": time.time(),
            "action": action,
            "tenant_id": tenant_id,
            "user_id": user_id,
            **kwargs,
        })

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """
        Issue a new session, embedding current user_epoch as 'ue' claim.
        Each call produces an independent session (per-device, per call).
        Keys include tenant_id prefix for isolation (t:{tid}:u:{uid}:epoch).
        """
        sid = secrets.token_hex(16)
        token = secrets.token_urlsafe(32)

        with self._lock:
            ue = self._get_epoch(tenant_id, user_id)

            self._sessions.setdefault(tenant_id, {})[sid] = {
                "user_id": user_id,
                "device_id": device_id,
                "ue": ue,
                "revoked": False,
            }
            self._user_sessions.setdefault(tenant_id, {}).setdefault(user_id, set()).add(sid)
            self._token_index[token] = (tenant_id, sid)
            self._token_claims[token] = {"ue": ue}

        return token

    def validate_session(self, token: str) -> dict | None:
        """
        Five-step validation (from analysis auth flow):
          1. Resolve token to (tenant, sid)
          2. Verify exp/aud/tid (here: token presence acts as exp check)
          3. L1 cache: check sid in revocation set
          4. L1 cache: compare token.ue with current user_epoch
          5. Cache miss -> backing store lookup (simulated as in-memory)

        This path is designed for minimal I/O: L1 hits complete validation
        with no external calls. Only misses fall through to the backing store.
        """
        with self._lock:
            location = self._token_index.get(token)
            if location is None:
                return None

            tenant_id, sid = location
            session = self._sessions.get(tenant_id, {}).get(sid)
            if session is None:
                return None

            # Step 3: sid revocation set check (L1 -> backing store)
            if self._is_sid_revoked(tenant_id, sid):
                return None

            # Step 4: user_epoch comparison (L1 -> backing store)
            token_ue = self._token_claims[token]["ue"]
            current_ue = self._get_epoch(tenant_id, session["user_id"])
            if token_ue != current_ue:
                # Epoch mismatch: user has been bulk-invalidated
                return None

            return {
                "tenant_id": tenant_id,
                "user_id": session["user_id"],
                "device_id": session["device_id"],
            }

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """
        All-device invalidation via user_epoch increment (from analysis):
          - INCR t:{tid}:u:{uid}:epoch
          - Broadcast revocation event -> each node's L1 clears epoch cache
        All tokens carrying old ue will fail step 4 immediately.
        Also adds each sid to the explicit revocation set for defense-in-depth.
        Returns count of sessions that were active before invalidation.
        """
        with self._lock:
            new_ue = self._incr_epoch(tenant_id, user_id)

            sids = self._user_sessions.get(tenant_id, {}).get(user_id, set())
            tenant_sessions = self._sessions.get(tenant_id, {})
            count = 0
            for sid in sids:
                sess = tenant_sessions.get(sid)
                if sess is not None and not sess["revoked"]:
                    sess["revoked"] = True
                    self._add_revoked_sid(tenant_id, sid)
                    count += 1

            self._audit(
                action="invalidate_user_sessions",
                tenant_id=tenant_id,
                user_id=user_id,
                new_ue=new_ue,
                revoked_count=count,
            )

        return count

    def invalidate_session(self, token: str) -> bool:
        """
        Per-device invalidation via explicit sid revocation set (from analysis):
          - Add sid to revocation set
          - Broadcast event -> each node's L1 marks sid as revoked
        user_epoch is NOT incremented; other sessions remain valid.
        Returns True if the token was found.
        """
        with self._lock:
            location = self._token_index.get(token)
            if location is None:
                return False

            tenant_id, sid = location
            session = self._sessions.get(tenant_id, {}).get(sid)
            if session is None:
                return False

            session["revoked"] = True
            self._add_revoked_sid(tenant_id, sid)

            self._audit(
                action="invalidate_session",
                tenant_id=tenant_id,
                user_id=session["user_id"],
                sid=sid,
            )

        return True
