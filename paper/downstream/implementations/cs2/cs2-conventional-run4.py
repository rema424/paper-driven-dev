"""
CS2-A-Run4: epoch-based generation counter with per-session state
Design: user epoch (generation) + independent session records

Based on the Run 4 design analysis:
- Redis data model:
    tenant:{tid}:user:{uid}:epoch          -> generation counter (all-session invalidation)
    tenant:{tid}:session:{sid}             -> per-session state
    tenant:{tid}:user:{uid}:sessions       -> sid list
- Token strategy:
    Access Token JWT claims: tid, uid, sid, epoch, jti
    Refresh Token: opaque, rotated, managed in Redis
- Auth flow:
    1. Local JWT signature verification (no I/O)
    2. L1 cache epoch lookup -> Redis fallback
    3. Token epoch == current epoch -> allow; else -> reject
- Invalidation:
    - All sessions: INCR epoch + event dispatch to all nodes
    - Single session: update session record + event dispatch
- Design principles:
    - API nodes fully stateless (no session state resident)
    - All keys prefixed with tenant_id for multi-tenant isolation
    - Audit log (here: in-memory list) for admin operations
"""

import secrets
import threading
import time


class SessionManager:
    """
    Epoch-generation session manager.

    Key namespace (in-memory dicts mirroring the Redis layout):
      _epoch[tenant][uid]           -> int (user epoch; INCR-able)
      _sessions[tenant][sid]        -> {user_id, device_id, epoch, revoked}
      _user_sessions[tenant][uid]   -> list of sids
      _token_index[token]           -> (tenant_id, sid)
      _token_epoch[token]           -> int (epoch captured at token issuance)
      _audit_log                    -> list of audit records
    """

    def __init__(self):
        # tenant:{tid}:user:{uid}:epoch
        self._epoch: dict[str, dict[str, int]] = {}
        # tenant:{tid}:session:{sid}
        self._sessions: dict[str, dict[str, dict]] = {}
        # tenant:{tid}:user:{uid}:sessions -> list[sid]
        self._user_sessions: dict[str, dict[str, list]] = {}
        # reverse lookup: token -> (tenant_id, sid)
        self._token_index: dict[str, tuple[str, str]] = {}
        # token epoch snapshot (analogous to JWT 'epoch' claim)
        self._token_epoch: dict[str, int] = {}
        # audit log (simulates async RDB write from analysis)
        self._audit_log: list[dict] = []
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_epoch(self, tenant_id: str, user_id: str) -> int:
        return self._epoch.get(tenant_id, {}).get(user_id, 0)

    def _incr_epoch(self, tenant_id: str, user_id: str) -> int:
        """Simulate Redis INCR on tenant:{tid}:user:{uid}:epoch."""
        tenant_map = self._epoch.setdefault(tenant_id, {})
        new_epoch = tenant_map.get(user_id, 0) + 1
        tenant_map[user_id] = new_epoch
        return new_epoch

    def _record_audit(self, action: str, tenant_id: str, user_id: str, **kwargs):
        """Append an audit record (non-blocking in real system; sync here for simplicity)."""
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
        Create a new session capturing the current user epoch.
        Each device gets an independent sid stored in tenant:{tid}:session:{sid}.
        Multi-device login is supported naturally (no per-user session cap).
        """
        sid = secrets.token_hex(16)
        token = secrets.token_urlsafe(32)

        with self._lock:
            current_epoch = self._get_epoch(tenant_id, user_id)

            # tenant:{tid}:session:{sid}
            self._sessions.setdefault(tenant_id, {})[sid] = {
                "user_id": user_id,
                "device_id": device_id,
                "epoch": current_epoch,
                "revoked": False,
            }
            # tenant:{tid}:user:{uid}:sessions
            self._user_sessions.setdefault(tenant_id, {}).setdefault(user_id, []).append(sid)
            # reverse index
            self._token_index[token] = (tenant_id, sid)
            self._token_epoch[token] = current_epoch

        return token

    def validate_session(self, token: str) -> dict | None:
        """
        Validate using epoch comparison (from analysis auth flow):
          1. Resolve token to (tenant, sid) [local, no I/O]
          2. Look up current user epoch (L1 cache / Redis fallback -> simulated here)
          3. Token epoch == current epoch -> proceed
          4. Session not individually revoked -> allow
        """
        with self._lock:
            location = self._token_index.get(token)
            if location is None:
                return None

            tenant_id, sid = location
            session = self._sessions.get(tenant_id, {}).get(sid)
            if session is None:
                return None

            # Individual revocation check
            if session["revoked"]:
                return None

            # Epoch comparison: token's embedded epoch vs current user epoch
            token_epoch = self._token_epoch.get(token)
            current_epoch = self._get_epoch(tenant_id, session["user_id"])
            if token_epoch != current_epoch:
                # User epoch has been incremented -> all old tokens rejected
                return None

            return {
                "tenant_id": tenant_id,
                "user_id": session["user_id"],
                "device_id": session["device_id"],
            }

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """
        Bulk invalidation via INCR epoch (from analysis: 管理者の即時無効化).
        Simulates: INCR tenant:{tid}:user:{uid}:epoch + failure event dispatch.
        All outstanding tokens carrying the old epoch will be rejected immediately.
        Also marks per-session records as revoked.
        Writes audit log (simulates async RDB write).
        Returns count of sessions active before invalidation.
        """
        with self._lock:
            new_epoch = self._incr_epoch(tenant_id, user_id)

            sids = self._user_sessions.get(tenant_id, {}).get(user_id, [])
            tenant_sessions = self._sessions.get(tenant_id, {})
            count = 0
            for sid in sids:
                sess = tenant_sessions.get(sid)
                if sess is not None and not sess["revoked"]:
                    sess["revoked"] = True
                    count += 1

            self._record_audit(
                action="invalidate_user",
                tenant_id=tenant_id,
                user_id=user_id,
                new_epoch=new_epoch,
                sessions_revoked=count,
            )

        return count

    def invalidate_session(self, token: str) -> bool:
        """
        Per-session invalidation (from analysis: 単独セッション失効).
        Marks tenant:{tid}:session:{sid}.revoked = True.
        Does NOT increment the user epoch (other sessions remain valid).
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

            was_found = True
            session["revoked"] = True

            self._record_audit(
                action="invalidate_session",
                tenant_id=tenant_id,
                user_id=session["user_id"],
                sid=sid,
            )

        return was_found
