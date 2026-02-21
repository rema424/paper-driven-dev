"""
CS2 条件C: PDD Template — マルチテナントSaaSセッション管理 (Run 5)

Design basis: §5 提案手法 — Epochベースのハイブリッド方式

Key design decisions from analysis:

§5.1 Epochベースのハイブリッド方式 (5 principles):
  1. アクセストークンは短 TTL (3〜5分) の署名付きトークン。
  2. ユーザー単位で `revoked_after` (失効 Epoch = Unix timestamp) を保持。
     任意の token で `iat < revoked_after` であれば拒否。
  3. API ノードは通常、署名検証 + ローカルキャッシュの Epoch 比較で判定。
  4. 管理者失効時は `revoked_after` を更新し、イベント配信で全ノードへ即時反映。
  5. 端末ごとに独立 session_id を持たせ、複数端末同時ログインを自然に許容。

§5.2 実装アーキテクチャ:
  - Auth Service: トークン発行、Refresh ローテーション。
  - Session Store (Redis + 永続 DB): セッション・失効 Epoch の保存。
  - Event Bus: `invalidate-user(tenant_id, user_id, epoch)` を配信。
  - API Node Local Cache: `user_epoch` をメモリ保持し高速判定。

§5.2 認証フロー:
  1. トークン署名/有効期限をローカル検証。
  2. tenant_id, user_id, iat を抽出。
  3. ローカル `revoked_after` と比較し、iat < revoked_after なら拒否。
  4. キャッシュミス時のみ Redis 参照し、結果を短 TTL で再キャッシュ。

§5.2 失効フロー:
  1. 管理者操作で `revoked_after` 更新（原子的; 現在時刻を設定）。
  2. 更新イベントを全ノードへ配信 (simulated: direct dict update).
  3. 各ノードがローカルキャッシュ即時更新。
  4. 以降、当該ユーザーの既存トークンは即時拒否。

§6 検証可能な性質:
  1. 複数端末同時ログイン → 両セッション独立して成功。
  2. ユーザー失効 → 伝播完了後、Uの既存トークンは全拒否。
  3. スケールアウト → stateless token; stickiness 不要。
  4. L1 hit → p99 遅延は低値。
  5. tenantA 操作 → tenantB は影響なし。

§4 問題の本質:
  「ローカル高速判定」と「グローバル失効一貫性」を同時に満たすこと。
  認証判定は `暗号学的正当性` に加えて `最新失効状態 (revoked_after)` を、
  許容遅延内で参照できる設計が必要。
"""

import secrets
import time
import hashlib
import hmac
import json
import base64
from typing import Optional


# ---------------------------------------------------------------------------
# Per-tenant signing keys
# ---------------------------------------------------------------------------

_SECRETS: dict[str, bytes] = {}


def _secret(tenant_id: str) -> bytes:
    if tenant_id not in _SECRETS:
        _SECRETS[tenant_id] = secrets.token_bytes(32)
    return _SECRETS[tenant_id]


# ---------------------------------------------------------------------------
# Signed token (simulates JWT HS256 without external dependencies)
# ---------------------------------------------------------------------------

def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64u_dec(s: str) -> bytes:
    r = len(s) % 4
    if r:
        s += "=" * (4 - r)
    return base64.urlsafe_b64decode(s)


def _issue(tenant_id: str, user_id: str, session_id: str,
           device_id: str, ttl: int = 300) -> str:
    """
    Issue a short-lived signed access token.

    §5.1 原則1: アクセストークンは短 TTL (3〜5分).
    §5.2 認証フロー 手順2: iat を埋め込む — 失効判定は `iat < revoked_after` で行う.

    Embedding iat allows the `revoked_after` timestamp-based rejection:
    any token issued before the revocation moment is rejected.
    """
    header = _b64u(b'{"alg":"HS256"}')
    now = int(time.time())
    payload_dict = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "session_id": session_id,
        "device_id": device_id,
        "iat": now,
        "exp": now + ttl,
    }
    payload = _b64u(json.dumps(payload_dict, separators=(",", ":")).encode())
    msg = f"{header}.{payload}"
    sig = hmac.new(_secret(tenant_id), msg.encode(), hashlib.sha256).digest()
    return f"{msg}.{_b64u(sig)}"


