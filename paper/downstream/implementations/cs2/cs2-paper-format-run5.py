"""
CS2-B-Run5: 4-layer architecture with formal correctness guarantee.

Design basis: cs2-paper-format-run5.md

Key design decisions from the paper:
- 4-layer architecture: auth middleware, session control, distributed cache, persistent
- user_version: monotonically increasing per (tenant_id, user_id), formal correctness
  guarantee: "once v_cur is incremented, token.user_version < v_cur always holds"
- Token claims: tenant_id, user_id, sid, user_version, exp
- Opaque refresh token stored hashed per device (sid); access token is short-lived signed
- L1 memory cache per API node for user_version; Pub/Sub to propagate changes
- invalidation: (1) INCR user_version, (2) mark sids revoked, (3) publish event
- Fail-safe: when event bus is stale, force Redis-direct mode (§4)
- Horizontal scale: no sticky sessions — API nodes are fully stateless (§5)
- Formal proposition (§4): if user_version is monotone and every request checks
  token.user_version < v_cur → reject, then no old token is accepted post-revocation.
"""

import secrets
import hashlib
import hmac as _hmac_mod
import json
import time
from typing import Optional


# ---------------------------------------------------------------------------
# Layer 1: Auth middleware — token signing & verification
# ---------------------------------------------------------------------------

_SIGNING_SECRET = secrets.token_bytes(32)
_ACCESS_TOKEN_TTL = 300  # 1-5 minutes per §3.2


