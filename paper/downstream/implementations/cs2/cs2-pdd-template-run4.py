"""
CS2 条件C: PDD Template — マルチテナントSaaSセッション管理 (Run 4)

Design basis: §5 提案手法 — データプレーン / 制御プレーン分離 +
user_epoch (単調増加) + revoked_sid セット + L1 キャッシュ + 無効化バス

Key design decisions from analysis:

§4 問題の本質:
  「認証データプレーンの局所高速判定」と「失効制御プレーンの全体一貫性」を両立する
  分散整合問題。特に「ユーザー単位の即時失効」と「端末単位の同時セッション維持」を
  同時に満たす状態モデルが核となる。

§5.1 有効条件 (exact formula from analysis):
  valid = sig_ok ∧ not_expired ∧ token.user_epoch == current_user_epoch(tenant,user)
          ∧ sid_not_revoked

  Note: the analysis uses `==` (exact match), not `>=`. This is a stricter check:
  the token's epoch must exactly match the stored epoch. If the stored epoch has been
  incremented (user invalidated), the comparison fails.

§5.2 実装アーキテクチャ (5 components):
  1. Auth Service        → create_session
  2. Session Control Store (Redis Cluster: user_epoch + revoked_sid set)
                         → _epoch_store + _revoked_sids
  3. System of Record (RDB: session history) → _session_history (audit log)
  4. Invalidation Bus (Pub/Sub or Stream)    → simulated by direct dict updates
  5. API Node L1 Cache (hot user epoch)      → _l1_epoch (same dict, single process)

§6 検証可能な性質:
  1. 同時ログイン性: 異なる session_id が2件 Active → both auth succeed.
  2. ユーザー単位即時失効: user_epoch 更新 → 旧 epoch トークンは全ノードで拒否.
  3. 端末単位失効の選択性: sid A revoked, sid B 継続.
  4. 水平スケール不変性: stateless token; state in shared store.
  5. 低遅延性: L1 hit → zero external I/O.
  6. テナント分離性: T1 操作は T2 に波及しない.

§7 注: 厳密な「瞬時」ではなく「運用上即時（サブ秒SLO）」を目標とする現実解。
"""

import secrets
import time
import hashlib
import hmac
import json
import base64
from typing import Optional


# ---------------------------------------------------------------------------
# Per-tenant signing keys (simulates KMS / JWK distribution)
# ---------------------------------------------------------------------------

_KEYS: dict[str, bytes] = {}


def _signing_key(tenant_id: str) -> bytes:
    if tenant_id not in _KEYS:
        _KEYS[tenant_id] = secrets.token_bytes(32)
    return _KEYS[tenant_id]


# ---------------------------------------------------------------------------
# Token utilities (compact signed token, simulates JWT HS256)
# ---------------------------------------------------------------------------

def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64u_decode(s: str) -> bytes:
    r = len(s) % 4
    if r:
        s += "=" * (4 - r)
    return base64.urlsafe_b64decode(s)


def _build_token(tenant_id: str, user_id: str, session_id: str,
                 device_id: str, user_epoch: int, ttl: int = 300) -> str:
    """
    Issue a short-lived access token.

    §5.1: アクセストークンは短寿命署名 JWT。
    Carries: tenant_id, user_id, session_id, device_id, user_epoch, iat, exp.
    The user_epoch embedded in the token must exactly match the stored epoch
    at validation time (§5.1 valid condition: token.user_epoch == current_user_epoch).
    """
    header = _b64u(b'{"alg":"HS256","typ":"AT+JWT"}')
    now = int(time.time())
    claims = {
        "ten": tenant_id,
        "usr": user_id,
        "sid": session_id,
        "dev": device_id,
        "epo": user_epoch,
        "iat": now,
        "exp": now + ttl,
    }
    payload = _b64u(json.dumps(claims, separators=(",", ":")).encode())
    msg = f"{header}.{payload}"
    sig = hmac.new(_signing_key(tenant_id), msg.encode(), hashlib.sha256).digest()
    return f"{msg}.{_b64u(sig)}"


