"""
CS2-B-Run3: Short-lived access token + user_epoch logical clock + L1 cache.

Design basis: cs2-paper-format-run3.md

Key design decisions from the paper:
- user_epoch as a logical clock (integer, monotonically increasing) per (tid, uid)
- Access token claims include: tid, uid, sid, uep (epoch), iat, exp
- refresh_valid_after: timestamp gate to invalidate existing refresh tokens (§2.2)
- L1 in-node memory cache for user_epoch; KVS only on cache miss (§2.3)
- High-risk operations can additionally verify session:{sid} in KVS
- Invalidation atomically: INCR epoch + SET refresh_valid_after + event dispatch
- Fail-safe: if event bus is delayed, nodes fall back to KVS direct lookup (§5)
- Tenant isolation: every key and claim includes tid
- Audit logging stub to satisfy the "must persist who invalidated whom" requirement
"""

import secrets
import hashlib
import hmac as _hmac_mod
import json
import time
from typing import Optional


# ---------------------------------------------------------------------------
# Signing infrastructure
# ---------------------------------------------------------------------------

_SIGNING_SECRET = secrets.token_bytes(32)
_ACCESS_TOKEN_TTL = 300  # 2-5 minutes per paper; using 5 min here


def _sign_payload(payload: dict) -> str:
    import base64
    body = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()
    sig = _hmac_mod.new(_SIGNING_SECRET, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def _verify_payload(token: str) -> Optional[dict]:
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
# SessionManager
# ---------------------------------------------------------------------------

class SessionManager:
    """
    Logical-clock epoch session manager with L1 cache and fail-safe mode (Run 3).

    State stores (simulating KVS + L1 cache layers):

    KVS layer (distributed KVS simulation):
        _kvs_user_epoch[(tid, uid)]        -> int
        _kvs_refresh_valid_after[(tid,uid)] -> float (Unix timestamp)
        _kvs_session[(tid, sid)]            -> {uid, device_id, status, expires_at}

    L1 cache (per-node in-process memory):
        _l1_epoch[(tid, uid)]              -> int
        _l1_revoked_sids                   -> set of (tid, sid)

    Audit log:
        _audit_log                          -> list of dict records

    The fail-safe flag _force_kvs_mode simulates the "event bus delayed →
    fall back to KVS direct reference" behaviour from §5.
    """

    def __init__(self) -> None:
        # KVS layer
        self._kvs_user_epoch: dict[tuple, int] = {}
        self._kvs_refresh_valid_after: dict[tuple, float] = {}
        self._kvs_session: dict[tuple, dict] = {}

        # L1 cache layer (updated by simulated event bus)
        self._l1_epoch: dict[tuple, int] = {}
        self._l1_revoked_sids: set[tuple] = set()

        # Audit log (satisfy §5 requirement: who invalidated whom, when)
        self._audit_log: list[dict] = []

        # When True, validate_session bypasses L1 and reads KVS directly
        self._force_kvs_mode: bool = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_epoch(self, tid: str, uid: str) -> int:
        """Retrieve the current epoch: L1 first, then KVS on miss (§2.3)."""
        key = (tid, uid)
        if not self._force_kvs_mode and key in self._l1_epoch:
            return self._l1_epoch[key]
        # KVS fallback
        epoch = self._kvs_user_epoch.get(key, 0)
        self._l1_epoch[key] = epoch  # populate cache
        return epoch

    def _dispatch_event(self, event: dict) -> None:
        """Simulate event bus dispatch: update all 'remote node' L1 caches.

        In a real deployment this would publish to Redis Streams / Kafka.
        The in-memory prototype updates the single shared L1 directly.
        """
        etype = event.get("type")
        if etype == "revoke_user":
            tid, uid, epoch = event["tid"], event["uid"], event["epoch"]
            self._l1_epoch[(tid, uid)] = epoch
        elif etype == "revoke_session":
            tid, sid = event["tid"], event["sid"]
            self._l1_revoked_sids.add((tid, sid))

    def _audit(self, action: str, tid: str, uid: str, **extra) -> None:
        """Persist an audit record (§5: must log who invalidated whom, when)."""
        self._audit_log.append({
            "action": action,
            "tenant_id": tid,
            "user_id": uid,
            "timestamp": time.time(),
            **extra,
        })

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """Create a short-lived access token for (tenant, user, device).

        The token embeds the current user_epoch (uep), allowing every
        validate call to compare against the L1-cached epoch without
        touching the KVS on the hot path.

        A unique sid per device enables concurrent multi-device logins (R1).
        """
        sid = secrets.token_hex(16)
        now = time.time()
        epoch = self._get_epoch(tenant_id, user_id)

        payload = {
            "tid": tenant_id,
            "uid": user_id,
            "sid": sid,
            "uep": epoch,
            "iat": now,
            "exp": now + _ACCESS_TOKEN_TTL,
        }
        token = _sign_payload(payload)

        self._kvs_session[(tenant_id, sid)] = {
            "uid": user_id,
            "device_id": device_id,
            "status": "active",
            "expires_at": now + _ACCESS_TOKEN_TTL,
        }
        return token

    def validate_session(self, token: str) -> Optional[dict]:
        """Validate an access token using the logical-clock epoch algorithm.

        Authentication steps (§2.3):
        1. Verify signature locally.
        2. Check exp locally.
        3. Look up user_epoch from L1 (miss → KVS); reject if token.uep != current.
        4. Check per-device revocation set.
        5. Optionally verify session:{sid} in KVS (high-risk path; always done here).

        Returns {"tenant_id", "user_id", "device_id"} if valid, else None.
        """
        payload = _verify_payload(token)
        if payload is None:
            return None

        if time.time() > payload.get("exp", 0):
            return None

        tid = payload.get("tid")
        uid = payload.get("uid")
        sid = payload.get("sid")
        token_epoch = payload.get("uep", 0)

        if not all([tid, uid, sid]):
            return None

        # Step 3: epoch check — the core of the logical-clock mechanism
        current_epoch = self._get_epoch(tid, uid)
        if token_epoch != current_epoch:
            return None

        # Step 4: per-device revocation
        if (tid, sid) in self._l1_revoked_sids:
            return None

        # Step 5: KVS session record check
        session = self._kvs_session.get((tid, sid))
        if session is None or session.get("status") != "active":
            return None

        return {
            "tenant_id": tid,
            "user_id": uid,
            "device_id": session["device_id"],
        }

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """Invalidate all sessions for a user via atomic epoch increment (§2.4).

        Operations (performed atomically in the KVS simulation):
        1. INCR user_epoch:{tid}:{uid}
        2. SET refresh_valid_after:{tid}:{uid} = now()
        3. Dispatch revoke_user event (Pub/Sub simulation)

        After this call, any access token carrying the old epoch will fail
        the epoch comparison in validate_session (R2).

        Returns the count of active session records that were deactivated.
        """
        key = (tenant_id, user_id)
        new_epoch = self._kvs_user_epoch.get(key, 0) + 1
        self._kvs_user_epoch[key] = new_epoch
        self._kvs_refresh_valid_after[key] = time.time()

        # Event bus: all API nodes update their L1 cache
        self._dispatch_event({
            "type": "revoke_user",
            "tid": tenant_id,
            "uid": user_id,
            "epoch": new_epoch,
        })

        # Audit
        self._audit("invalidate_user", tenant_id, user_id, new_epoch=new_epoch)

        # Deactivate session records and count them
        count = 0
        for (tid, sid), session in self._kvs_session.items():
            if tid == tenant_id and session.get("uid") == user_id:
                if session.get("status") == "active":
                    session["status"] = "revoked"
                    count += 1
        return count

    def invalidate_session(self, token: str) -> bool:
        """Invalidate a single device session.

        Marks the session record as revoked in the KVS and dispatches a
        revoke_session event so that L1 caches on all nodes add the sid
        to their local revocation set.

        Returns True if the session existed and was revoked, False otherwise.
        """
        payload = _verify_payload(token)
        if payload is None:
            return False

        tid = payload.get("tid")
        sid = payload.get("sid")
        uid = payload.get("uid")
        if not (tid and sid):
            return False

        session = self._kvs_session.get((tid, sid))
        if session is None or session.get("status") != "active":
            return False

        session["status"] = "revoked"

        # Event bus dispatch
        self._dispatch_event({
            "type": "revoke_session",
            "tid": tid,
            "sid": sid,
        })

        self._audit("invalidate_session", tid, uid or "", session_id=sid)
        return True
