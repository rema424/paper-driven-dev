"""
CS2 条件C: PDD Template — マルチテナントSaaSセッション管理 (Run 3)

Design basis: §5 提案手法 — 二層失効モデル + Push/Pull整合 +
短命Access Token + 状態付きRefreshToken

Key design decisions from analysis:

§5.1 基本原理1 — 二層失効モデル:
  (A) session_id 単位失効 (端末単位): `ss:{tenant}:{sid}` の status を revoked に。
  (B) user_epoch 失効 (ユーザー全端末): `ue:{tenant}:{user}` を原子的にインクリメント。
  Both mechanisms can be applied independently; (B) supersedes all (A) for a user.

§5.1 基本原理2 — Push + Pull整合:
  Push: 失効イベントを Pub/Sub で即時配信 → 各ノードの L1 を更新 (simulated).
  Pull: キャッシュ取りこぼし時は Redis 再照会で補正 (simulated by same dict).

§5.1 基本原理3 — 短命Access Token + 状態付きRefresh Token:
  Access Token: short TTL (5 min), carries sid and epoch. Validated locally.
  Refresh Token: opaque, stored server-side, rotated on each use.
  (Refresh lifecycle simulated but not fully exercised in this implementation.)

§5.2 データ構造 (simulated in-memory as dicts):
  ue:{tenant}:{user}  -> user_epoch (int)
  ss:{tenant}:{sid}   -> {status: active|revoked, exp: int, user_id, device_id, epoch}

§4 問題の本質:
  認証判定に必要な状態を最小化 (epoch int + revocation bool) し、
  失効イベントを全ノードへ低遅延伝播する。

§6 検証可能な性質:
  A: 複数端末同時ログイン → 各 sid は独立して active。
  B: ユーザー即時失効 → user_epoch 更新後、旧 epoch トークンは拒否。
  C: 端末単位失効 → 指定 sid のみ revoked。他 sid は影響なし。
  D: 水平スケーリング → ステートレストークン; 状態は共有ストアに。
  E: 低レイテンシ → L1 ヒット時は外部 I/O なし。
"""

import secrets
import time
import hashlib
import hmac
import json
import base64
from typing import Optional


# ---------------------------------------------------------------------------
# Per-tenant signing key store (simulates KMS / JWK endpoint)
# ---------------------------------------------------------------------------

_KEY_STORE: dict[str, bytes] = {}


def _key(tenant_id: str) -> bytes:
    if tenant_id not in _KEY_STORE:
        _KEY_STORE[tenant_id] = secrets.token_bytes(32)
    return _KEY_STORE[tenant_id]


# ---------------------------------------------------------------------------
# Compact signed token (simulates JWT without external library)
# ---------------------------------------------------------------------------

def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _b64u_dec(s: str) -> bytes:
    r = len(s) % 4
    if r:
        s += "=" * (4 - r)
    return base64.urlsafe_b64decode(s)


def _create_access_token(tenant_id: str, user_id: str, sid: str,
                          epoch: int, ttl: int = 300) -> str:
    """
    §5.2 Access Token: JWT-like, carrying tenant_id, user_id, sid, epoch.
    Short TTL (default 300 s) to limit the damage window for revocation latency.
    """
    header = _b64u(b'{"alg":"HS256"}')
    now = int(time.time())
    claims = {
        "t": tenant_id, "u": user_id, "s": sid,
        "e": epoch, "iat": now, "exp": now + ttl,
    }
    payload = _b64u(json.dumps(claims, separators=(",", ":")).encode())
    msg = f"{header}.{payload}"
    sig = hmac.new(_key(tenant_id), msg.encode(), hashlib.sha256).digest()
    return f"{msg}.{_b64u(sig)}"


