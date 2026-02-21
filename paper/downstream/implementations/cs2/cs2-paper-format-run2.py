"""
CS2-B-Run2: Hybrid short-lived JWT + user_epoch invalidation.

Design basis: cs2-paper-format-run2.md

Key design decisions from the paper:
- Short-lived access tokens (JWT-like, ~120s) issued per device session (sid)
- user_epoch per (tenant, user): atomic INCR for full-user invalidation (R2)
- session:{tid}:{sid} records for per-device (single-session) invalidation
- Pub/Sub event bus to propagate revocation to all API nodes (in-memory simulation)
- Local cache for user_epoch to avoid Redis on every request (R4)
- Stateless API nodes; all durable state in Redis Cluster simulation (R3)

Token claims: {tid, uid, sid, ue (user_epoch), iat, exp}
"""

import secrets
import hashlib
import hmac
import json
import time
from typing import Optional


# ---------------------------------------------------------------------------
# Simulated signing infrastructure
# ---------------------------------------------------------------------------

_SIGNING_SECRET = secrets.token_bytes(32)
_TOKEN_TTL = 120  # seconds — short-lived, matching the paper's example


def _sign(payload: dict) -> str:
    """Produce a compact signed token: base64url(payload).HMAC-SHA256."""
    import base64
    body = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()
    sig = hmac.new(
        _SIGNING_SECRET,
        body.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{body}.{sig}"


def _verify(token: str) -> Optional[dict]:
    """Verify HMAC signature and return the payload dict, or None if invalid."""
    import base64
    try:
        body, sig = token.rsplit(".", 1)
    except ValueError:
        return None
    expected = hmac.new(_SIGNING_SECRET, body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    padding = "=" * (-len(body) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(body + padding))
    except Exception:
        return None
    return payload


# ---------------------------------------------------------------------------
# SessionManager
# ---------------------------------------------------------------------------

class SessionManager:
    """
    Hybrid JWT + user_epoch session manager (Run 2).

    Storage layout:
        _user_epoch[(tid, uid)]   -> int   (current epoch; starts at 0)
        _sessions[(tid, sid)]     -> {"uid", "device_id", "status", "expires_at"}
        _revoked_sids             -> set of (tid, sid)  (per-device revocations)
        _epoch_cache[(tid, uid)]  -> int   (L1 cache; updated by Pub/Sub events)

    The _epoch_cache simulates the in-process L1 memory cache described in §3.
    In a single-process prototype it is the same dict as _user_epoch, but the
    separation models the two-layer lookup (L1 first, then the KVS on miss).

    Pub/Sub is simulated: invalidation immediately updates _epoch_cache and
    _revoked_sids so that subsequent validate_session calls reflect the change
    without any network round-trip (mirrors the "all API nodes update instantly"
    guarantee of the paper).
    """

    def __init__(self) -> None:
        # Simulates Redis: user_epoch:{tid}:{uid}
        self._user_epoch: dict[tuple, int] = {}
        # Simulates Redis: session:{tid}:{sid}
        self._sessions: dict[tuple, dict] = {}
        # L1 per-process cache for user_epoch (updated by simulated Pub/Sub)
        self._epoch_cache: dict[tuple, int] = {}
        # Per-device revocation set (populated by single-session invalidation)
        self._revoked_sids: set[tuple] = set()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _current_epoch(self, tid: str, uid: str) -> int:
        """Return the authoritative epoch, consulting L1 then the KVS."""
        key = (tid, uid)
        # L1 hit
        if key in self._epoch_cache:
            return self._epoch_cache[key]
        # KVS miss path
        epoch = self._user_epoch.get(key, 0)
        self._epoch_cache[key] = epoch
        return epoch

    def _broadcast_revocation(self, tid: str, uid: str, new_epoch: int) -> None:
        """Simulate Pub/Sub: push new epoch to all API node L1 caches."""
        # In a real system this would publish to a channel and all subscribers
        # would update their local caches.  In this in-memory prototype we
        # update the single shared cache directly.
        self._epoch_cache[(tid, uid)] = new_epoch

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """Issue a short-lived signed access token for the given device.

        A unique sid is minted per device; the same (tenant, user) can hold
        multiple concurrent sids (R1 — multiple devices).

        The token embeds: tid, uid, sid, ue (current user_epoch), iat, exp.
        """
        sid = secrets.token_hex(16)
        now = time.time()
        epoch = self._current_epoch(tenant_id, user_id)

        payload = {
            "tid": tenant_id,
            "uid": user_id,
            "sid": sid,
            "ue": epoch,
            "iat": now,
            "exp": now + _TOKEN_TTL,
        }
        token = _sign(payload)

        # Persist session metadata in the KVS simulation
        self._sessions[(tenant_id, sid)] = {
            "uid": user_id,
            "device_id": device_id,
            "status": "active",
            "expires_at": now + _TOKEN_TTL,
        }
        return token

    def validate_session(self, token: str) -> Optional[dict]:
        """Validate a signed access token.

        Authentication algorithm (§3.3):
        1. Verify HMAC signature and exp locally.
        2. Compare token's user_epoch (ue) against L1-cached current epoch;
           fetch from KVS only on cache miss.
        3. Check per-device revocation set.
        4. If all checks pass, return identity dict.

        This keeps the hot path entirely local (R4).
        """
        payload = _verify(token)
        if payload is None:
            return None

        # Step 1: expiry check (local)
        if time.time() > payload.get("exp", 0):
            return None

        tid = payload.get("tid")
        uid = payload.get("uid")
        sid = payload.get("sid")
        token_epoch = payload.get("ue", 0)

        if not all([tid, uid, sid]):
            return None

        # Step 2: epoch comparison (L1 first, KVS on miss)
        current_epoch = self._current_epoch(tid, uid)
        if token_epoch != current_epoch:
            # Epoch mismatch: the token was issued before the last full-user
            # revocation — reject immediately.
            return None

        # Step 3: per-device revocation check
        if (tid, sid) in self._revoked_sids:
            return None

        # Resolve device_id from the session store
        session = self._sessions.get((tid, sid))
        if session is None or session.get("status") != "active":
            return None

        return {
            "tenant_id": tid,
            "user_id": uid,
            "device_id": session["device_id"],
        }

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """Invalidate ALL sessions for a user by incrementing their epoch (§3.2).

        The user_epoch is atomically incremented in the KVS, then broadcast
        via Pub/Sub to all API-node L1 caches.  Any token carrying the old
        epoch value will fail the epoch comparison on the next validate call.

        Returns the number of session records that were marked inactive.
        """
        key = (tenant_id, user_id)
        new_epoch = self._user_epoch.get(key, 0) + 1
        self._user_epoch[key] = new_epoch

        # Pub/Sub: propagate new epoch to all L1 caches instantly
        self._broadcast_revocation(tenant_id, user_id, new_epoch)

        # Count and deactivate matching session records
        count = 0
        for (tid, sid), session in self._sessions.items():
            if tid == tenant_id and session.get("uid") == user_id:
                if session.get("status") == "active":
                    session["status"] = "revoked"
                    count += 1
        return count

    def invalidate_session(self, token: str) -> bool:
        """Invalidate a single device session (per-device revocation).

        Marks the sid in both the KVS session record and the local revocation
        set.  The revoked-sid check in validate_session will then reject any
        subsequent tokens carrying this sid.

        Returns True if the session existed and was revoked, False otherwise.
        """
        payload = _verify(token)
        if payload is None:
            return False

        tid = payload.get("tid")
        sid = payload.get("sid")
        if not (tid and sid):
            return False

        session = self._sessions.get((tid, sid))
        if session is None:
            return False

        if session.get("status") == "revoked":
            # Already revoked; signal "not found / already gone"
            return False

        session["status"] = "revoked"
        self._revoked_sids.add((tid, sid))

        # Publish per-device revocation event (simulated)
        # Other nodes would add (tid, sid) to their own _revoked_sids.
        return True