def _parse(token: str) -> Optional[dict]:
    """Verify and parse token, returning payload dict or None."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    header, payload_b64, sig_b64 = parts
    try:
        payload = json.loads(_b64u_dec(payload_b64))
    except Exception:
        return None
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        return None
    expected = _b64u(
        hmac.new(_secret(tenant_id), f"{header}.{payload_b64}".encode(),
                 hashlib.sha256).digest()
    )
    if not hmac.compare_digest(expected, sig_b64):
        return None
    return payload


# ---------------------------------------------------------------------------
# Session Store + API Node Local Cache
#
# §5.2 Session Store (Redis + 永続 DB), simulated as in-memory dicts:
#
#   _revoked_after[(tenant_id, user_id)] = Unix timestamp (float)
#       Any token with iat < this value is rejected.
#       Updated atomically on user-level invalidation.
#
#   _sessions[(tenant_id, session_id)] = {user_id, device_id, iat, revoked: bool}
#       Provides device_id lookup and per-session revocation flag.
#
# §5.2 API Node Local Cache:
#   _l1_revoked_after — node-local copy of _revoked_after, updated via Event Bus.
#   In single-process simulation: same dict reference.
# ---------------------------------------------------------------------------


class SessionManager:
    """
    Multi-tenant SaaS session manager.

    Design: Epoch-based hybrid — `revoked_after` timestamp + per-session flag.
    Ref: CS2-C-Run5 §5 提案手法.

    Revocation logic (§5.2 認証フロー 手順3):
      if token.iat < revoked_after(tenant, user): reject
    """

    TOKEN_TTL = 300  # 5 minutes (§5.1: short TTL)

    def __init__(self) -> None:
        # Session Store: revoked_after timestamps (user-level invalidation)
        # Key: (tenant_id, user_id) -> float (Unix timestamp)
        # Semantics: tokens with iat < this value are rejected.
        self._revoked_after: dict[tuple[str, str], float] = {}

        # Session Store: individual session records
        # Key: (tenant_id, session_id) -> {user_id, device_id, iat, revoked}
        self._sessions: dict[tuple[str, str], dict] = {}

        # Index: (tenant_id, user_id) -> set[session_id] (for bulk invalidation)
        self._user_sids: dict[tuple[str, str], set[str]] = {}

        # API Node Local Cache: revoked_after (Event Bus updates this on invalidation).
        # §5.2: キャッシュミス時のみ Redis 参照; ヒット時は外部 I/O なし.
        # In single-process simulation: same dict reference.
        self._l1_revoked_after: dict[tuple[str, str], float] = self._revoked_after

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_revoked_after(self, tenant_id: str, user_id: str) -> float:
        """
        §5.2 認証フロー 手順3 + 4:
        Try L1 first (no I/O). On miss, fall back to store (same dict here).
        Returns 0.0 if no revocation has occurred (all tokens valid by default).
        """
        return self._l1_revoked_after.get((tenant_id, user_id), 0.0)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """
        §5.2 Auth Service: トークン発行。

        §5.1 原則5: 端末ごとに独立 session_id — 複数端末同時ログインを自然に許容。
        §6 性質1: tenantA/userX と tenantB/userX は独立して管理される。
        """
        session_id = secrets.token_hex(16)
        now = int(time.time())

        # Persist session record.
        sess_key = (tenant_id, session_id)
        self._sessions[sess_key] = {
            "user_id": user_id,
            "device_id": device_id,
            "iat": now,
            "revoked": False,
        }

        # Register under user index.
        user_key = (tenant_id, user_id)
        self._user_sids.setdefault(user_key, set()).add(session_id)

        return _issue(tenant_id, user_id, session_id, device_id, self.TOKEN_TTL)

    def validate_session(self, token: str) -> Optional[dict]:
        """
        §5.2 認証フロー (API Node — ローカル高速判定):
          1. トークン署名/有効期限をローカル検証 (no I/O).
          2. tenant_id, user_id, iat を抽出。
          3. ローカル revoked_after と比較: iat < revoked_after → 拒否。
          4. session_id の per-session revoked フラグを確認。

        §6 性質4: L1 hit → p99 遅延は低値（外部 I/O なし）.
        §6 性質5: tenantA/userX の失効は tenantB/userX に影響しない。
        """
        payload = _parse(token)
        if payload is None:
            return None

        tenant_id = payload["tenant_id"]
        user_id = payload["user_id"]
        session_id = payload["session_id"]
        iat = payload["iat"]
        exp = payload["exp"]

        # 1. Expiry.
        if int(time.time()) > exp:
            return None

        # 2. Epoch-based revocation: iat < revoked_after → token was issued before
        #    the most recent bulk revocation → reject.
        # §5.2 認証フロー 手順3.
        revoked_after = self._get_revoked_after(tenant_id, user_id)
        if iat < revoked_after:
            return None

        # 3. Per-session (device-level) revocation check.
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
        §5.2 失効フロー (ユーザー全体):
          1. revoked_after を現在時刻に原子的更新。
             以降、当該ユーザーの既存トークン (iat < now) は全て拒否される。
          2. Event Bus でイベント配信: invalidate-user(tenant_id, user_id, epoch)
             (simulated: L1 cache same dict → immediate update on all "nodes").
          3. 各ノードがローカルキャッシュ即時更新。

        §6 性質2: 伝播完了後、U の既存トークンは全ノードで拒否される.

        Returns count of sessions that were active at the time of invalidation.
        """
        user_key = (tenant_id, user_id)

        # Atomic update: set revoked_after to current time.
        # Any existing token has iat <= now, so all are rejected.
        # Tiny buffer (+1e-6) ensures iat < revoked_after even if issued this exact second.
        now = time.time() + 1e-6
        self._revoked_after[user_key] = now
        # Event bus: "invalidate-user" event published.
        # L1 updated (same dict in single-process simulation).

        # Mark individual session records as revoked for consistency.
        sids = self._user_sids.get(user_key, set())
        count = 0
        for sid in list(sids):
            sess_key = (tenant_id, sid)
            rec = self._sessions.get(sess_key)
            if rec and not rec["revoked"]:
                rec["revoked"] = True
                count += 1

        return count

    def invalidate_session(self, token: str) -> bool:
        """
        §5.1 原則5 / §5.2: 端末単位の独立セッション無効化。

        Sets the per-session `revoked` flag. Does not affect other sessions
        for the same user (§6 性質1 の逆: 選択的端末ログアウト).

        Returns True if session existed and was not already revoked.
        """
        payload = _parse(token)
        if payload is None:
            return False

        tenant_id = payload["tenant_id"]
        session_id = payload["session_id"]
        sess_key = (tenant_id, session_id)

        record = self._sessions.get(sess_key)
        if record is None or record["revoked"]:
            return False

        record["revoked"] = True
        return True