def _read_token(token: str) -> Optional[dict]:
    """
    Verify signature and return claims, or None.
    Tenant key is looked up from claims['ten'].
    """
    parts = token.split(".")
    if len(parts) != 3:
        return None
    header, payload_b64, sig_b64 = parts
    try:
        claims = json.loads(_b64u_decode(payload_b64))
    except Exception:
        return None
    tenant_id = claims.get("ten")
    if not tenant_id:
        return None
    key = _signing_key(tenant_id)
    expected = _b64u(hmac.new(key, f"{header}.{payload_b64}".encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(expected, sig_b64):
        return None
    return claims


# ---------------------------------------------------------------------------
# Session Control Store + System of Record (in-memory simulation)
#
# Redis Cluster data structures (§5.2):
#   user_epoch store: (tenant_id, user_id) -> int
#   revoked_sid set:  (tenant_id) -> set[sid]    (fine-grained per-session revocation)
#
# System of Record (RDB):
#   session_history: (tenant_id, session_id) -> {user_id, device_id, created_at}
# ---------------------------------------------------------------------------


class SessionManager:
    """
    Multi-tenant SaaS session manager.

    Design: data plane / control plane separation + user_epoch + revoked_sid set.
    Ref: CS2-C-Run4 §5 提案手法.

    Valid condition (exact, from §5.1):
      valid = sig_ok ∧ not_expired
              ∧ token.user_epoch == current_user_epoch(tenant, user)
              ∧ sid_not_revoked
    """

    TOKEN_TTL = 300  # seconds; short-lived to bound revocation latency

    def __init__(self) -> None:
        # Control plane: user_epoch per (tenant, user)
        # Key: (tenant_id, user_id) -> int
        self._epoch_store: dict[tuple[str, str], int] = {}

        # Control plane: revoked session IDs per tenant
        # Key: tenant_id -> set[session_id]
        self._revoked_sids: dict[str, set[str]] = {}

        # System of Record: session metadata (audit / device lookup)
        # Key: (tenant_id, session_id) -> {user_id, device_id, user_epoch, created_at}
        self._session_history: dict[tuple[str, str], dict] = {}

        # User -> sessions index (for bulk user invalidation)
        # Key: (tenant_id, user_id) -> set[session_id]
        self._user_sessions: dict[tuple[str, str], set[str]] = {}

        # API Node L1 Cache: hot user epochs (simulated as same dict; in prod, node-local)
        # §5.2: Invalidation Bus propagates epoch updates to each node's L1.
        self._l1_epoch: dict[tuple[str, str], int] = self._epoch_store

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_epoch(self, tenant_id: str, user_id: str) -> int:
        return self._epoch_store.get((tenant_id, user_id), 0)

    def _l1_get_epoch(self, tenant_id: str, user_id: str) -> int:
        """
        Data plane hot path: read epoch from L1 cache.
        §5.2: ホットユーザーの user_epoch を保持し、認証遅延を最小化。
        """
        return self._l1_epoch.get((tenant_id, user_id), 0)

    def _is_sid_revoked(self, tenant_id: str, session_id: str) -> bool:
        """Check revoked_sid set (O(1) in-memory lookup)."""
        return session_id in self._revoked_sids.get(tenant_id, set())

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """
        §5.2 Auth Service: ログイン時に session_id 発行。
        tenant_id / user_id / device_id / user_epoch を記録。

        Different devices for the same user get different session_ids,
        enabling simultaneous multi-device login.
        """
        session_id = secrets.token_hex(16)
        user_epoch = self._get_epoch(tenant_id, user_id)
        now = int(time.time())

        # Persist to System of Record.
        sess_key = (tenant_id, session_id)
        self._session_history[sess_key] = {
            "user_id": user_id,
            "device_id": device_id,
            "user_epoch": user_epoch,
            "created_at": now,
        }

        # Register under user index.
        user_key = (tenant_id, user_id)
        self._user_sessions.setdefault(user_key, set()).add(session_id)

        return _build_token(tenant_id, user_id, session_id, device_id,
                            user_epoch, self.TOKEN_TTL)

    def validate_session(self, token: str) -> Optional[dict]:
        """
        §5.1 有効条件（データプレーン — ローカル高速判定）:
          valid = sig_ok ∧ not_expired
                  ∧ token.user_epoch == current_user_epoch(tenant, user)
                  ∧ sid_not_revoked

        All checks use L1 cache / local memory; no external I/O on hot path.
        §6 性質5 低遅延性: L1 hit → p99 遅延は目標値を満たす.
        """
        claims = _read_token(token)
        if claims is None:
            return None

        tenant_id = claims["ten"]
        user_id = claims["usr"]
        session_id = claims["sid"]
        token_epoch = claims["epo"]
        exp = claims["exp"]

        # 1. Expiry check.
        if int(time.time()) > exp:
            return None

        # 2. user_epoch exact match (control plane check via L1).
        # §5.1: token.user_epoch == current_user_epoch(tenant, user)
        # If current epoch has been incremented (user invalidated), mismatch → reject.
        current_epoch = self._l1_get_epoch(tenant_id, user_id)
        if token_epoch != current_epoch:
            return None

        # 3. Per-session revocation check (fine-grained, endpoint-level).
        if self._is_sid_revoked(tenant_id, session_id):
            return None

        # Retrieve device_id from System of Record.
        sess_key = (tenant_id, session_id)
        record = self._session_history.get(sess_key)
        if record is None:
            return None

        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "device_id": record["device_id"],
        }

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """
        §5.2 管理者失効フロー (ユーザー単位):
          1. user_epoch を原子的にインクリメント
          2. 無効化バス経由で全 API ノードへイベント配信
             (simulated: L1 cache = same dict → immediate propagation)
          3. 以後、旧 epoch トークンは token.user_epoch != current_epoch で拒否

        §6 性質2: 全ノードで SLO 内に旧 epoch トークンが拒否される.
        §6 性質6: テナント分離 — T1 操作は T2 に波及しない.

        Returns count of sessions that were active (not already in revoked set).
        """
        user_key = (tenant_id, user_id)

        # Atomic epoch increment (simulates Redis INCR).
        new_epoch = self._epoch_store.get(user_key, 0) + 1
        self._epoch_store[user_key] = new_epoch
        # Invalidation Bus event published: L1 updated immediately (same dict).

        # Add all user's session_ids to the revoked_sid set.
        session_ids = self._user_sessions.get(user_key, set())
        revoked_set = self._revoked_sids.setdefault(tenant_id, set())
        count = 0
        for sid in list(session_ids):
            if sid not in revoked_set:
                revoked_set.add(sid)
                count += 1

        return count

    def invalidate_session(self, token: str) -> bool:
        """
        §5.2 端末単位失効:
          Specific session_id added to revoked_sid set and event published.
          §6 性質3: 他 sid は継続利用できる (selective revocation).

        Returns True if the session existed and was not already revoked.
        """
        claims = _read_token(token)
        if claims is None:
            return False

        tenant_id = claims["ten"]
        session_id = claims["sid"]

        # Verify session exists in the System of Record.
        sess_key = (tenant_id, session_id)
        if sess_key not in self._session_history:
            return False

        revoked_set = self._revoked_sids.setdefault(tenant_id, set())
        if session_id in revoked_set:
            return False

        revoked_set.add(session_id)
        return True
