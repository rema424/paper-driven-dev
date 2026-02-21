"""
CS2 条件C: PDD Template — セッション管理 (Run 1)

Design basis: §5 提案手法 — 短寿命アクセストークン + セッション世代 (user_epoch) +
ローカルキャッシュ + 失効イベント配布

Key design decisions from analysis:
- Two-tier revocation model:
    (1) user_epoch: monotonically increasing counter per (tenant, user).
        Incrementing it instantly invalidates ALL sessions for that user.
    (2) session_status: per-session revoked flag for fine-grained single-session invalidation.
- Token carries: tenant_id, user_id, session_id, user_epoch (at issuance time).
- Validation checks: sig (simulated via HMAC), expiry, user_epoch match, session not revoked.
- Local L1 cache (dict) simulates the per-node in-memory cache that avoids external store
  lookups on hot paths. In this single-process implementation, the "store" and "cache" are
  both in-memory dicts, but the design boundary is preserved.
- invalidate_user_sessions increments user_epoch atomically, simulating the event-bus
  propagation to all nodes (all nodes share the same in-memory store here).
- invalidate_session marks a specific session as revoked.

§1.2 Core tension resolved:
  Low latency  <-> Local epoch/status cache avoids external I/O on cache hit.
  Immediate revocation <-> user_epoch increment invalidates all stale tokens.
  Horizontal scale <-> Stateless token; state lives in shared store (simulated here).
  Tenant isolation <-> All keys namespaced by tenant_id.
"""

import secrets
import time
import hashlib
import hmac
import json
import base64
from typing import Optional

# ---------------------------------------------------------------------------
# Internal token format (opaque to caller):
#   base64url(json_header).base64url(json_payload).hex_signature
# Signature: HMAC-SHA256 over "header.payload" using a per-tenant secret.
# This simulates asymmetric JWT signing without external libraries.
# ---------------------------------------------------------------------------

_SIGNING_SECRETS: dict[str, bytes] = {}  # tenant_id -> signing key bytes

def _tenant_secret(tenant_id: str) -> bytes:
    """Return (and lazily create) a per-tenant signing secret."""
    if tenant_id not in _SIGNING_SECRETS:
        _SIGNING_SECRETS[tenant_id] = secrets.token_bytes(32)
    return _SIGNING_SECRETS[tenant_id]


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    if pad != 4:
        s += "=" * pad
    return base64.urlsafe_b64decode(s)


def _sign(tenant_id: str, message: str) -> str:
    secret = _tenant_secret(tenant_id)
    sig = hmac.new(secret, message.encode(), hashlib.sha256).digest()
    return _b64url_encode(sig)


def _issue_token(tenant_id: str, user_id: str, session_id: str,
                 user_epoch: int, ttl: int = 300) -> str:
    """
    Issue a short-lived signed token embedding the user_epoch at issuance time.
    TTL defaults to 300 s (5 min) to minimise revocation window.
    """
    header = _b64url_encode(json.dumps({"alg": "HS256"}).encode())
    payload_data = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "session_id": session_id,
        "user_epoch": user_epoch,
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl,
    }
    payload = _b64url_encode(json.dumps(payload_data).encode())
    sig = _sign(tenant_id, f"{header}.{payload}")
    return f"{header}.{payload}.{sig}"


def _decode_token(token: str) -> Optional[dict]:
    """
    Decode and verify a token. Returns payload dict if signature is valid, else None.
    """
    parts = token.split(".")
    if len(parts) != 3:
        return None
    header_b64, payload_b64, sig_b64 = parts
    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception:
        return None
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        return None
    expected_sig = _sign(tenant_id, f"{header_b64}.{payload_b64}")
    if not hmac.compare_digest(sig_b64, expected_sig):
        return None
    return payload


# ---------------------------------------------------------------------------
# Session truth store (simulates Redis Cluster with tenant-namespaced keys)
#
# §5.1 の「真理値ストア」:
#   _user_epoch[(tenant_id, user_id)]  -> current epoch int
#   _session_store[(tenant_id, session_id)] -> {user_id, device_id, status, exp}
#
# §5.1 の「ローカルL1キャッシュ」(per-node in-memory):
#   In a distributed system these would live in each API node's memory and be
#   invalidated via Pub/Sub events. Here they share the same dict as the store
#   (single process), but the access pattern is preserved.
# ---------------------------------------------------------------------------

