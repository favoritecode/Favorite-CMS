"""Production operator CLI over existing Favorite CMS Engine contracts."""
from __future__ import annotations

import argparse
from getpass import getpass
from pathlib import Path
import sys

from backend.bootstrap import build_kernel
from backend.core import Kernel
from backend.database.migrations import DatabaseMigrationEngine
from backend.engines.permissions import PermissionEngine, RoleGrant
from backend.engines.themes import ThemeEngine, ThemePackage
from backend.operations import InstallationEngine, InstallationRequest, InstallationState, RequiredAuthorization

STARTER_THEME_ID = "favorite.theme.starter"


class _ThemeRuntime:
    def activate(self) -> None: pass
    def deactivate(self) -> None: pass


def _authorization(value: str) -> tuple[str, str, RequiredAuthorization]:
    parts = value.split(":", 3)
    if len(parts) != 4 or any(not part.strip() for part in parts):
        raise argparse.ArgumentTypeError("authorization must be permission-id:owner:action:resource-type")
    permission_id, owner, action, resource_type = parts
    return permission_id, owner, RequiredAuthorization(permission_id, action, resource_type)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="favorite-cms", description="Favorite CMS production operator interface")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate", help="Apply explicitly registered migrations")
    commands.add_parser("status", help="Show safe installation and migration status")
    install = commands.add_parser("install", help="Run the explicit first-install workflow")
    install.add_argument("--email", required=True); install.add_argument("--display-name", required=True)
    install.add_argument("--role", required=True, help="Caller-selected initial role identifier")
    install.add_argument("--authorization", action="append", required=True, type=_authorization,
                         help="Explicit permission-id:owner:action:resource-type; repeat as required")
    install.add_argument("--password-stdin", action="store_true", help="Read the password from one stdin line")
    install.add_argument("--theme-root", type=Path, default=Path("themes") / STARTER_THEME_ID)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    kernel = build_kernel()
    try:
        kernel.bootstrap()
        if arguments.command == "migrate":
            migrations = kernel.container.resolve("engine.migrations", DatabaseMigrationEngine)
            migrations.initialize_history(); applied = migrations.upgrade()
            print(f"Migrations applied: {len(applied)}")
            return 0
        if arguments.command == "status":
            installer = kernel.container.resolve("engine.installation", InstallationEngine)
            migrations = kernel.container.resolve("engine.migrations", DatabaseMigrationEngine)
            try: migration_state = str(len(migrations.pending()))
            except Exception: migration_state = "unavailable (migration history is not initialized)"
            print(f"Installation: {installer.state().value}"); print(f"Pending migrations: {migration_state}")
            return 0
        return _install(kernel, arguments)
    except Exception as exc:
        print(f"Favorite CMS command failed safely: {type(exc).__name__}", file=sys.stderr)
        return 1
    finally:
        kernel.shutdown()


def _install(kernel: Kernel, arguments: argparse.Namespace) -> int:
    installer = kernel.container.resolve("engine.installation", InstallationEngine)
    if installer.state() is InstallationState.INSTALLED:
        print(f"Installation: {InstallationState.INSTALLED.value}")
        return 0
    theme_root = arguments.theme_root.resolve()
    themes = kernel.container.resolve("engine.themes", ThemeEngine)
    if themes.active_theme != STARTER_THEME_ID:
        try: themes.package(STARTER_THEME_ID)
        except Exception: themes.bind(STARTER_THEME_ID, ThemePackage(theme_root, templates=("templates/page.html",), layouts=("layouts/base.html",), assets=("assets/starter.css",)), _ThemeRuntime())
        if not themes.activate(STARTER_THEME_ID): raise RuntimeError("Starter Theme activation failed")
    permissions = kernel.container.resolve("engine.permissions", PermissionEngine)
    authorizations: list[RequiredAuthorization] = []
    for permission_id, owner, required in arguments.authorization:
        permissions.grant_role(RoleGrant(arguments.role, permission_id, owner)); authorizations.append(required)
    password = sys.stdin.readline().rstrip("\r\n") if arguments.password_stdin else getpass("Initial password: ")
    state = installer.install(InstallationRequest(
        arguments.email, arguments.display_name, password, arguments.role, tuple(authorizations)))
    print(f"Installation: {state.value}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
