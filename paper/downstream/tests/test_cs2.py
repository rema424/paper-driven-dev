"""Hidden test suite for CS2: Multi-Tenant SaaS Session Management.

Tests are derived SOLELY from the problem statement requirements:
  - 同一ユーザーの複数端末からの同時ログインをサポートする
  - 管理者が特定ユーザーのセッションを即座に無効化できる
  - 水平スケーリングに対応する（→ functional correctness only）
  - リクエスト認証のレイテンシを最小化する（→ functional correctness only）

10 test cases covering functional correctness.
"""

import pytest


def _get_session_manager(impl_module):
    """Find and instantiate the SessionManager from the implementation."""
    for name in dir(impl_module):
        obj = getattr(impl_module, name)
        if (
            isinstance(obj, type)
            and hasattr(obj, "create_session")
            and hasattr(obj, "validate_session")
            and hasattr(obj, "invalidate_user_sessions")
            and hasattr(obj, "invalidate_session")
        ):
            try:
                return obj()
            except TypeError:
                continue  # abstract class, skip
    pytest.fail("No SessionManager implementation found")


class TestCS2BasicSession:
    """Core session lifecycle."""

    def test_create_and_validate(self, impl_module):
        """Creating a session should return a token that validates successfully."""
        sm = _get_session_manager(impl_module)
        token = sm.create_session("tenant_1", "user_1", "device_1")
        info = sm.validate_session(token)
        assert info is not None
        assert info["tenant_id"] == "tenant_1"
        assert info["user_id"] == "user_1"
        assert info["device_id"] == "device_1"

    def test_invalid_token(self, impl_module):
        """A random/invalid token should return None."""
        sm = _get_session_manager(impl_module)
        info = sm.validate_session("nonexistent_token_xyz")
        assert info is None

    def test_unique_tokens(self, impl_module):
        """Different sessions should produce different tokens."""
        sm = _get_session_manager(impl_module)
        t1 = sm.create_session("tenant_1", "user_1", "device_1")
        t2 = sm.create_session("tenant_1", "user_1", "device_2")
        assert t1 != t2


class TestCS2MultiDevice:
    """Requirement: 同一ユーザーの複数端末からの同時ログイン"""

    def test_concurrent_sessions(self, impl_module):
        """Same user on multiple devices → all sessions valid simultaneously."""
        sm = _get_session_manager(impl_module)
        t1 = sm.create_session("tenant_1", "user_1", "phone")
        t2 = sm.create_session("tenant_1", "user_1", "laptop")
        t3 = sm.create_session("tenant_1", "user_1", "tablet")
        assert sm.validate_session(t1) is not None
        assert sm.validate_session(t2) is not None
        assert sm.validate_session(t3) is not None


class TestCS2AdminInvalidation:
    """Requirement: 管理者が特定ユーザーのセッションを即座に無効化"""

    def test_invalidate_all_user_sessions(self, impl_module):
        """Admin invalidation should revoke ALL sessions for the user."""
        sm = _get_session_manager(impl_module)
        t1 = sm.create_session("tenant_1", "user_1", "phone")
        t2 = sm.create_session("tenant_1", "user_1", "laptop")
        count = sm.invalidate_user_sessions("tenant_1", "user_1")
        assert count == 2
        assert sm.validate_session(t1) is None
        assert sm.validate_session(t2) is None

    def test_invalidation_does_not_affect_others(self, impl_module):
        """Invalidating user_1's sessions should not affect user_2."""
        sm = _get_session_manager(impl_module)
        t1 = sm.create_session("tenant_1", "user_1", "phone")
        t2 = sm.create_session("tenant_1", "user_2", "phone")
        sm.invalidate_user_sessions("tenant_1", "user_1")
        assert sm.validate_session(t1) is None
        assert sm.validate_session(t2) is not None

    def test_invalidation_is_immediate(self, impl_module):
        """After invalidation, validation should immediately fail."""
        sm = _get_session_manager(impl_module)
        token = sm.create_session("tenant_1", "user_1", "phone")
        assert sm.validate_session(token) is not None  # valid before
        sm.invalidate_user_sessions("tenant_1", "user_1")
        assert sm.validate_session(token) is None  # invalid after


