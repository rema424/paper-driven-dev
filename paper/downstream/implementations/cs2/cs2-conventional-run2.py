"""
CS2-A-Run2: Version-number based session invalidation
Design: user_session_version (INCR-style) for bulk invalidation

Based on the Run 2 design analysis:
- Tokens carry a version number (ver) matching user_ver:{tid}:{uid}
- Bulk invalidation: INCR user_ver -> all existing tokens become stale immediately
- Per-session state: sess:{tid}:{sid} -> active/revoked
- Multi-tenant: all keys prefixed with tenant_id
- Low latency: version check is O(1) in-memory dict lookup
- Pub/Sub: simulated via in-memory version counter (no actual pub/sub needed
  for single-process; the counter IS the shared state)

Authentication flow (from analysis):
  1. Validate JWT signature + exp locally
  2. Compare token.ver with user_ver:{tid}:{uid} (L1 -> Redis fallback)
  3. Optionally check sess:{tid}:{sid} for individual revocation
  4. Match -> allow; mismatch -> 401
"""

import secrets
import threading


class SessionManager:
    """
    Version-number based session manager.

    Storage layout mirrors the analysis's Redis key structure:
      _user_ver[tenant][uid]         -> int (current version, starts at 1)
      _sessions[tenant][sid]         -> {user_id, device_id, version, active}
      _user_sessions[tenant][uid]    -> set of sids
      _token_to_sid[token]           -> (tenant_id, sid)
      _token_ver[token]              -> int (version snapshot at creation time)
    """

    def __init__(self):
        # user_ver:{tid}:{uid} -> current version (analogous to Redis INCR counter)
        self._user_ver: dict[str, dict[str, int]] = {}
        # sess:{tid}:{sid} -> session record
        self._sessions: dict[str, dict[str, dict]] = {}
        # user_sess:{tid}:{uid} -> set of sids
        self._user_sessions: dict[str, dict[str, set]] = {}
        # token reverse index -> (tenant_id, sid)
        self._token_to_sid: dict[str, tuple[str, str]] = {}
        # token -> version number captured at issuance
        self._token_ver: dict[str, int] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_user_ver(self, tenant_id: str, user_id: str) -> int:
        """Return current user version; initializes to 1 on first access."""
        return self._user_ver.setdefault(tenant_id, {}).setdefault(user_id, 1)

    def _incr_user_ver(self, tenant_id: str, user_id: str) -> int:
        """Atomically increment user version (simulates Redis INCR)."""
        tenant_vers = self._user_ver.setdefault(tenant_id, {})
        new_ver = tenant_vers.get(user_id, 1) + 1
        tenant_vers[user_id] = new_ver
        return new_ver

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """
        Issue a new session token for (tenant, user, device).
        Captures the current user_ver at issuance time (analogous to JWT 'ver' claim).
        Multiple concurrent sessions per user are naturally supported via distinct sids.
        """
        sid = secrets.token_hex(16)
        token = secrets.token_urlsafe(32)

        with self._lock:
            current_ver = self._get_user_ver(tenant_id, user_id)

            # sess:{tid}:{sid}
            self._sessions.setdefault(tenant_id, {})[sid] = {
                "user_id": user_id,
                "device_id": device_id,
                "version": current_ver,
                "active": True,
            }
            # user_sess:{tid}:{uid}
            self._user_sessions.setdefault(tenant_id, {}).setdefault(user_id, set()).add(sid)
            # reverse index
            self._token_to_sid[token] = (tenant_id, sid)
            self._token_ver[token] = current_ver

        return token

    def validate_session(self, token: str) -> dict | None:
        """
        Validate a session token using version comparison.

        Steps (from analysis):
          1. Resolve token to (tenant, sid)
          2. Compare token.ver with current user_ver:{tid}:{uid}
             - Mismatch -> 401 (bulk invalidation in effect)
          3. Check sess:{tid}:{sid}.active for individual revocation
          4. All pass -> return session metadata
        """
        with self._lock:
            location = self._token_to_sid.get(token)
            if location is None:
                return None

            tenant_id, sid = location
            session = self._sessions.get(tenant_id, {}).get(sid)
            if session is None:
                return None

            # Step 2: version check (simulates L1 cache -> Redis lookup)
            token_ver = self._token_ver.get(token)
            current_ver = self._get_user_ver(tenant_id, session["user_id"])
            if token_ver != current_ver:
                # Version mismatch: user has been bulk-invalidated
                return None

            # Step 3: individual session revocation check
            if not session["active"]:
                return None

            return {
                "tenant_id": tenant_id,
                "user_id": session["user_id"],
                "device_id": session["device_id"],
            }

    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """
        Bulk-invalidate ALL sessions for a user by incrementing user_ver.

        Simulates: INCR user_ver:{tid}:{uid}
        All tokens whose embedded version no longer matches the new version
        will be rejected on next validate_session (immediate effect).
        Also marks individual session records inactive for accurate counting.
        Returns count of sessions that were active before invalidation.
        """
        with self._lock:
            # INCR user_ver: all outstanding tokens with old ver become stale
            self._incr_user_ver(tenant_id, user_id)

            sids = self._user_sessions.get(tenant_id, {}).get(user_id, set())
            tenant_sessions = self._sessions.get(tenant_id, {})
            count = 0
            for sid in sids:
                sess = tenant_sessions.get(sid)
                if sess is not None and sess["active"]:
                    sess["active"] = False
                    count += 1

        return count

    def invalidate_session(self, token: str) -> bool:
        """
        Invalidate a specific session by marking sess:{tid}:{sid}.active = False.
        Returns True if the session was found (regardless of prior revocation state).
        """
        with self._lock:
            location = self._token_to_sid.get(token)
            if location is None:
                return False

            tenant_id, sid = location
            session = self._sessions.get(tenant_id, {}).get(sid)
            if session is None:
                return False

            was_active = session["active"]
            session["active"] = False
            return True
