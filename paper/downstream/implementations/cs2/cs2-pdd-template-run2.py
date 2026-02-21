"""
CS2 条件C: PDD Template — マルチテナントSaaSセッション管理 (Run 2)

Design basis: §5 提案手法 — 二層トークン + revocation_version (単調増加) +
L1キャッシュ + プッシュ無効化 (Pub/Sub)

Key design decisions from analysis:
- §5.1 原則1 二層トークン: short-lived Access Token + rotating Refresh Token.
  Only Access Tokens are validated per-request; Refresh Tokens live in the store.
- §5.1 原則3 版管理失効: per-user `revocation_version` (monotonically increasing int).
  Invalidating a user atomically bumps their version; tokens carrying an older version
  are rejected. This satisfies "即時一括失効" without scanning all sessions.
- §5.1 原則4 プッシュ無効化: invalidation events are "published" to all nodes.
  Simulated here by updating the shared in-memory store (single process).
- §5.1 原則5 フェイルセーフ: on cache miss → fall back to central store; deny-first policy.
- §4 受理条件:
    accept = sig_valid ∧ not_expired ∧ session_active ∧ token_iat > revoked_after(user)
  revoked_after is stored as a Unix timestamp: it is set to now() at invalidation time.
  Any token whose iat < revoked_after is rejected.
- §6 検証可能な性質5: tenant_id=A の操作は tenant_id=B には波及しない。
  Enforced by prefixing all store keys with tenant_id.

§1.2 Core tension:
  Low latency  <-> revocation_version / revoked_after checked from L1 (in-memory dict).
  Immediate revocation <-> bump revocation_version + publish event.
  Horizontal scale <-> stateless token; shared central store (Redis Cluster in prod).
  Tenant isolation <-> all store keys namespaced with tenant_id.
"""

import secrets
import time
import hashlib
import hmac
import json
import base64
from typing import Optional


# ---------------------------------------------------------------------------
# Signing infrastructure (per-tenant HMAC secrets, simulating JWT RS256/ES256)
# ---------------------------------------------------------------------------

_TENANT_SECRETS: dict[str, bytes] = {}


def _get_secret(tenant_id: str) -> bytes:
    if tenant_id not in _TENANT_SECRETS:
        _TENANT_SECRETS[tenant_id] = secrets.token_bytes(32)
    return _TENANT_SECRETS[tenant_id]


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64u_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    if pad != 4:
        s += "=" * pad
    return base64.urlsafe_b64decode(s)


def _make_token(tenant_id: str, user_id: str, session_id: str,
                revocation_version: int, iat: int, ttl: int) -> str:
    """
    Issue a short-lived signed access token.

    Payload carries revocation_version so each API node can compare it against
    the stored version without any external lookup on cache-hit paths.
    """
    header = _b64u(b'{"alg":"HS256","typ":"AT"}')
    payload_dict = {
        "tid": tenant_id,        # tenant_id (abbreviated to tid in token)
        "uid": user_id,
        "sid": session_id,
        "rv": revocation_version,  # revocation_version at issuance
        "iat": iat,
        "exp": iat + ttl,
    }
    payload = _b64u(json.dumps(payload_dict, separators=(",", ":")).encode())
    secret = _get_secret(tenant_id)
    sig = hmac.new(secret, f"{header}.{payload}".encode(), hashlib.sha256).digest()
    return f"{header}.{payload}.{_b64u(sig)}"


