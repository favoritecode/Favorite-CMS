import pytest

from backend.core import Kernel
from backend.engines.permissions import (
    AuthorizationContext,
    PermissionDefinition,
    PermissionDenied,
    PermissionEngine,
    PermissionError,
    RoleGrant,
)
from backend.engines.authentication import AuthenticationContext, AuthenticationEngine
from backend.engines.users import UserEngine


def _definition(**overrides: object) -> PermissionDefinition:
    values = {
        "permission_id": "tests.article.read",
        "owner": "tests",
        "action": "read",
        "resource_type": "article",
        **overrides,
    }
    return PermissionDefinition(**values)


def _authenticated(kernel: Kernel, *, role: str = "member") -> AuthenticationContext:
    users = kernel.container.resolve("engine.users", UserEngine)
    authentication = kernel.container.resolve("engine.authentication", AuthenticationEngine)
    user = users.create(
        email=f"{role}-{id(kernel)}@example.com", display_name=role, role=role
    )
    authentication.set_password(user.user_id, "correct horse battery staple")
    result = authentication.login(
        email=user.email, password="correct horse battery staple"
    )
    assert result.success
    return result.context


def test_permission_defaults_to_deny(identity_kernel: Kernel) -> None:
    permissions = identity_kernel.container.resolve("engine.permissions", PermissionEngine)
    context = AuthorizationContext("read", "article", _authenticated(identity_kernel))
    assert not permissions.evaluate("unknown", context).allowed
    permissions.register(_definition())
    assert not permissions.evaluate("tests.article.read", context).allowed
    with pytest.raises(PermissionDenied):
        permissions.require("tests.article.read", context)


def test_role_grants_are_explicit_and_owner_scoped(identity_kernel: Kernel) -> None:
    permissions = identity_kernel.container.resolve("engine.permissions", PermissionEngine)
    permissions.register(_definition())
    with pytest.raises(PermissionError, match="owner"):
        permissions.grant_role(RoleGrant("member", "tests.article.read", "other"))
    permissions.grant_role(RoleGrant("member", "tests.article.read", "tests"))
    member = _authenticated(identity_kernel)
    allowed = permissions.evaluate(
        "tests.article.read",
        AuthorizationContext("read", "article", member),
    )
    unknown = _authenticated(identity_kernel, role="unknown")
    unknown_role = permissions.evaluate(
        "tests.article.read",
        AuthorizationContext("read", "article", unknown),
    )
    assert allowed.allowed and allowed.reason == "role_grant"
    assert not unknown_role.allowed


def test_ownership_and_public_rules_are_capability_specific(identity_kernel: Kernel) -> None:
    permissions = identity_kernel.container.resolve("engine.permissions", PermissionEngine)
    permissions.register(_definition(allow_owner=True, allow_public=True))
    authentication = _authenticated(identity_kernel)
    assert authentication.user_id is not None
    owner = AuthorizationContext(
        "read", "article", authentication, owner_user_id=authentication.user_id
    )
    other = AuthorizationContext(
        "read", "article", authentication, owner_user_id="someone-else"
    )
    public = AuthorizationContext("read", "article", public=True)
    mismatch = AuthorizationContext(
        "delete", "article", authentication, owner_user_id=authentication.user_id
    )
    assert permissions.evaluate("tests.article.read", owner).allowed
    assert not permissions.evaluate("tests.article.read", other).allowed
    assert permissions.evaluate("tests.article.read", public).allowed
    assert not permissions.evaluate("tests.article.read", mismatch).allowed


def test_authentication_success_alone_never_authorizes(identity_kernel: Kernel) -> None:
    permissions = identity_kernel.container.resolve("engine.permissions", PermissionEngine)
    permissions.register(_definition())
    context = AuthorizationContext("read", "article", _authenticated(identity_kernel))
    assert not permissions.evaluate("tests.article.read", context).allowed


def test_forged_authentication_context_fails_closed(identity_kernel: Kernel) -> None:
    permissions = identity_kernel.container.resolve("engine.permissions", PermissionEngine)
    permissions.register(_definition(allow_owner=True))
    forged = AuthenticationContext(
        True, "00000000-0000-0000-0000-000000000001", "password",
        "00000000-0000-0000-0000-000000000002", "2999-01-01T00:00:00+00:00",
    )
    decision = permissions.evaluate(
        "tests.article.read",
        AuthorizationContext(
            "read", "article", forged,
            owner_user_id="00000000-0000-0000-0000-000000000001",
        ),
    )
    assert not decision.allowed
