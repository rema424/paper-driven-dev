"""
CS2-B-Run4: user_version monotonic counter for O(1) full-user revocation.

Design basis: cs2-paper-format-run4.md

Key design decisions from the paper:
- user_version:{tenant_id}:{user_id} -> int  (monotonically increasing)
- session:{tenant_id}:{session_id} -> {user_id, refresh_hash, status, expires_at}
- Access token claims: {tenant_id, user_id, session_id, user_version, exp, iat, jti}
- All keys include tenant_id to enforce logical tenant isolation (§2.2)
- Per-device session_id issued at login; multiple sids per (tenant, user) allowed (R1)
- Full-user invalidation: INCR user_version + Pub/Sub → O(1) store operation (§3.3)
- L1 memory cache for user_version; KVS only on miss (§3.2)
- Pub/Sub simulated: propagates new version to all gateway L1 caches
- TTL_L1 is intentionally short in production; here simulated as always-fresh
- fail-closed vs fail-soft policy stub for Redis outages (§6)
- Audit log for all invalidation operations
"""

import secrets
import hashlib
import hmac as _hmac
import json
import time
from typing import Optional


# ---------------------------------------------------------------------------
# Token signing
# ---------------------------------------------------------------------------

_SIGNING_SECRET = secrets.token_bytes(32)
_ACCESS_TTL = 300  # 2-5 min per paper