def _parse_access_token(token: str) -> Optional[dict]:
    """Verify token and return claims dict, or None."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    header, payload_b64, sig_b64 = parts
    try:
        claims = json.loads(_b64u_dec(payload_b64))
    except Exception:
        return None
    tenant_id = claims.get("t")
    if not tenant_id:
        return None
    expected_sig = hmac.new(
        _key(tenant_id), f"{header}.{payload_b64}".encode(), hashlib.sha256
    ).digest()
    if not hmac.compare_digest(_b64u(expected_sig), sig_b64):
        return None
    return claims


# ---------------------------------------------------------------------------
# Session store (simulates Redis Cluster with two key spaces)
#
# ue:{tenant}:{user} -> user_epoch  (int, monotonically increasing)
# ss:{tenant}:{sid}  -> session record dict
# ---------------------------------------------------------------------------


class SessionManager:
    """
    Multi-tenant SaaS session manager.

    Design: two-tier revocation (user_epoch + session_id) with Push+Pull consistency.
    Ref: CS2-C-Run3 §5 提案手法.
    """

    TOKEN_TTL = 300  # 5 minutes (short-lived access token)

    def __init__(self) -> None:
        # ue:{tenant}:{user} -> int   (user_epoch)
        self._ue: dict[str, int] = {}

        # ss:{tenant}:{sid} -> dict   (session record)
        self._ss: dict[str, dict] = {}

        # Index: (tenant_id, user_id) -> set[sid]  (for bulk user invalidation)
        self._uid_to_sids: dict[str, set[str]] = {}

        # L1 cache per API node for user_epoch (Push-updated via simulated event bus).
        # In production: node-local dict, updated by Pub/Sub listener.
        # Here: same reference as _ue (single process).
        self._l1_ue: dict[str, int] = self._ue

    # ------------------------------------------------------------------
    # Key helpers (explicit naming from §5.2)
    # ------------------------------------------------------------------

    @staticmethod
    def _ue_key(tenant_id: str, user_id: str) -> str:
        """ue:{tenant}:{user}"""
        return f"ue:{tenant_id}:{user_id}"

    @staticmethod
    def _ss_key(tenant_id: str, sid: str) -> str:
        """ss:{tenant}:{sid}"""
        return f"ss:{tenant_id}:{sid}"

    @staticmethod
    def _uid_key(tenant_id: str, user_id: str) -> str:
        return f"{tenant_id}:{user_id}"

    def _get_epoch(self, tenant_id: str, user_id: str) -> int:
        return self._ue.get(self._ue_key(tenant_id, user_id), 0)

    def _l1_get_epoch(self, tenant_id: str, user_id: str) -> int:
        """
        Push + Pull整合: Try L1 first (zero I/O).
        On miss, fall back to store (simulated — same dict here).
        """
        key = self._ue_key(tenant_id, user_id)
        return self._l1_ue.get(key, 0)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """
        §5.2 ログイン: 端末ごとに sid を発行し、JWTに tenant_id/user_id/sid/epoch/exp を格納。
        複数端末同時ログインは自然に許容される（sid が端末を識別する）。
        """
        sid = secrets.token_hex(16)
        epoch = self._get_epoch(tenant_id, user_id)
        exp = int(time.time()) + self.TOKEN_TTL

        # ss:{tenant}:{sid} record
        ss_key = self._ss_key(tenant_id, sid)
        self._ss[ss_key] = {
            "user_id": user_id,
            "device_id": device_id,
            "status": "active",   # active | revoked
            "epoch": epoch,       # epoch at issuance (for cross-check)
            "exp": exp,
        }

        # Register sid under user index (for bulk invalidation lookup).
        uid_key = self._uid_key(tenant_id, user_id)
        self._uid_to_sids.setdefault(uid_key, set()).add(sid)

        return _create_access_token(tenant_id, user_id, sid, epoch, self.TOKEN_TTL)

    def validate_session(self, token: str) -> Optional[dict]:
        """
        §5.2 認証（通常経路）:
          1. JWT署名ローカル検証 (no I/O)
          2. exp チェック
          3. L1 で user_epoch 比較 — token.epoch < current_epoch → reject (旧世代)
          4. ss:{tenant}:{sid} の status 確認 — revoked → reject
          5. 全チェック通過 → {tenant_id, user_id, device_id} 返却
        """
        claims = _parse_access_token(token)
        if claims is None:
            return None

        tenant_id = claims["t"]
        user_id = claims["u"]
        sid = claims["s"]
        token_epoch = claims["e"]
        exp = claims["exp"]

        # 1. Expiry.
        if int(time.time()) > exp:
            return None

        # 2. user_epoch check via L1 (Push + Pull; no external I/O on hit).
        current_epoch = self._l1_get_epoch(tenant_id, user_id)
        if token_epoch < current_epoch:
            # Token was issued before the most recent bulk user invalidation.
            return None

        # 3. Per-session status (端末単位失効).
        ss_key = self._ss_key(tenant_id, sid)
        record = self._ss.get(ss_key)
        if record is None or record["status"] != "active":
            return None

        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "device_id": record["device_id"],
        }

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """
        §5.2 管理者失効（ユーザー全体）:
          user_epoch を原子的にインクリメントし、失効イベントを配信。
          各ノードは L1 更新により旧 epoch トークンを即時拒否。

        §6 性質B: 以降の全端末リクエストは旧 epoch として拒否される。
        Push: event published to all nodes (simulated: direct dict update).
        """
        ue_key = self._ue_key(tenant_id, user_id)

        # Atomic increment (simulates Redis INCR).
        new_epoch = self._ue.get(ue_key, 0) + 1
        self._ue[ue_key] = new_epoch
        # Push invalidation event: L1 updated (same dict in single process).

        # Mark individual session records as revoked for belt-and-suspenders
        # consistency (ensures session status also reflects reality).
        uid_key = self._uid_key(tenant_id, user_id)
        sids = self._uid_to_sids.get(uid_key, set())
        count = 0
        now = int(time.time())
        for sid in list(sids):
            ss_key = self._ss_key(tenant_id, sid)
            rec = self._ss.get(ss_key)
            if rec and rec["status"] == "active" and now <= rec["exp"]:
                rec["status"] = "revoked"
                count += 1

        return count

    def invalidate_session(self, token: str) -> bool:
        """
        §5.2 管理者失効（特定端末）:
          該当 sid を revoked へ更新し、同様にイベント配信。
          §6 性質C: 他 sid (端末) は影響しない。

        Returns True if the session existed and was active.
        """
        claims = _parse_access_token(token)
        if claims is None:
            return False

        tenant_id = claims["t"]
        sid = claims["s"]
        ss_key = self._ss_key(tenant_id, sid)

        rec = self._ss.get(ss_key)
        if rec is None or rec["status"] != "active":
            return False

        rec["status"] = "revoked"
        return True