def _encode(payload: dict) -> str:
    """Produce a compact signed token string."""
    import base64
    body = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()
    sig = _hmac_mod.new(_SIGNING_SECRET, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def _decode(token: str) -> Optional[dict]:
    """Verify and decode a signed token; return None if invalid."""
    import base64
    try:
        body, sig = token.rsplit(".", 1)
    except ValueError:
        return None
    expected = _hmac_mod.new(
        _SIGNING_SECRET, body.encode(), hashlib.sha256
    ).hexdigest()
    if not _hmac_mod.compare_digest(expected, sig):
        return None
    padding = "=" * (-len(body) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(body + padding))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Layers 2-4: Session control, distributed cache, persistent layer
# ---------------------------------------------------------------------------

class SessionManager:
    """
    4-layer session manager with formal user_version correctness (Run 5).

    Layer 2 — Session control: create_session, invalidate_user_sessions,
               invalidate_session.

    Layer 3 — Distributed cache simulation:
        _cache_version[(tenant_id, user_id)]    -> int  (user_version KVS)
        _cache_session[(tenant_id, sid)]        -> dict (session metadata)

    Layer 1/3 — L1 in-node memory:
        _l1_version[(tenant_id, user_id)]       -> int
        _l1_revoked_sids                        -> set of (tenant_id, sid)

    Layer 4 — Persistent layer (audit only in this prototype):
        _persistent_audit                       -> list of dicts

    Fail-safe flag: _force_cache_direct
        When True, validate_session always reads _cache_version directly,
        bypassing L1 (simulates the Redis-direct fallback on bus delays).

    Correctness proposition (§4):
        user_version is monotonically non-decreasing.
        For any token τ created at version v, and any future version v' >= v+1
        (achieved by at least one invalidate_user_sessions call),
        τ.user_version == v < v' == v_cur, so the check τ.user_version != v_cur
        will always fail, guaranteeing rejection.
    """

    def __init__(self) -> None:
        # Layer 3: distributed cache
        self._cache_version: dict[tuple, int] = {}
        self._cache_session: dict[tuple, dict] = {}

        # Layer 1/3: L1 per-node cache
        self._l1_version: dict[tuple, int] = {}
        self._l1_revoked_sids: set[tuple] = set()

        # Layer 4: persistent audit log
        self._persistent_audit: list[dict] = []

        # Fail-safe mode: forces direct cache read on validation
        self._force_cache_direct: bool = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _vk(self, tenant_id: str, user_id: str) -> tuple:
        """Compound key for user_version store."""
        return (tenant_id, user_id)

    def _sk(self, tenant_id: str, sid: str) -> tuple:
        """Compound key for session store."""
        return (tenant_id, sid)

    def _read_version(self, tenant_id: str, user_id: str) -> int:
        """Read user_version: L1 first, then distributed cache on miss.

        Implements Algorithm Auth step 3 from §3.3:
            v_cur = L1[k]  (miss → Redis reference)
        """
        vk = self._vk(tenant_id, user_id)
        if not self._force_cache_direct and vk in self._l1_version:
            return self._l1_version[vk]
        v = self._cache_version.get(vk, 0)
        self._l1_version[vk] = v
        return v

    def _publish_user_revoked(self, tenant_id: str, user_id: str, new_v: int) -> None:
        """Pub/Sub or Stream: propagate user_version increment to all API nodes."""
        # Each receiving node would run: l1_version[(tid, uid)] = new_v
        self._l1_version[self._vk(tenant_id, user_id)] = new_v

    def _publish_session_revoked(self, tenant_id: str, sid: str) -> None:
        """Pub/Sub: propagate single-session revocation flag to all API nodes."""
        self._l1_revoked_sids.add(self._sk(tenant_id, sid))

    def _persist_audit(self, action: str, tenant_id: str, user_id: str, **kw) -> None:
        """Write an audit record to the persistent layer (Layer 4)."""
        self._persistent_audit.append({
            "action": action,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "timestamp": time.time(),
            **kw,
        })

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """Create a new device session and return a short-lived access token.

        A unique sid per device supports concurrent sessions from the same
        user (R1 — same (tenant, user) can have N active sids).

        The access token embeds user_version at issue time.  Subsequent
        validate_session calls compare this embedded version against the
        current authoritative version to detect revocation (§3.3 step 4).
        """
        sid = secrets.token_hex(16)
        now = time.time()
        version = self._read_version(tenant_id, user_id)

        token = _encode({
            "tenant_id": tenant_id,
            "user_id": user_id,
            "sid": sid,
            "user_version": version,
            "exp": now + _ACCESS_TOKEN_TTL,
        })

        self._cache_session[self._sk(tenant_id, sid)] = {
            "user_id": user_id,
            "device_id": device_id,
            "status": "active",
            "expires_at": now + _ACCESS_TOKEN_TTL,
        }
        return token

    def validate_session(self, token: str) -> Optional[dict]:
        """Validate a session token using the formal Algorithm Auth (§3.3).

        ```
        Algorithm Auth(τ):
        1: verify signature and exp locally
        2: k = (tenant_id, user_id)
        3: v_cur = L1[k]  (miss → Redis ref)
        4: if τ.user_version < v_cur then Reject       ← formal proposition
        5: if sid revocation flag is set  then Reject
        6: Accept
        ```

        The formal correctness guarantee (§4): because user_version is
        monotone, τ.user_version != v_cur iff revocation occurred after τ
        was issued, so step 4 correctly rejects all post-revocation tokens.

        Returns {"tenant_id", "user_id", "device_id"} if valid, else None.
        """
        # Step 1: local signature + expiry
        payload = _decode(token)
        if payload is None:
            return None
        if time.time() > payload.get("exp", 0):
            return None

        tid = payload.get("tenant_id")
        uid = payload.get("user_id")
        sid = payload.get("sid")
        token_version = payload.get("user_version", -1)

        if not all(x is not None for x in [tid, uid, sid]):
            return None

        # Steps 3-4: user_version check (formal proposition from §4)
        v_cur = self._read_version(tid, uid)
        if token_version != v_cur:
            # Covers both: token issued before revocation (token_version < v_cur)
            # and any hypothetical future downgrade (token_version > v_cur, impossible
            # but guarded for robustness).
            return None

        # Step 5: per-device revocation flag
        if self._sk(tid, sid) in self._l1_revoked_sids:
            return None

        # Additional session record check (Layer 3)
        session = self._cache_session.get(self._sk(tid, sid))
        if session is None or session.get("status") != "active":
            return None

        return {
            "tenant_id": tid,
            "user_id": uid,
            "device_id": session["device_id"],
        }

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """Invalidate all sessions for a user via atomic user_version increment.

        Sequence (§3.4, 1 transaction):
        1. INCR user_version:{tenant_id}:{user_id}  in distributed cache
        2. Mark all active sids for this user as revoked in session cache
        3. Publish user-revocation event (Pub/Sub / Stream)

        Formal guarantee: after increment, v_cur > token.user_version for
        all tokens issued before this call, so they are all rejected (R2).

        Returns count of session records deactivated.
        """
        vk = self._vk(tenant_id, user_id)
        new_v = self._cache_version.get(vk, 0) + 1
        self._cache_version[vk] = new_v

        # Event propagation (Pub/Sub simulation)
        self._publish_user_revoked(tenant_id, user_id, new_v)

        self._persist_audit(
            "invalidate_user_sessions",
            tenant_id,
            user_id,
            new_version=new_v,
        )

        count = 0
        for (tid, sid), session in self._cache_session.items():
            if tid == tenant_id and session.get("user_id") == user_id:
                if session.get("status") == "active":
                    session["status"] = "revoked"
                    self._publish_session_revoked(tid, sid)
                    count += 1
        return count

    def invalidate_session(self, token: str) -> bool:
        """Invalidate a specific session by its access token.

        Marks the session record revoked in the distributed cache, then
        broadcasts the per-device revocation via Pub/Sub so that all API
        nodes add the sid to their L1 revocation sets.

        This allows targeted single-device logout without affecting the
        user's other active sessions (complement to invalidate_user_sessions).

        Returns True if the session existed and was active, False otherwise.
        """
        payload = _decode(token)
        if payload is None:
            return False

        tid = payload.get("tenant_id")
        uid = payload.get("user_id")
        sid = payload.get("sid")
        if not (tid and sid):
            return False

        sk = self._sk(tid, sid)
        session = self._cache_session.get(sk)
        if session is None or session.get("status") != "active":
            return False

        session["status"] = "revoked"
        self._publish_session_revoked(tid, sid)
        self._persist_audit("invalidate_session", tid, uid or "", session_id=sid)
        return True