def _verify_token(token: str) -> Optional[dict]:
    """Verify signature and return payload dict, or None on failure."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    h, p, s = parts
    try:
        payload = json.loads(_b64u_decode(p))
    except Exception:
        return None
    tenant_id = payload.get("tid")
    if not tenant_id:
        return None
    secret = _get_secret(tenant_id)
    expected = hmac.new(secret, f"{h}.{p}".encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64u(expected), s):
        return None
    return payload


# ---------------------------------------------------------------------------
# Central Session Authority (simulates Redis Cluster + Session Authority service)
#
# §5.2 構成要素:
#   Auth Service  -> handled in create_session
#   Session Authority / Redis Cluster -> _session_store, _user_revocation
#   Event Bus (Pub/Sub) -> simulated: invalidation writes directly to shared dicts
#   Stateless API Nodes with L1 cache -> _l1_revocation_version (same dict, single process)
# ---------------------------------------------------------------------------


class SessionManager:
    """
    Multi-tenant SaaS session manager.

    Design: two-layer token + revocation_version + L1 push invalidation.
    Ref: CS2-C-Run2 §5 提案手法.
    """

    ACCESS_TOKEN_TTL = 300  # 5 minutes — short-lived to limit revocation window

    def __init__(self) -> None:
        # Central store: session records
        # Key: (tenant_id, session_id) -> {user_id, device_id, status, iat}
        self._session_store: dict[tuple[str, str], dict] = {}

        # Central store: per-user revocation_version (monotonically increasing)
        # Key: (tenant_id, user_id) -> int
        # Also represents revoked_after semantics: when bumped, all tokens issued
        # with older rv values are rejected.
        self._user_revocation: dict[tuple[str, str], int] = {}

        # Index: (tenant_id, user_id) -> set of session_ids
        self._user_index: dict[tuple[str, str], set[str]] = {}

        # L1 cache on each API node (same dict in single-process simulation).
        # In production, this is a node-local dict, updated via Pub/Sub events.
        self._l1_revocation_version: dict[tuple[str, str], int] = self._user_revocation

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _current_rv(self, tenant_id: str, user_id: str) -> int:
        """Return current revocation_version for (tenant, user), default 0."""
        return self._user_revocation.get((tenant_id, user_id), 0)

    def _l1_lookup_rv(self, tenant_id: str, user_id: str) -> int:
        """
        L1 cache lookup for revocation_version.

        §5.1 原則4 / §5.2: On cache hit, returns local value immediately (no I/O).
        Cache miss would fall back to central store. Simulated here as same dict.
        """
        return self._l1_revocation_version.get((tenant_id, user_id), 0)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """
        Create a new session (device-scoped).

        §5.2 ログイン時: 端末ごとに独立した session_id を発行し、複数同時ログインを許容。
        Issues a short-lived access token carrying the current revocation_version.
        """
        session_id = secrets.token_hex(16)
        iat = int(time.time())
        rv = self._current_rv(tenant_id, user_id)

        # Persist session in central store.
        sess_key = (tenant_id, session_id)
        self._session_store[sess_key] = {
            "user_id": user_id,
            "device_id": device_id,
            "status": "active",  # active | revoked
            "iat": iat,
        }

        # Register in user index.
        user_key = (tenant_id, user_id)
        self._user_index.setdefault(user_key, set()).add(session_id)

        return _make_token(tenant_id, user_id, session_id, rv, iat, self.ACCESS_TOKEN_TTL)

    def validate_session(self, token: str) -> Optional[dict]:
        """
        Validate an access token.

        §5.2 認証時 (API Node hot path):
          1. 署名をローカル検証 (no I/O)
          2. exp チェック
          3. revocation_version を L1 で確認: token.rv < current_rv → reject
          4. session_id の status を確認: revoked → reject
          5. セッションが存在しない → reject (fail-safe / deny-first)

        §5.1 受理条件:
          accept = sig_valid ∧ not_expired ∧ session_active ∧ token_rv >= current_rv
        """
        payload = _verify_token(token)
        if payload is None:
            return None

        tenant_id = payload["tid"]
        user_id = payload["uid"]
        session_id = payload["sid"]
        token_rv = payload["rv"]
        exp = payload["exp"]

        # 1. Expiry.
        if int(time.time()) > exp:
            return None

        # 2. Revocation version check (L1 lookup — O(1), zero I/O on hit).
        current_rv = self._l1_lookup_rv(tenant_id, user_id)
        if token_rv < current_rv:
            return None

        # 3. Per-session status check (fine-grained single-session revocation).
        sess_key = (tenant_id, session_id)
        record = self._session_store.get(sess_key)
        if record is None or record["status"] != "active":
            return None

        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "device_id": record["device_id"],
        }

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """
        Invalidate ALL sessions for a user in a tenant.

        §5.2 管理者失効時:
          1. revocation_version を原子的にインクリメント (+1)
          2. 全セッションレコードを revoked に更新
          3. イベント配信 (Pub/Sub) — シミュレーション: 即時 L1 更新

        §6 性質2: 全端末の次回リクエストが反映 SLA 以内に 401 となる。
        §6 性質5: tenant_id=B のセッション状態には影響しない。

        Returns count of sessions that were active.
        """
        user_key = (tenant_id, user_id)

        # Atomic increment of revocation_version.
        new_rv = self._user_revocation.get(user_key, 0) + 1
        self._user_revocation[user_key] = new_rv
        # Event bus publication simulated: L1 cache updated immediately
        # (same dict in single-process; in prod, Pub/Sub triggers node-local update).

        # Mark all per-session records as revoked.
        session_ids = self._user_index.get(user_key, set())
        count = 0
        for sid in list(session_ids):
            sess_key = (tenant_id, sid)
            rec = self._session_store.get(sess_key)
            if rec and rec["status"] == "active":
                rec["status"] = "revoked"
                count += 1

        return count

    def invalidate_session(self, token: str) -> bool:
        """
        Invalidate a single session identified by token.

        §5.2 特定セッション失効: session_id を revoked へ更新し、イベント配信。
        同一ユーザーの他セッションは影響しない (端末単位失効)。

        Returns True if session existed and was active, False otherwise.
        """
        payload = _verify_token(token)
        if payload is None:
            return False

        tenant_id = payload["tid"]
        session_id = payload["sid"]
        sess_key = (tenant_id, session_id)

        rec = self._session_store.get(sess_key)
        if rec is None or rec["status"] != "active":
            return False

        rec["status"] = "revoked"
        return True
