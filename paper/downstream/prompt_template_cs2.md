# Implementation Task: Multi-Tenant SaaS Session Management

## Problem Statement

マルチテナントSaaSのセッション管理システムを設計する必要があります。

以下の要件を同時に満たす必要があります:
- 同一ユーザーの複数端末からの同時ログインをサポートする
- 管理者が特定ユーザーのセッションを即座に無効化できる
- 水平スケーリングに対応する（サーバー台数を増減できる）
- リクエスト認証のレイテンシを最小化する

## Design Analysis

The following design analysis was produced for this problem. Use it to guide your implementation.

---
{design_document}
---

## Interface Specification

You MUST implement a class that conforms to this interface:

```python
from abc import ABC, abstractmethod

class SessionManager(ABC):
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
```

## Instructions

1. Read the design analysis carefully
2. Implement a concrete Python class that inherits from SessionManager
3. Your implementation should reflect the design decisions and insights from the analysis
4. The implementation must be a single Python file
5. Include all necessary imports (including `import secrets`, `import uuid` if needed)
6. Do NOT import from external packages — use only the Python standard library
7. Do NOT import the ABC class from a file — redefine SessionManager as a plain class or just implement the methods directly
8. Your concrete class MUST have `create_session`, `validate_session`, `invalidate_user_sessions`, and `invalidate_session` methods with the exact signatures above
9. For storage, use in-memory data structures (dict, etc.) — no external databases

Output ONLY the Python code. No explanations, no markdown fences.