class TestCS2SingleSessionOps:
    """Single session invalidation and edge cases."""

    def test_invalidate_single_session(self, impl_module):
        """Invalidating one session should not affect other sessions of same user."""
        sm = _get_session_manager(impl_module)
        t1 = sm.create_session("tenant_1", "user_1", "phone")
        t2 = sm.create_session("tenant_1", "user_1", "laptop")
        result = sm.invalidate_session(t1)
        assert result is True
        assert sm.validate_session(t1) is None
        assert sm.validate_session(t2) is not None

    def test_invalidate_nonexistent_session(self, impl_module):
        """Invalidating a non-existent token returns False."""
        sm = _get_session_manager(impl_module)
        result = sm.invalidate_session("nonexistent_token")
        assert result is False

    def test_tenant_isolation(self, impl_module):
        """Sessions should be isolated between tenants.
        Invalidating user_1 in tenant_1 should not affect user_1 in tenant_2."""
        sm = _get_session_manager(impl_module)
        t1 = sm.create_session("tenant_1", "user_1", "phone")
        t2 = sm.create_session("tenant_2", "user_1", "phone")
        sm.invalidate_user_sessions("tenant_1", "user_1")
        assert sm.validate_session(t1) is None
        assert sm.validate_session(t2) is not None


class TestCS2EdgeCases:
    """Edge cases requiring deeper design understanding."""

    def test_session_recreation_after_bulk_invalidation(self, impl_module):
        """After admin invalidation, new sessions should work.
        Old tokens should remain invalid."""
        sm = _get_session_manager(impl_module)
        old = sm.create_session("t1", "u1", "phone")
        sm.invalidate_user_sessions("t1", "u1")
        new = sm.create_session("t1", "u1", "phone")
        assert sm.validate_session(old) is None  # old still invalid
        assert sm.validate_session(new) is not None  # new works

    def test_idempotent_bulk_invalidation(self, impl_module):
        """Bulk invalidation called twice → second returns 0."""
        sm = _get_session_manager(impl_module)
        sm.create_session("t1", "u1", "phone")
        sm.create_session("t1", "u1", "laptop")
        count1 = sm.invalidate_user_sessions("t1", "u1")
        count2 = sm.invalidate_user_sessions("t1", "u1")
        assert count1 == 2
        assert count2 == 0

    def test_mixed_invalidation_counts(self, impl_module):
        """Individual invalidation reduces subsequent bulk count."""
        sm = _get_session_manager(impl_module)
        t1 = sm.create_session("t1", "u1", "phone")
        sm.create_session("t1", "u1", "laptop")
        sm.create_session("t1", "u1", "tablet")
        sm.invalidate_session(t1)  # invalidate 1 of 3
        count = sm.invalidate_user_sessions("t1", "u1")  # should get remaining 2
        assert count == 2

    def test_token_is_nonempty_string(self, impl_module):
        """Session token must be a non-empty string."""
        sm = _get_session_manager(impl_module)
        token = sm.create_session("t1", "u1", "d1")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_multi_tenant_mixed_operations(self, impl_module):
        """Same user_id in 3 tenants. Operations in 1 tenant don't leak."""
        sm = _get_session_manager(impl_module)
        t1a = sm.create_session("tenant_1", "shared_user", "phone")
        t2a = sm.create_session("tenant_2", "shared_user", "phone")
        t3a = sm.create_session("tenant_3", "shared_user", "phone")
        # Invalidate in tenant_1 only
        count = sm.invalidate_user_sessions("tenant_1", "shared_user")
        assert count == 1
        assert sm.validate_session(t1a) is None
        assert sm.validate_session(t2a) is not None
        assert sm.validate_session(t3a) is not None