class SessionManager:
    """
    Multi-tenant SaaS session manager.

    Design: short-lived token + user_epoch (generation counter) + per-session revocation.
    Ref: CS2-C-Run1 §5 提案手法.
    """

    # Token TTL in seconds (short-lived to minimise revocation exposure window).
    TOKEN_TTL = 300

    def __init__(self) -> None:
        # Truth store: user_epoch per (tenant, user)
        # Key: (tenant_id, user_id) -> int
        self._user_epoch: dict[tuple[str, str], int] = {}

        # Truth store: session records
        # Key: (tenant_id, session_id) -> {user_id, device_id, user_epoch, exp, revoked}
        self._sessions: dict[tuple[str, str], dict] = {}

        # Index: (tenant_id, user_id) -> set of session_ids
        # Needed for efficient invalidate_user_sessions.
        self._user_sessions: dict[tuple[str, str], set[str]] = {}

        # L1 cache: mirrors _user_epoch for hot-path reads (same dict here,
        # but in distributed system this would be a node-local copy).
        self._epoch_cache: dict[tuple[str, str], int] = self._user_epoch

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """
        Create a new session for (tenant_id, user_id, device_id).

        §5.2 Auth Service: 端末ごとに独立した session_id を発行。
        同一ユーザーの複数端末は同時に複数のアクティブセッションを持てる。
        Returns a signed token string embedding the current user_epoch.
        """
        session_id = secrets.token_hex(16)
        user_key = (tenant_id, user_id)
        sess_key = (tenant_id, session_id)

        # Obtain (or initialise) the current user_epoch.
        epoch = self._user_epoch.get(user_key, 0)
        exp = int(time.time()) + self.TOKEN_TTL

        # Persist session record in the truth store.
        self._sessions[sess_key] = {
            "user_id": user_id,
            "device_id": device_id,
            "user_epoch": epoch,
            "exp": exp,
            "revoked": False,
        }

        # Register session under user's session index.
        self._user_sessions.setdefault(user_key, set()).add(session_id)

        # Issue a short-lived token with the epoch embedded.
        token = _issue_token(tenant_id, user_id, session_id, epoch, ttl=self.TOKEN_TTL)
        return token

    def validate_session(self, token: str) -> Optional[dict]:
        """
        Validate a session token.

        §5.2 API Nodes 認証フロー:
          1. JWT署名検証（ローカル）
          2. exp チェック
          3. user_epoch_cache で token.user_epoch >= current_epoch を確認
          4. revoked_session_cache で session_id を確認
        Returns {tenant_id, user_id, device_id} if valid, else None.
        """
        payload = _decode_token(token)
        if payload is None:
            return None

        tenant_id = payload["tenant_id"]
        user_id = payload["user_id"]
        session_id = payload["session_id"]
        token_epoch = payload["user_epoch"]
        exp = payload["exp"]

        # Step 1: expiry check (simulates JWT exp verification).
        if int(time.time()) > exp:
            return None

        # Step 2: user_epoch check (L1 cache lookup — O(1), no external I/O).
        # If the current epoch has advanced beyond the token's epoch, the token
        # was issued before a bulk revocation and must be rejected.
        user_key = (tenant_id, user_id)
        current_epoch = self._epoch_cache.get(user_key, 0)
        if token_epoch < current_epoch:
            return None

        # Step 3: per-session revocation check.
        sess_key = (tenant_id, session_id)
        record = self._sessions.get(sess_key)
        if record is None or record["revoked"]:
            return None

        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "device_id": record["device_id"],
        }

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """
        Invalidate ALL sessions for a user in a tenant.

        §5.2 管理者操作 — ユーザー全セッション無効化:
          user_epoch をインクリメントする（世代更新）。
          これにより、旧世代のトークンは全て epoch チェックで拒否される。
          また、個別 session レコードも revoked フラグを立てて整合させる。

        In a distributed system, this atomic increment would be followed by an
        event bus publication (UserInvalidated event), causing all API nodes to
        update their L1 epoch caches immediately.

        Returns count of sessions that were active at the time of invalidation.
        """
        user_key = (tenant_id, user_id)

        # Atomically increment epoch (simulates Redis INCR).
        new_epoch = self._user_epoch.get(user_key, 0) + 1
        self._user_epoch[user_key] = new_epoch
        # L1 cache is the same dict here; in distributed system, event propagates it.

        # Mark all individual session records as revoked (belt-and-suspenders).
        session_ids = self._user_sessions.get(user_key, set())
        count = 0
        for sid in list(session_ids):
            sess_key = (tenant_id, sid)
            record = self._sessions.get(sess_key)
            if record and not record["revoked"] and int(time.time()) <= record["exp"]:
                record["revoked"] = True
                count += 1

        return count

    def invalidate_session(self, token: str) -> bool:
        """
        Invalidate a specific session identified by the token.

        §5.2 管理者操作 — 特定セッション無効化:
          session_status を revoked へ更新し、イベント配信（ここでは即時dict更新）。
          同一ユーザーの他セッションには影響しない（端末単位の細粒度失効）。

        Returns True if the session existed and was active, False otherwise.
        """
        payload = _decode_token(token)
        if payload is None:
            return False

        tenant_id = payload["tenant_id"]
        session_id = payload["session_id"]
        sess_key = (tenant_id, session_id)

        record = self._sessions.get(sess_key)
        if record is None:
            return False
        if record["revoked"]:
            return False

        record["revoked"] = True
        return True
