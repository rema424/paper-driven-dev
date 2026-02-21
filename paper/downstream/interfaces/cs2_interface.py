"""Interface for CS2: Multi-Tenant SaaS Session Management.

The implementation must provide a SessionManager class that handles
session creation, validation, and invalidation for a multi-tenant SaaS
application supporting concurrent multi-device login.
"""

from abc import ABC, abstractmethod


class SessionManager(ABC):
    """Abstract base class for multi-tenant session management."""

    @abstractmethod
    def create_session(self, tenant_id: str, user_id: str, device_id: str) -> str:
        """Create a new session for a user on a specific device.

        Args:
            tenant_id: The tenant identifier.
            user_id: The user identifier within the tenant.
            device_id: The device identifier.

        Returns:
            A unique session token string.
        """
        ...

    @abstractmethod
    def validate_session(self, token: str) -> dict | None:
        """Validate a session token.

        Args:
            token: The session token to validate.

        Returns:
            A dict with keys 'tenant_id', 'user_id', 'device_id' if valid,
            or None if the token is invalid or expired.
        """
        ...

    @abstractmethod
    def invalidate_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """Invalidate all sessions for a specific user in a tenant.

        This is the admin-level invalidation operation.

        Args:
            tenant_id: The tenant identifier.
            user_id: The user identifier.

        Returns:
            The number of sessions that were invalidated.
        """
        ...

    @abstractmethod
    def invalidate_session(self, token: str) -> bool:
        """Invalidate a specific session.

        Args:
            token: The session token to invalidate.

        Returns:
            True if the session existed and was invalidated,
            False if the token was not found.
        """
        ...
