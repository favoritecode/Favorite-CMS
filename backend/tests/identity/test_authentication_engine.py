from datetime import datetime, timedelta, timezone

import pytest

from backend.core import Kernel
from backend.engines.authentication import AuthenticationEngine, CredentialToken, PasswordHasher
from backend.engines.users import AccountState, UserEngine


def _account(kernel: Kernel, email: str = "member@example.com") -> tuple[UserEngine, AuthenticationEngine, str]:
    users = kernel.container.resolve("engine.users", UserEngine)
    authentication = kernel.container.resolve("engine.authentication", AuthenticationEngine)
    user = users.create(email=email, display_name="Member", role="member")
    authentication.set_password(user.user_id, "correct horse battery staple")
    return users, authentication, user.user_id


def test_password_hashing_is_salted_and_verifiable() -> None:
    hasher = PasswordHasher(iterations=100_000)
    first = hasher.hash("correct horse battery staple")
    second = hasher.hash("correct horse battery staple")
    assert first != second
    assert "correct horse battery staple" not in first
    assert hasher.verify("correct horse battery staple", first)
    assert not hasher.verify("wrong", first)


def test_valid_login_resolves_identity_without_granting_permissions(identity_kernel: Kernel) -> None:
    _, authentication, user_id = _account(identity_kernel)
    result = authentication.login(
        email="member@example.com", password="correct horse battery staple"
    )
    assert result.success and result.token is not None
    assert result.context.user_id == user_id
    assert authentication.resolve(result.token).authenticated
    assert "ey" not in repr(result)
    assert str(result.token) == "[REDACTED]"


@pytest.mark.parametrize(
    ("email", "password"),
    (("missing@example.com", "wrong"), ("member@example.com", "wrong"), ("invalid", "wrong")),
)
def test_invalid_credentials_have_the_same_safe_result(
    identity_kernel: Kernel, email: str, password: str
) -> None:
    _account(identity_kernel)
    result = identity_kernel.container.resolve(
        "engine.authentication", AuthenticationEngine
    ).login(email=email, password=password)
    assert not result.success
    assert result.failure == "invalid_authentication"
    assert not result.context.authenticated and result.token is None


def test_restricted_or_inactive_user_cannot_authenticate(identity_kernel: Kernel) -> None:
    users, authentication, user_id = _account(identity_kernel)
    for state in (AccountState.RESTRICTED, AccountState.INACTIVE):
        users.change_state(user_id, state)
        assert not authentication.login(
            email="member@example.com", password="correct horse battery staple"
        ).success


def test_logout_revokes_context_and_is_repeat_safe(identity_kernel: Kernel) -> None:
    _, authentication, _ = _account(identity_kernel)
    token = authentication.login(
        email="member@example.com", password="correct horse battery staple"
    ).token
    assert isinstance(token, CredentialToken)
    assert authentication.logout(token)
    assert not authentication.resolve(token).authenticated
    assert not authentication.logout(token)


def test_password_change_invalidates_previously_issued_context(identity_kernel: Kernel) -> None:
    _, authentication, user_id = _account(identity_kernel)
    old = authentication.login(
        email="member@example.com", password="correct horse battery staple"
    ).token
    authentication.set_password(user_id, "a different secure passphrase")
    assert not authentication.resolve(old).authenticated
    assert not authentication.login(
        email="member@example.com", password="correct horse battery staple"
    ).success
    assert authentication.login(
        email="member@example.com", password="a different secure passphrase"
    ).success


def test_tampered_and_expired_contexts_are_anonymous(identity_kernel: Kernel) -> None:
    _, authentication, _ = _account(identity_kernel)
    result = authentication.login(
        email="member@example.com", password="correct horse battery staple"
    )
    assert result.token is not None
    raw = result.token.reveal()
    tampered = raw[:-1] + ("A" if raw[-1] != "A" else "B")
    assert not authentication.resolve(tampered).authenticated
    authentication._clock = lambda: datetime.now(timezone.utc) + timedelta(hours=1)
    assert not authentication.resolve(result.token).authenticated