def _make_token(payload: dict) -> str:
    import base64
    body = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()
    sig = _hmac.new(_SIGNING_SECRET, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def _decode_token(token: str) -> Optional[dict]:
    import base64
    try:
        body, sig = token.rsplit(".", 1)
    except ValueError:
        return None
    expected = _hmac.new(_SIGNING_SECRET, body.encode(), hashlib.sha256).hexdigest()
    if not _hmac.compare_digest(expected, sig):
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
    user_version-based session manager with tenant isolation (Run 4).

    Data model (§2.2):
        _kv_user_version[(tenant_id, user_id)]   -> int
        _kv_session[(tenant_id, session_id)]     -> {
            user_id, device_id, refresh_hash, status, expires_at
        }

    L1 gateway cache:
        _l1_version[(tenant_id, user_id)]        -> int
        _l1_revoked_sessions                     -> set of (tenant_id, session_id)

    All key accesses embed tenant_id, enforcing logical isolation across tenants.
    """

    def __init__(self) -> None:
        # KVS: user_version:{tenant_id}:{user_id}
        self._kv_user_version: dict[tuple, int] = {}
        # KVS: session:{tenant_id}:{session_id}
        self._kv_session: dict[tuple, dict] = {}

        # L1 cache: latest known user_version per gateway node
        self._l1_version: dict[tuple, int] = {}
        # L1: per-session revocations broadcast by Pub/Sub
        self._l1_revoked_sessions: set[tuple] = set()

        # Audit log (§6: must persist all invalidation operations)
        self._audit: list[dict] = []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _version_key(self, tenant_id: str, user_id: str) -> tuple:
        return (tenant_id, user_id)

    def _session_key(self, tenant_id: str, session_id: str) -> tuple:
        return (tenant_id, session_id)

    def _get_version(self, tenant_id: str, user_id: str) -> int:
        """L1 hit → return cached; L1 miss → read KVS and populate cache."""
        vk = self._version_key(tenant_id, user_id)
        if vk in self._l1_version:
            return self._l1_version[vk]
        v = self._kv_user_version.get(vk, 0)
        self._l1_version[vk] = v
        return v

    def _pubsub_broadcast_user(self, tenant_id: str, user_id: str, version: int) -> None:
        """Simulate Pub/Sub: update L1 cache on all gateway nodes with new version."""
        self._l1_version[self._version_key(tenant_id, user_id)] = version

    def _pubsub_broadcast_session(self, tenant_id: str, session_id: str) -> None:
        """Simulate Pub/Sub: mark a single session as revoked in all L1 caches."""
        self._l1_revoked_sessions.add(self._session_key(tenant_id, session_id))

    def _log_audit(self, action: str, tenant_id: str, user_id: str, **kwargs) -> None:
        self._audit.append({
            "action": action,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "ts": time.time(),
            **kwargs,
        })

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """Issue an access token for a new device session.

        Token claims (§2.3): tenant_id, user_id, session_id, user_version,
        exp, iat, jti.

        A unique session_id per device allows (tenant, user) to hold
        multiple simultaneous sessions (R1).
        """
        session_id = secrets.token_hex(16)
        jti = secrets.token_hex(8)  # unique token ID per paper's claim set
        now = time.time()
        version = self._get_version(tenant_id, user_id)

        token = _make_token({
            "tenant_id": tenant_id,
            "user_id": user_id,
            "session_id": session_id,
            "user_version": version,
            "exp": now + _ACCESS_TTL,
            "iat": now,
            "jti": jti,
        })

        self._kv_session[self._session_key(tenant_id, session_id)] = {
            "user_id": user_id,
            "device_id": device_id,
            "refresh_hash": None,  # refresh token management out of scope here
            "status": "active",
            "expires_at": now + _ACCESS_TTL,
        }
        return token

    def validate_session(self, token: str) -> Optional[dict]:
        """Validate an access token using the user_version check (§3.2).

        Steps:
        1. Local signature verification.
        2. Local expiry check.
        3. user_version comparison: token.user_version == L1_version(tenant, user).
           If L1 miss, fetch from KVS.
        4. Per-session revocation check (L1 revoked set).
        5. KVS session record status check.

        Returns {"tenant_id", "user_id", "device_id"} or None.
        """
        payload = _decode_token(token)
        if payload is None:
            return None

        if time.time() > payload.get("exp", 0):
            return None

        tid = payload.get("tenant_id")
        uid = payload.get("user_id")
        sid = payload.get("session_id")
        token_version = payload.get("user_version", -1)

        if not all(x is not None for x in [tid, uid, sid]):
            return None

        # Step 3: user_version gate — the single O(1) revocation check (§3.3)
        current_version = self._get_version(tid, uid)
        if token_version != current_version:
            return None

        # Step 4: per-device revocation
        if self._session_key(tid, sid) in self._l1_revoked_sessions:
            return None

        # Step 5: KVS session record
        session = self._kv_session.get(self._session_key(tid, sid))
        if session is None or session.get("status") != "active":
            return None

        return {
            "tenant_id": tid,
            "user_id": uid,
            "device_id": session["device_id"],
        }

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """Invalidate ALL sessions for a user via a single version increment (§3.3).

        Operation sequence:
        1. INCR user_version:{tenant_id}:{user_id}   (atomic KVS update)
        2. Publish revoke_user event via Pub/Sub       (L1 cache broadcast)

        Any token carrying the old user_version will immediately fail the
        version check in validate_session (R2).

        Returns the count of session records deactivated.
        """
        vk = self._version_key(tenant_id, user_id)
        new_version = self._kv_user_version.get(vk, 0) + 1
        self._kv_user_version[vk] = new_version

        # Broadcast via simulated Pub/Sub
        self._pubsub_broadcast_user(tenant_id, user_id, new_version)

        self._log_audit(
            "invalidate_user_sessions",
            tenant_id,
            user_id,
            new_version=new_version,
        )

        count = 0
        for (tid, sid), session in self._kv_session.items():
            if tid == tenant_id and session.get("user_id") == user_id:
                if session.get("status") == "active":
                    session["status"] = "revoked"
                    count += 1
        return count

    def invalidate_session(self, token: str) -> bool:
        """Invalidate a specific device session by token.

        Per-device revocation path (§3.3 second bullet):
        - Mark session:{tenant_id}:{session_id} as revoked in KVS.
        - Broadcast per-session revocation event via Pub/Sub.

        Returns True if the session was found and revoked, False otherwise.
        """
        payload = _decode_token(token)
        if payload is None:
            return False

        tid = payload.get("tenant_id")
        uid = payload.get("user_id")
        sid = payload.get("session_id")
        if not (tid and sid):
            return False

        sk = self._session_key(tid, sid)
        session = self._kv_session.get(sk)
        if session is None or session.get("status") != "active":
            return False

        session["status"] = "revoked"
        self._pubsub_broadcast_session(tid, sid)
        self._log_audit("invalidate_session", tid, uid or "", session_id=sid)
        return True
