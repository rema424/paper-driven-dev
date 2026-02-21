"""
CS2-A-Run3: user_ver version matching in token claims vs store
Design: Access token embeds user_ver; validation compares against current store value

Based on the Run 3 design analysis:
- Data model:
    sess:{tenant_id}:{sid}          -> user_id, device_id, status(active/revoked), expires_at
    user_sess:{tenant_id}:{user_id} -> set of sids
    user_ver:{tenant_id}:{user_id}  -> forced-revocation version number
- Access token claims: tenant_id, user_id, sid, user_ver, exp
- Authentication flow:
    1. Verify JWT signature + expiry locally (no I/O)
    2. Check sid status in local cache (Redis fallback on miss)
    3. Verify token's user_ver matches current user_ver -> allow
- Invalidation:
    - All devices: INCR user_ver + event broadcast
    - Single device: mark sid as revoked + event broadcast

The version mismatch is the primary guard for bulk invalidation.
Per-session status field provides granular control.
"""

import secrets
import threading


# Status constants matching the analysis's active/revoked enumeration
_STATUS_ACTIVE = "active"
_STATUS_REVOKED = "revoked"


class SessionManager:
    """
    Session manager with embedded user_ver claim and per-session status field.

    Storage mirrors the analysis's three key namespaces:
      _sess[tenant][sid]            -> {user_id, device_id, status}
      _user_sess[tenant][uid]       -> set of sids
      _user_ver[tenant][uid]        -> int (version counter)
      _token_index[token]           -> (tenant_id, sid)
      _token_user_ver[token]        -> int (user_ver embedded at issuance)
    """

    def __init__(self):
        # sess:{tenant_id}:{sid}
        self._sess: dict[str, dict[str, dict]] = {}
        # user_sess:{tenant_id}:{user_id} -> set of sids
        self._user_sess: dict[str, dict[str, set]] = {}
        # user_ver:{tenant_id}:{user_id} -> int
        self._user_ver: dict[str, dict[str, int]] = {}
        # token -> (tenant_id, sid)
        self._token_index: dict[str, tuple[str, str]] = {}
        # token -> user_ver at issuance (embedded claim)
        self._token_user_ver: dict[str, int] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _current_user_ver(self, tenant_id: str, user_id: str) -> int:
        """Return current user_ver; defaults to 0."""
        return self._user_ver.get(tenant_id, {}).get(user_id, 0)

    def _increment_user_ver(self, tenant_id: str, user_id: str) -> int:
        """INCR user_ver:{tenant_id}:{user_id} and return new value."""
        tenant_map = self._user_ver.setdefault(tenant_id, {})
        new_ver = tenant_map.get(user_id, 0) + 1
        tenant_map[user_id] = new_ver
        return new_ver

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """
        Create a new session, embedding the current user_ver into the token.
        Each device gets an independent sid (supports concurrent multi-device login).
        """
        sid = secrets.token_hex(16)
        token = secrets.token_urlsafe(32)

        with self._lock:
            ver = self._current_user_ver(tenant_id, user_id)

            # sess:{tenant_id}:{sid}
            self._sess.setdefault(tenant_id, {})[sid] = {
                "user_id": user_id,
                "device_id": device_id,
                "status": _STATUS_ACTIVE,
            }
            # user_sess:{tenant_id}:{user_id}
            self._user_sess.setdefault(tenant_id, {}).setdefault(user_id, set()).add(sid)
            # token reverse index + embedded claim
            self._token_index[token] = (tenant_id, sid)
            self._token_user_ver[token] = ver

        return token

    def validate_session(self, token: str) -> dict | None:
        """
        Validate token using three-step check (from analysis):
          Step 1: Resolve token (local operation, no I/O)
          Step 2: Check sid status (active/revoked)
          Step 3: Compare embedded user_ver with current user_ver
                  -> mismatch means bulk invalidation has occurred

        All checks use in-memory state (simulating local cache hits).
        """
        with self._lock:
            location = self._token_index.get(token)
            if location is None:
                return None

            tenant_id, sid = location
            session = self._sess.get(tenant_id, {}).get(sid)
            if session is None:
                return None

            # Step 2: per-session status check
            if session["status"] != _STATUS_ACTIVE:
                return None

            # Step 3: user_ver comparison
            token_ver = self._token_user_ver.get(token)
            current_ver = self._current_user_ver(tenant_id, session["user_id"])
            if token_ver != current_ver:
                # user_ver has been incremented since token was issued -> reject
                return None

            return {
                "tenant_id": tenant_id,
                "user_id": session["user_id"],
                "device_id": session["device_id"],
            }

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """
        All-device invalidation via INCR user_ver (from analysis: ユーザー全端末無効化).
        All tokens holding the old ver will fail step 3 on next validation.
        Also marks per-session status as revoked.
        Returns count of sessions that were active at the time of the call.
        """
        with self._lock:
            # INCR user_ver:{tenant_id}:{user_id}
            self._increment_user_ver(tenant_id, user_id)

            sids = self._user_sess.get(tenant_id, {}).get(user_id, set())
            tenant_sess = self._sess.get(tenant_id, {})
            count = 0
            for sid in sids:
                sess = tenant_sess.get(sid)
                if sess is not None and sess["status"] == _STATUS_ACTIVE:
                    sess["status"] = _STATUS_REVOKED
                    count += 1

        return count

    def invalidate_session(self, token: str) -> bool:
        """
        Single-device invalidation (from analysis: 特定端末のみ無効化).
        Marks the target sid as revoked without touching user_ver.
        Returns True if the token was found in the index.
        """
        with self._lock:
            location = self._token_index.get(token)
            if location is None:
                return False

            tenant_id, sid = location
            session = self._sess.get(tenant_id, {}).get(sid)
            if session is None:
                return False

            session["status"] = _STATUS_REVOKED
            return True
