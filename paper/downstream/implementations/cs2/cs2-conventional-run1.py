"""
CS2-A-Run1: Hybrid JWT-style session management
Design: Short-lived access token + revocation timestamps

Based on the Run 1 design analysis:
- Hybrid: JWT-like token with iat-based revocation checking
- Revocation stored both at session level (sess:{tenant}:{sid}) and
  user level (user_rev:{tenant}:{uid}) for bulk invalidation
- User-session index (user_sess:{tenant}:{uid}) for enumeration
- Local validation uses iat comparison against revoked_at timestamps
- No external DB: all state is in-memory dicts simulating Redis

Revocation check logic (from analysis):
  - token.iat <= user_revoked_at  -> rejected (bulk user revocation)
  - token.iat <= session_revoked_at -> rejected (per-session revocation)
"""

import secrets
import time
import threading


class SessionManager:
    """
    Hybrid session manager using opaque tokens with server-side state.

    Storage layout mirrors the analysis's Redis key structure:
      _sessions[tenant][sid]      -> {user_id, device_id, created_at, revoked_at}
      _user_revoked_at[tenant][uid] -> float timestamp (epoch seconds)
      _user_sessions[tenant][uid] -> set of active session ids
      _token_index[token]         -> (tenant_id, sid)  -- reverse lookup
    """

    def __init__(self):
        # sess:{tenant}:{sid}
        self._sessions: dict[str, dict[str, dict]] = {}
        # user_rev:{tenant}:{uid} -> revoked_at timestamp
        self._user_revoked_at: dict[str, dict[str, float]] = {}
        # user_sess:{tenant}:{uid} -> set of sids
        self._user_sessions: dict[str, dict[str, set]] = {}
        # token -> (tenant_id, sid)  opaque token reverse index
        self._token_index: dict[str, tuple[str, str]] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _tenant_sessions(self, tenant_id: str) -> dict:
        return self._sessions.setdefault(tenant_id, {})

    def _tenant_user_revoked(self, tenant_id: str) -> dict:
        return self._user_revoked_at.setdefault(tenant_id, {})

    def _tenant_user_sessions(self, tenant_id: str) -> dict:
        return self._user_sessions.setdefault(tenant_id, {})

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """
        Create a new session for (tenant, user, device).
        Returns an opaque token that encodes tenant+session identity.
        Each call creates an independent session (multiple devices supported).
        """
        sid = secrets.token_hex(16)
        token = secrets.token_urlsafe(32)
        created_at = time.time()

        with self._lock:
            # sess:{tenant}:{sid}
            self._tenant_sessions(tenant_id)[sid] = {
                "user_id": user_id,
                "device_id": device_id,
                "created_at": created_at,
                "revoked_at": None,
            }
            # user_sess:{tenant}:{uid}
            user_sids = self._tenant_user_sessions(tenant_id).setdefault(user_id, set())
            user_sids.add(sid)
            # reverse index: token -> (tenant, sid)
            self._token_index[token] = (tenant_id, sid)

        return token

    def validate_session(self, token: str) -> dict | None:
        """
        Validate a session token using iat-based revocation checks.

        Validation steps (from analysis):
          1. Resolve token to (tenant_id, sid) via index
          2. Confirm session record exists and is not individually revoked
          3. Check user-level bulk revocation:
             session.created_at <= user_revoked_at -> reject
          4. Return session metadata if all checks pass
        """
        with self._lock:
            location = self._token_index.get(token)
            if location is None:
                return None

            tenant_id, sid = location
            session = self._tenant_sessions(tenant_id).get(sid)
            if session is None:
                return None

            # Per-session revocation check
            if session["revoked_at"] is not None:
                return None

            # User-level bulk revocation check:
            # analogous to: token.iat <= user_revoked_at -> reject
            user_rev_ts = self._tenant_user_revoked(tenant_id).get(session["user_id"])
            if user_rev_ts is not None and session["created_at"] <= user_rev_ts:
                return None

            return {
                "tenant_id": tenant_id,
                "user_id": session["user_id"],
                "device_id": session["device_id"],
            }

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """
        Bulk invalidate ALL sessions for a user in a tenant.

        Sets user_rev:{tenant}:{uid} = now (analogous to Redis SETEX).
        All existing sessions whose created_at <= revoked_at will be rejected
        on next validate_session call (simulates event-driven cache invalidation).
        Also marks each session record as individually revoked for clean enumeration.
        Returns count of sessions that were active at the time of invalidation.
        """
        revoked_at = time.time()
        count = 0

        with self._lock:
            # Record bulk revocation timestamp: user_rev:{tenant}:{uid}
            self._tenant_user_revoked(tenant_id)[user_id] = revoked_at

            # Also mark individual session records and count them
            sids = self._tenant_user_sessions(tenant_id).get(user_id, set())
            sessions_store = self._tenant_sessions(tenant_id)
            for sid in sids:
                sess = sessions_store.get(sid)
                if sess is not None and sess["revoked_at"] is None:
                    sess["revoked_at"] = revoked_at
                    count += 1

        return count

    def invalidate_session(self, token: str) -> bool:
        """
        Invalidate a specific session by token.

        Sets sess:{tenant}:{sid}.revoked_at = now.
        Returns True if the session existed (and was active), False otherwise.
        """
        with self._lock:
            location = self._token_index.get(token)
            if location is None:
                return False

            tenant_id, sid = location
            session = self._tenant_sessions(tenant_id).get(sid)
            if session is None:
                return False

            if session["revoked_at"] is not None:
                # Already revoked; still existed so return True
                return True

            session["revoked_at"] = time.time()
            return True
