#!/usr/bin/env python3
"""
Dev environment validation script.

Checks that your local environment has everything needed to develop youtube-sync.
"""

import shutil
import subprocess
import sys
from pathlib import Path

from rich.console import Console

console = Console()


def check_python_version() -> bool:
    """Verify Python 3.14+ is available."""
    version = sys.version_info
    required = (3, 14)

    if version >= required:
        console.print(f"✓ Python {version.major}.{version.minor}.{version.micro}", style="green")
        return True
    else:
        console.print(
            f"✗ Python {version.major}.{version.minor} found, need 3.14+",
            style="red",
        )
        console.print("  Install Python 3.14: https://www.python.org/downloads/", style="dim")
        return False


def check_uv_installed() -> bool:
    """Verify uv is installed and get version."""
    if not shutil.which("uv"):
        console.print("✗ uv not found", style="red")
        console.print("  Install: curl -LsSf https://astral.sh/uv/install.sh | sh", style="dim")
        return False

    try:
        result = subprocess.run(
            ["uv", "--version"], capture_output=True, text=True, check=True, timeout=5
        )
        version = result.stdout.strip()
        console.print(f"✓ {version}", style="green")
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        console.print("✗ uv found but couldn't get version", style="red")
        return False


def check_1password_cli() -> bool:
    """Verify 1Password CLI is installed."""
    if not shutil.which("op"):
        console.print("✗ 1Password CLI (op) not found", style="red")
        console.print(
            "  Install: https://developer.1password.com/docs/cli/get-started/", style="dim"
        )
        return False

    try:
        result = subprocess.run(
            ["op", "--version"], capture_output=True, text=True, check=True, timeout=5
        )
        version = result.stdout.strip()
        console.print(f"✓ 1Password CLI {version}", style="green")
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        console.print("✗ op found but couldn't get version", style="red")
        return False


def check_1password_authenticated() -> bool:
    """Verify 1Password CLI is authenticated."""
    try:
        # Try to get account info - will fail if not authenticated
        subprocess.run(
            ["op", "account", "list"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        console.print("✓ 1Password authenticated", style="green")
        return True
    except subprocess.CalledProcessError as e:
        if "not currently signed in" in e.stderr.lower() or "no accounts" in e.stderr.lower():
            console.print("✗ 1Password not signed in", style="red")
            console.print("  Run: op signin", style="dim")
        else:
            console.print(f"✗ 1Password auth check failed: {e.stderr.strip()}", style="red")
        return False
    except subprocess.TimeoutExpired:
        console.print("✗ 1Password auth check timed out", style="red")
        return False


def check_dependencies_installed() -> bool:
    """Verify project dependencies are installed."""
    try:
        # Check if .venv exists
        venv_path = Path(".venv")
        if not venv_path.exists():
            console.print("✗ Virtual environment not found", style="red")
            console.print("  Run: uv sync", style="dim")
            return False

        # Try to import a project dependency
        subprocess.run(
            ["uv", "run", "python", "-c", "import pydantic; import httpx"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        console.print("✓ Dependencies installed", style="green")
        return True
    except subprocess.CalledProcessError:
        console.print("✗ Dependencies missing or incomplete", style="red")
        console.print("  Run: uv sync", style="dim")
        return False
    except subprocess.TimeoutExpired:
        console.print("✗ Dependency check timed out", style="red")
        return False


def check_can_run_tests() -> bool:
    """Verify tests can run."""
    try:
        result = subprocess.run(
            ["uv", "run", "pytest", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        # Count collected tests
        lines = result.stdout.strip().split("\n")
        for line in lines:
            if "test" in line.lower():
                console.print(f"✓ Tests can run ({line.strip()})", style="green")
                return True
        console.print("✓ Tests can run", style="green")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"✗ Test collection failed: {e.stderr.strip()}", style="red")
        return False
    except subprocess.TimeoutExpired:
        console.print("✗ Test collection timed out", style="red")
        return False


def check_git_repo() -> bool:
    """Verify we're in a git repository."""
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        console.print("✓ Git repository", style="green")
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        console.print("✗ Not in a git repository", style="red")
        return False


def main():
    """Run all environment checks."""
    console.print("\n[bold]YouTube Sync - Environment Check[/bold]\n")

    checks = [
        ("Python version", check_python_version),
        ("uv package manager", check_uv_installed),
        ("Git repository", check_git_repo),
        ("1Password CLI", check_1password_cli),
        ("1Password authentication", check_1password_authenticated),
        ("Project dependencies", check_dependencies_installed),
        ("Test framework", check_can_run_tests),
    ]

    results = []
    for name, check_func in checks:
        console.print(f"\nChecking {name}...")
        try:
            results.append(check_func())
        except Exception as e:
            console.print(f"✗ Unexpected error: {e}", style="red")
            results.append(False)

    # Summary
    console.print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)

    if passed == total:
        console.print(f"\n✅ All checks passed ({passed}/{total})", style="bold green")
        console.print("\nYou're ready to develop! Try:", style="green")
        console.print("  just check     # Run all quality checks", style="dim")
        console.print("  just sync-subs # Test the sync script (dry-run)", style="dim")
        return 0
    else:
        failed = total - passed
        console.print(
            f"\n⚠️  {failed} check(s) failed ({passed}/{total} passed)",
            style="bold yellow",
        )
        console.print("\nFix the issues above, then run 'just doctor' again.", style="yellow")
        return 1


if __name__ == "__main__":
    sys.exit(main())
